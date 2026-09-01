# Contexto atual do projeto — Agenda Fácil

## Como usar este documento

Este é o resumo operacional para continuar o desenvolvimento. `PromptMestre.md` contém princípios, requisitos e método de trabalho. Antes de alterar código, confirme o estado no repositório e siga:

`entender -> planejar -> implementar -> testar -> revisar -> documentar -> avançar`

Trabalhe em uma etapa pequena por vez. Explique o objetivo e o critério de aceite antes do código; depois teste e atualize este documento.

## Produto e escopo

O Agenda Fácil é um sistema web de agendamento para pequenos prestadores de serviços. O cliente agenda sem criar conta e o empreendedor administra o próprio negócio.

Fluxo público: `/book/<slug>/` -> serviço -> data/horário -> nome/telefone -> confirmação.

MVP implementado:

- autenticação do empreendedor e cadastro do negócio;
- serviços, preços, duração, margem e ativação;
- horários semanais com múltiplos intervalos;
- disponibilidade, conflitos e reservas públicas/manuais;
- cancelamento público por token e administrativo;
- agenda diária e estados confirmado, cancelado, concluído e não compareceu;
- clientes por telefone e histórico simples;
- notificações internas;
- página pública estruturada e personalizável;
- contato manual via `wa.me`;
- base de lembretes automáticos via Evolution API self-hosted.

Fora do escopo: pagamentos, financeiro, Google Calendar, SMS, marketplace, aplicativo mobile, múltiplos profissionais, fila, lista de espera, feriados/bloqueios por data, relatórios avançados e upload de HTML/ZIP/JavaScript do usuário.

## Stack e ambiente

- Python 3.13.1, Django 6.1, Django Templates, HTML, CSS e JavaScript Vanilla.
- SQLite no desenvolvimento; ORM do Django.
- Autenticação nativa; um negócio por usuário.
- `.venv`, `requirements.txt`, `db.sqlite3`.
- Idioma `pt-br`, timezone `America/Cuiaba`, `USE_TZ = True`.
- Templates globais em `templates/`, estáticos em `static/`.

Comandos:

```text
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check
.\.venv\Scripts\python.exe manage.py test
```

## Estado implementado

### Domínio

Modelos principais em `agenda/models.py`: `Business`, `Service`, `WorkingDay`, `WorkingHours`, `Appointment`, `Customer`, `BusinessPage`, `BusinessNotification`, `WhatsAppIntegration` e `AppointmentReminder`.

As operações administrativas estão em `agenda/views.py` e `agenda/urls.py`, protegidas por login, pertencimento ao negócio, POST e CSRF. Nunca expor dados de outro negócio.

### Agendamento

A regra central está em `agenda/services.py`:

- horários são aware no timezone local;
- granularidade padrão de 15 minutos por negócio;
- serviço deve estar ativo e pertencer ao negócio;
- tempo operacional = duração + margem e deve caber em um intervalo;
- intervalos sobrepostos são inválidos; adjacentes são permitidos;
- somente agendamentos confirmados bloqueiam horários;
- conflitos usam sobreposição estrita;
- confirmações passam por transação, revalidação e criação do cliente/agendamento/notificação.

SQLite limita concorrência entre processos; validar PostgreSQL antes da produção.

### Evolution API

A decisão atual é Evolution API v2.3.7 self-hosted com Baileys, Docker e PostgreSQL, em servidor separado do Django. O cliente REST usa:

- `EVOLUTION_API_URL` e `EVOLUTION_API_KEY` no ambiente do Django;
- header `apikey`;
- estado por `GET /instance/connectionState/{instanceName}`;
- conexão por `GET /instance/connect/{instanceName}`;
- envio por `POST /message/sendText/{instanceName}`;
- payload de texto simples e `provider_message_id`;
- QR Code/pairing code apenas na resposta, sem persistência.

A instância local `agenda-facil` retornou estado `open`. Uma mensagem real de teste foi enviada e recebida no número autorizado. Nenhum lembrete automático de cliente foi enviado.

