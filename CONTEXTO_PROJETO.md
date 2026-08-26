# Contexto atual do projeto — Agenda Fácil

## Como usar este documento

Este arquivo é um resumo operacional para uma nova sessão de desenvolvimento. O documento de princípios, requisitos e método de trabalho é `PromptMestre.md`; ele continua sendo a referência principal. Antes de alterar código, confirme o estado no repositório e siga o ciclo:

`entender -> planejar -> implementar -> testar -> revisar -> documentar -> avançar`

Não implemente várias funcionalidades de uma vez. Para cada etapa, explique brevemente o objetivo, altere somente o necessário, teste e atualize este documento.

## Produto e escopo

O Agenda Fácil é um sistema web de agendamento e gestão de atendimentos para pequenos prestadores de serviços. O cliente agenda sem criar conta; o empreendedor administra o próprio negócio.

Fluxo público principal:

`/book/<slug>/` -> escolher serviço -> escolher data e horário -> informar nome e telefone -> confirmar.

Escopo atual do MVP:

- cadastro/login do empreendedor;
- cadastro do negócio e slug público;
- serviços ativos/inativos, preço, duração e margem;
- horários semanais com múltiplos intervalos;
- disponibilidade e prevenção de conflitos;
- agendamento público e manual;
- cancelamento público por token e cancelamento administrativo;
- agenda diária, estados `confirmado`, `cancelado`, `concluído` e `não compareceu`;
- cadastro/histórico simples de clientes por telefone;
- notificações internas no dashboard;
- página pública estruturada e personalizável;
- contato manual via `wa.me`;
- base de lembretes automáticos via WhatsApp Business Cloud API.

Fora do escopo atual: pagamentos, financeiro, Google Calendar, SMS, marketplace, aplicativo mobile, múltiplos profissionais, fila, lista de espera, feriados/bloqueios por data, relatórios avançados e upload de HTML/ZIP/JavaScript do usuário.

## Stack e ambiente

- Python 3.13.1 e Django 6.1.
- Django Templates, HTML, CSS e JavaScript Vanilla.
- SQLite no desenvolvimento; ORM relacional do Django.
- Autenticação nativa do Django, sem usuário customizado.
- Ambiente virtual: `.venv`.
- Idioma: `pt-br`; timezone: `America/Cuiaba`; `USE_TZ = True`.
- Arquivos estáticos em `static/`, templates globais em `templates/`.
- Dependências em `requirements.txt`; banco local em `db.sqlite3`.

Comandos básicos:

```text
python manage.py check
python manage.py makemigrations --check
python manage.py test
```

## Estado implementado

### Domínio e autorização

Os principais modelos estão em `agenda/models.py`:

- `Business`: um por usuário (`User.owner` com `OneToOneField`), identificado por slug único.
- `Service`: pertence a um negócio; `operational_minutes = duration_minutes + buffer_minutes`.
- `WorkingDay` e `WorkingHours`: configuração semanal, dias fechados e intervalos.
- `Appointment`: negócio, serviço, cliente, horário, snapshot de nome/telefone, status e token de cancelamento.
- `Customer`: telefone normalizado e único dentro de cada negócio.
- `BusinessPage`: campos estruturados da página pública e temas fixos.
- `BusinessNotification`: notificações internas isoladas por negócio.
- `WhatsAppIntegration` e `AppointmentReminder`: conexão, consentimento e processamento de lembretes.

Views e rotas estão em `agenda/views.py` e `agenda/urls.py`. Operações administrativas são protegidas por login, pertencimento ao negócio, `POST` e CSRF. Consultas de negócio nunca devem aceitar objetos de outro proprietário.

### Agendamento e disponibilidade

A regra central está em `agenda/services.py`:

- horários são `datetime` aware no timezone local;
- a granularidade padrão é 15 minutos e pertence ao `Business`;
- o serviço precisa estar ativo e pertencer ao negócio;
- o tempo operacional precisa caber integralmente em um único intervalo;
- a margem ocupa o período posterior ao atendimento;
- intervalos sobrepostos são inválidos; intervalos adjacentes são permitidos;
- horários passados não são oferecidos;
- somente agendamentos `CONFIRMED` bloqueiam disponibilidade;
- conflitos usam sobreposição estrita; cancelamentos liberam o horário;
- toda confirmação passa por `create_confirmed_appointment()`, que abre transação, revalida disponibilidade e cria o cliente/agendamento/notificação.

No SQLite, a concorrência entre múltiplos processos é limitada. A validação real com `select_for_update()` deve ser feita em PostgreSQL antes da produção.

### Página pública

A rota `/book/<slug>/` renderiza `BusinessPage` com fallback para nome e descrição de `Business`. A página aceita apenas dados estruturados e temas fixos. Não executar conteúdo enviado pelo empreendedor na mesma origem: não adicionar upload de HTML, CSS, JavaScript, ZIP ou iframe sem uma arquitetura isolada e revisão de segurança específica.

