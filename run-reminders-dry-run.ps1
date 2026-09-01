$ErrorActionPreference = 'Stop'

if (-not (Test-Path '.\.venv\Scripts\python.exe')) {
    throw 'Ambiente virtual nao encontrado. Execute este script na pasta raiz do projeto.'
}

if (-not (Test-Path '.env.evolution')) {
    throw 'Arquivo .env.evolution nao encontrado.'
}

$apiKey = ((Get-Content .env.evolution | Where-Object { $_ -match '^AUTHENTICATION_API_KEY=' } | Select-Object -First 1) -replace '^AUTHENTICATION_API_KEY=', '')
if ([string]::IsNullOrWhiteSpace($apiKey) -or $apiKey -eq 'troque-por-um-segredo-longo') {
    throw 'AUTHENTICATION_API_KEY nao esta configurada com um valor valido.'
}

$env:EVOLUTION_API_URL = 'http://localhost:8080'
$env:EVOLUTION_API_KEY = $apiKey
.\.venv\Scripts\python.exe manage.py send_whatsapp_reminders --dry-run
