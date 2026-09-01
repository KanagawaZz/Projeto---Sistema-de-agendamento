# Evolution API local

Esta estrutura prepara a Evolution API v2.3.7 com Baileys e PostgreSQL no Docker Desktop para Windows.

## Antes de iniciar

1. Instale o Docker Desktop e confirme que os containers Linux estao habilitados.
2. Copie `.env.evolution.example` para `.env.evolution`.
3. Troque `AUTHENTICATION_API_KEY` e `POSTGRES_PASSWORD` por valores longos e locais.
4. Confirme na documentacao/imagem 2.3.7 os nomes das variaveis `DATABASE_*` e `AUTHENTICATION_API_KEY`. O Compose foi deixado explicito para facilitar essa conferencia.
5. Mantenha `EVOLUTION_BIND_ADDRESS=127.0.0.1` durante o teste local. Isso evita expor a API na rede.

## Validar sem iniciar

No PowerShell, na raiz do projeto:

```text
docker compose config
```

Se a configuracao for valida, o comando deve exibir a configuracao expandida sem erro. Nao publique essa saida, pois ela pode conter secrets.

## Iniciar e verificar

Somente depois de revisar o arquivo `.env.evolution`:

```text
docker compose --env-file .env.evolution up -d
docker compose --env-file .env.evolution ps
```

Teste localmente no navegador ou PowerShell:

```text
curl http://localhost:8080
```

Para parar sem apagar dados:

```text
docker compose down
```

Nao use `docker compose down -v`: isso remove os volumes persistentes e a sessao do WhatsApp.

## Voltar a trabalhar depois de desligar o computador

1. Abra o Docker Desktop e aguarde ele informar que esta em execucao.
2. No PowerShell, abra a pasta do projeto.
3. Execute o script:

```powershell
.\start-evolution.ps1
```

O script verifica o Docker, valida `.env.evolution`, inicia os containers e mostra o status. Ele nao exibe a API key e nao inicia o Django.

Como o Compose usa `restart: unless-stopped`, os containers tambem podem voltar automaticamente quando o Docker Desktop iniciar. Para habilitar isso, abra Docker Desktop > Settings > General e marque a opcao para iniciar o Docker Desktop com o Windows.

Para parar ao terminar o trabalho, use:

```powershell
docker compose --env-file .env.evolution down
```

Esse comando para os containers sem remover os volumes nem a sessao conectada.

## Persistencia

- `evolution_instances` preserva as sessoes das instancias.
- `evolution_db` preserva o PostgreSQL.
- Em um servidor real, esses volumes precisam de backup e armazenamento confiavel.

## Configurar o Django localmente

O arquivo `.env.evolution` e usado pelo Docker da Evolution. O Django nao carrega esse arquivo automaticamente. No PowerShell que sera usado para iniciar o Django, defina:

```powershell
$env:EVOLUTION_API_URL = "http://localhost:8080"
$env:EVOLUTION_API_KEY = "sua-chave-local"
```

Depois, acesse `/business/whatsapp/`, informe `agenda-facil` como nome da instancia e salve. Use o botao de validacao; a API deve retornar estado `open` quando a sessao estiver conectada.

Para producao, use variaveis permanentes ou um secret manager. Nunca coloque a chave no frontend, banco Django ou Git.

Depois de iniciar a Evolution, o Django deve ser iniciado em outro terminal com as variaveis configuradas:

```powershell
$env:EVOLUTION_API_URL = "http://localhost:8080"
$env:EVOLUTION_API_KEY = "mesmo-valor-de-AUTHENTICATION_API_KEY"
.\.venv\Scripts\python.exe manage.py runserver
```

## Verificar lembretes sem enviar mensagens

Com a Evolution em execucao e a API key real configurada em `.env.evolution`, abra outro PowerShell na raiz do projeto e execute:

```powershell
.\run-reminders-dry-run.ps1
```

O script carrega a API key somente em memoria e executa `send_whatsapp_reminders --dry-run`. Nenhuma chamada de envio e feita nesse modo. Se a chave ainda estiver com o valor de exemplo, o script interrompe a execucao.

## Rotina para amanha

```powershell
.\start-evolution.ps1
$env:EVOLUTION_API_URL = "http://localhost:8080"
$env:EVOLUTION_API_KEY = "mesmo-valor-de-AUTHENTICATION_API_KEY"
.\.venv\Scripts\python.exe manage.py runserver
```

Em outro PowerShell, use `.\run-reminders-dry-run.ps1` para diagnostico. Nao habilite ainda lembretes para clientes reais nem execute o comando sem `--dry-run`.

## Limites desta etapa

- A consulta de estado, o envio de texto e a mensagem configuravel pelo cliente REST Django ja estao implementados e testados com API simulada.
- O comando de lembretes ainda deve ser executado por scheduler; use `--dry-run` para conferir quantos seriam enviados sem chamada externa.
- A porta esta vinculada somente ao computador local.
- Para servidores separados, sera necessario HTTPS, firewall e uma URL acessivel pelo Django.
- Nao colocar API key no frontend, no banco Django ou no Git.

A proxima etapa so deve ser a validacao do Compose e da API local com a versao efetivamente usada. Depois disso sera feita a adaptacao do cliente Django, mantendo o envio assincrono e o consentimento explicito.
