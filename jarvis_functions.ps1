# Добавляем функцию для получения эмбеддинга из LLM
function Get-Embedding {
    param([string]$Text)
    
    $body = @{text = $Text} | ConvertTo-Json
    $utf8Body = [System.Text.Encoding]::UTF8.GetBytes($body)
    
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/embedding" `
            -Method Post -Body $utf8Body -ContentType "application/json; charset=utf-8" -UseBasicParsing
        
        $json = $response.Content | ConvertFrom-Json
        return $json.embedding
    } catch {
        Write-Host "⚠️ Ошибка получения эмбеддинга, использую пустой" -ForegroundColor Yellow
        return @()
    }
}

# Функция добавления узла с эмбеддингом
function Add-Node-With-Embedding {
    param([string]$Text, [string]$Intent = "memory")
    
    Write-Host "📡 Получаю эмбеддинг..." -ForegroundColor Cyan
    $embedding = Get-Embedding $Text
    
    # Сохраняем эмбеддинг во временный файл
    $embFile = [System.IO.Path]::GetTempFileName()
    $embedding | ConvertTo-Json | Out-File $embFile
    
    # Добавляем узел с эмбеддингом
    $result = & "C:\Users\Usuario\Jarvis\binvg\target\release\binvg.exe" add "$Text" "$Intent" --embedding-file $embFile 2>&1
    
    Remove-Item $embFile -Force
    
    Write-Host $result -ForegroundColor Green
}

# Функция поиска с парсингом результатов
function Search-Memory {
    param([string]$Query, [int]$TopK = 5)
    
    Write-Host "🔍 Поиск в памяти: '$Query'" -ForegroundColor Cyan
    
    $output = & "C:\Users\Usuario\Jarvis\binvg\target\release\binvg.exe" search "$Query" --top-k $TopK 2>&1
    
    $context = ""
    $results = @()
    
    $output -split "`n" | ForEach-Object {
        if ($_ -match '\[\s*(\d+)\]\s*(.+)') {
            $id = $matches[1]
            $text = $matches[2]
            $context += "• $text`n"
            $results += [PSCustomObject]@{Id = $id; Text = $text}
        }
    }
    
    if ($context -eq "") {
        Write-Host "  Ничего не найдено" -ForegroundColor Gray
    } else {
        Write-Host "  Найдено $($results.Count) узлов" -ForegroundColor Green
    }
    
    return @{
        Context = $context
        Results = $results
    }
}

# Функция вопроса с контекстом из памяти
function Ask-With-Memory {
    param([string]$Question)
    
    # 1. Ищем в памяти
    $memory = Search-Memory -Query $Question -TopK 5
    
    # 2. Формируем промпт
    if ($memory.Context -ne "") {
        $prompt = "Контекст из памяти (наиболее релевантные записи):`n$($memory.Context)`nВопрос пользователя: $Question`nОтветь на русском языке, используя контекст если это уместно."
    } else {
        $prompt = "Вопрос пользователя: $Question`nОтветь на русском языке."
    }
    
    Write-Host "🤔 Думаю..." -ForegroundColor Yellow
    
    # 3. Отправляем в LLM
    $body = @{
        prompt = $prompt
        max_tokens = 400
        temperature = 0.7
    } | ConvertTo-Json
    
    $utf8Body = [System.Text.Encoding]::UTF8.GetBytes($body)
    
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/generate" `
            -Method Post -Body $utf8Body -ContentType "application/json; charset=utf-8" -UseBasicParsing
        
        $json = $response.Content | ConvertFrom-Json
        
        Write-Host "`n💬 Ответ:" -ForegroundColor Green
        Write-Host $json.response -ForegroundColor White
        
        # 4. Возвращаем для автозаписи
        return $json.response
    } catch {
        Write-Host "❌ Ошибка: $_" -ForegroundColor Red
        return $null
    }
}

# Функция для сохранения диалога в память
function Save-Dialog-To-Memory {
    param([string]$Question, [string]$Answer)
    
    if (-not $Answer) { return }
    
    Write-Host "💾 Сохраняю диалог в память..." -ForegroundColor Gray
    
    # Получаем эмбеддинги для обоих сообщений
    $qEmbedding = Get-Embedding $Question
    $aEmbedding = Get-Embedding $Answer
    
    # Сохраняем вопрос
    $qEmbFile = [System.IO.Path]::GetTempFileName()
    $qEmbedding | ConvertTo-Json | Out-File $qEmbFile
    & "C:\Users\Usuario\Jarvis\binvg\target\release\binvg.exe" add "Вопрос: $Question" "dialog" --embedding-file $qEmbFile 2>&1 | Out-Null
    
    # Сохраняем ответ
    $aEmbFile = [System.IO.Path]::GetTempFileName()
    $aEmbedding | ConvertTo-Json | Out-File $aEmbFile
    & "C:\Users\Usuario\Jarvis\binvg\target\release\binvg.exe" add "Ответ: $Answer" "dialog" --embedding-file $aEmbFile 2>&1 | Out-Null
    
    # Связываем вопрос и ответ
    & "C:\Users\Usuario\Jarvis\binvg\target\release\binvg.exe" connect 0 1 1.0 2>&1 | Out-Null  # TODO: получить реальные ID
    
    Remove-Item $qEmbFile, $aEmbFile -Force
    
    Write-Host "✅ Диалог сохранен" -ForegroundColor Green
}

# Единая функция для работы с Jarvis
function Jarvis {
    param([string]$Command)
    
    switch -Regex ($Command) {
        '^ask (.+)$' {
            $question = $matches[1]
            $answer = Ask-With-Memory $question
            Save-Dialog-To-Memory -Question $question -Answer $answer
        }
        '^add (.+)$' {
            Add-Node-With-Embedding $matches[1]
        }
        '^search (.+)$' {
            $mem = Search-Memory $matches[1] -TopK 10
            $mem.Results | Format-Table Id, Text -AutoSize
        }
        '^stats$' {
            & "C:\Users\Usuario\Jarvis\binvg\target\release\binvg.exe" stats
        }
        '^nodes$' {
            $all = Search-Memory "" -TopK 100
            $all.Results | Format-Table Id, Text -AutoSize
        }
        '^help$' {
            Write-Host @"
Доступные команды:
  ask <вопрос>    - спросить с контекстом из памяти
  add <текст>     - добавить узел в память
  search <текст>  - поиск по памяти
  stats           - статистика памяти
  nodes           - показать все узлы
  help            - эта справка
"@ -ForegroundColor Cyan
        }
        default {
            Write-Host "Неизвестная команда. Введи 'help'" -ForegroundColor Red
        }
    }
}