### WhatsApp

`Business.whatsapp_phone` serve para links manuais `wa.me`; não é a identidade de envio da API. O envio automático usa `WhatsAppIntegration`, token referenciado por variável de ambiente `WHATSAPP_TOKEN_BUSINESS_<id>` e o comando `send_whatsapp_reminders`.

Regras atuais:

- lembrete exige consentimento explícito do cliente;
- agendamento válido não depende de API externa;
- processamento ocorre fora da requisição web;
- há status, tentativas, retry limitado, claim e unicidade por agendamento/tipo;
- cancelamento invalida lembretes pendentes/em processamento;
- `--dry-run` não faz chamadas externas;
- testes da Meta são simulados.

Ainda não está pronto para uso real: faltam scheduler documentado, rate limiting, revogação de consentimento, histórico operacional no painel, webhooks de entrega/leitura, secret manager e configuração externa da Meta/template. Não enviar mensagens reais durante testes.

## Regras de continuidade

1. Corrigir a causa raiz, preservando simplicidade e APIs existentes quando possível.
2. Não criar abstrações, APIs, bibliotecas ou funcionalidades futuras sem necessidade concreta.
3. Revalidar regras temporais com testes; usar timezone do Django, nunca horários improvisados.
4. Manter isolamento entre negócios em models, forms, views, queries e templates.
5. Integrações externas devem ser desacopladas, idempotentes e incapazes de impedir a criação de um agendamento.
6. Alterações de negócio importantes exigem teste e atualização deste contexto.
7. Antes de código: objetivo, arquivos envolvidos, regra e critério de aceite. Depois: teste, revisão curta e documentação.

## Validação e pontos conhecidos

Último estado registrado: `python manage.py check`, `python manage.py makemigrations --check` e a suíte de testes passaram; a última suíte completa registrada tinha 67 testes. Confirme novamente antes de confiar nesse número, pois o código pode ter mudado.

Débitos técnicos relevantes:

- validar concorrência real em PostgreSQL;
- tornar `slot_granularity_minutes` editável no `BusinessForm`, se isso for necessário ao usuário;
- decidir estratégia de produção para secrets, banco e scheduler;
- tratar o caso de resultado externo desconhecido após a API aceitar uma mensagem;
- o token de cancelamento é bearer token sem expiração/rotação;
- não há constraints de banco para conflitos temporais.

## Decisões já fechadas

- autenticação nativa e um negócio por usuário;
- slug automático preservado após edição;
- tempo operacional derivado, não armazenado;
- horários semanais em `WorkingDay`/`WorkingHours`;
- disponibilidade por intervalos contínuos e granularidade configurável;
- margem aplicada após o atendimento;
- novo agendamento nasce confirmado;
- cancelamento permitido antes do início, sem prazo mínimo;
- página pública renderizada por template confiável, sem código executável do usuário;
- lembretes externos assíncronos, com consentimento explícito e controle de reprocessamento.

## Estado do trabalho

### CONCLUÍDO

Fundação Django, autenticação, negócio, serviços, horários, disponibilidade, agendamento público/manual, agenda diária, estados de atendimento, clientes, notificações internas, UX responsiva, página pública estruturada e base da integração oficial de lembretes WhatsApp.

### EM DESENVOLVIMENTO

Operação segura dos lembretes automáticos: a base de domínio, conexão, comando e testes existe, mas ainda faltam controles operacionais e configuração para produção.

### PENDENTE

Executar e registrar uma nova validação completa; decidir e implementar somente o próximo incremento após revisar a operação dos lembretes.

### FUTURO

Exceções de agenda, financeiro, múltiplos profissionais, pagamentos e demais itens fora do escopo listados acima.

## Próximo dia de trabalho

### Etapa recomendada: observabilidade dos lembretes WhatsApp

Antes de qualquer nova funcionalidade de produto, concluir o menor incremento operacional da integração existente.

Sequência:

1. Confirmar no código o fluxo do comando `send_whatsapp_reminders` e seus estados.
2. Adicionar uma visualização administrativa simples dos lembretes do próprio negócio, mostrando status, tentativas, última tentativa e erro sanitizado.
3. Criar testes de autorização, isolamento e renderização dos estados principais.
4. Documentar como executar o comando periodicamente no ambiente de desenvolvimento, sem token real.
5. Rodar `check`, `makemigrations --check` e `test`; revisar o diff.

Critério de conclusão: o empreendedor consegue entender no painel se um lembrete está pendente, foi enviado, falhou ou foi cancelado, sem expor token nem dados de outro negócio. Não implementar rate limiting, webhook ou envio real na mesma etapa; registrar esses itens para a etapa seguinte.

Ao terminar o dia, atualizar somente as seções `Validação e pontos conhecidos`, `Estado do trabalho` e `Próximo dia de trabalho`, mantendo este arquivo como um resumo atual e não como histórico detalhado.
