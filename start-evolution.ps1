$ErrorActionPreference = 'Stop'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker nao foi encontrado. Abra ou instale o Docker Desktop antes de continuar.'
}

if (-not (Test-Path '.env.evolution')) {
    throw 'Arquivo .env.evolution nao encontrado. Crie-o a partir de .env.evolution.example.'
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'O Docker Desktop nao esta em execucao. Abra-o e execute este script novamente.'
}

docker compose --env-file .env.evolution config --quiet
if ($LASTEXITCODE -ne 0) {
    throw 'A configuracao do Docker Compose e invalida. Revise .env.evolution.'
}

docker compose --env-file .env.evolution up -d
if ($LASTEXITCODE -ne 0) {
    throw 'Nao foi possivel iniciar a Evolution API.'
}

docker compose --env-file .env.evolution ps
Write-Host ''
Write-Host 'Evolution API iniciada. Verifique http://localhost:8080 e depois inicie o Django.'