O empreendedor configura apenas o nome da instância no painel. A API key nunca aparece no frontend nem é salva pelo formulário.

### Lembretes

- `Business.whatsapp_reminder_message` é configurável.
- Placeholders permitidos: `{cliente}`, `{servico}`, `{data}`, `{hora}`, `{negocio}`.
- O formulário mostra prévia local com dados fictícios usando `textContent`.
- O cliente precisa consentir explicitamente.
- O envio ocorre somente pelo comando assíncrono `send_whatsapp_reminders`.
- `--dry-run` não envia mensagens.
- Há claim, retry limitado, prevenção de duplicidade e tratamento de resultado desconhecido.
- Lembretes inelegíveis são cancelados com motivo; os fora da janela continuam pendentes.
- O painel exibe os 50 lembretes mais recentes do próprio negócio com status, tentativas, datas e erro.

## Segurança e decisões

- Não executar código enviado pelo usuário na mesma origem; não aceitar HTML, ZIP, JavaScript ou iframe personalizado.
- Integrações externas não podem bloquear a criação do agendamento.
- API keys, senhas e volumes não entram no Git.
- `Business.whatsapp_phone` é somente contato manual `wa.me`, não identidade da API.
- Cada negócio deve usar uma instância Evolution própria em produção.
- A sessão da Evolution é preservada pelos volumes Docker.
- Não habilitar lembretes para clientes reais antes da revisão operacional.

## Arquivos de infraestrutura

- `docker-compose.yml`: Evolution, PostgreSQL, volumes, healthcheck e rede.
- `.env.evolution.example`: modelo de configuração.
- `.env.evolution`: configuração local ignorada pelo Git; contém secrets e não deve ser compartilhada.
- `start-evolution.ps1`: valida Docker/configuração e inicia os containers.
- `run-reminders-dry-run.ps1`: carrega a API key em memória e executa o comando sem envio.
- `EVOLUTION_API_LOCAL.md`: instalação, retomada, configuração Django e dry-run.

## Validação e débitos

Último estado: migrações aplicadas até 0015; `check` passou; `makemigrations --check` passou; suíte completa passou com 78 testes; sintaxe dos scripts PowerShell passou.

Débitos relevantes:

- configurar scheduler real;
- rate limiting e revogação de consentimento;
- webhook, caso seja necessário para status de entrega/conexão;
- revisar secrets, HTTPS e backup antes da produção;
- validar concorrência em PostgreSQL;
- tratar resultado externo desconhecido com procedimento operacional.

## Estado do trabalho

### CONCLUÍDO

Funcionalidades do MVP, integração Evolution, conexão/estado, envio controlado, mensagem configurável, prévia local, histórico administrativo e testes.

### EM DESENVOLVIMENTO

Operação segura dos lembretes automáticos. O envio foi validado manualmente, mas ainda não está habilitado para clientes reais.

### PENDENTE

Documentar e validar a execução periódica do comando; revisar a ativação controlada.

### FUTURO

Webhooks, rate limiting, melhorias de consentimento, PostgreSQL de produção e funcionalidades fora do escopo.

## Próximo dia de trabalho

### Etapa recomendada: preparar operação dos lembretes

1. Abrir o Docker Desktop e executar `./start-evolution.ps1`.
2. Conferir se `.env.evolution` possui API key real, não o valor de exemplo.
3. Iniciar o Django com `EVOLUTION_API_URL` e `EVOLUTION_API_KEY` configuradas.
4. Executar `./run-reminders-dry-run.ps1` e conferir a saída, sem enviar mensagens.
5. Revisar scheduler, secrets, consentimento, janela, cancelamento, claim e retry.
6. Somente após confirmação explícita, planejar ativação controlada para um número autorizado.

Critério de conclusão: o comando pode ser executado em dry-run, os lembretes aparecem no histórico e nenhum segredo ou mensagem real é exposto sem autorização.

Ao final da sessão, atualize este documento mantendo apenas o estado atual, os débitos e a próxima etapa.
