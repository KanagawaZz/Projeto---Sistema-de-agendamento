# Instruções para IA e continuidade do projeto

## Visão geral
Este repositório é um sistema de agendamento em Django com integração de WhatsApp/Evolution API para lembretes e automação.

Arquitetura principal:
- `agenda/`: app principal do sistema
- `config/`: configuração Django
- `templates/agenda/`: templates HTML
- `static/agenda/`: arquivos estáticos
- `agenda/migrations/`: migrações do banco

## Stack
- Python / Django
- SQLite por padrão no projeto
- Docker / Docker Compose para execução em ambiente de empresa
- Integração com WhatsApp/Evolution API

## Como rodar o projeto
Se estiver em ambiente com Docker:

```bash
docker compose up --build
```

Depois, rode as migrações:

```bash
docker compose exec web python manage.py migrate
```

Crie superusuário:

```bash
docker compose exec web python manage.py createsuperuser
```

Para visualizar logs:

```bash
docker compose logs -f
```

Se o serviço não for chamado de `web`, ajustar para o nome correto no `docker-compose.yml`.

## Fluxo de trabalho recomendado
- Antes de alterar qualquer feature, identificar o modelo, a view, o form ou template afetados.
- Preferir mudanças pequenas e focadas.
- Manter compatibilidade com o Django e com os templates existentes.
- Não remover migrações sem necessidade clara.
- Não expor tokens, chaves ou segredos no código.
- Usar variáveis de ambiente quando possível.

## Estrutura importante
- `agenda/models.py`: modelos principais de negócio, agendamentos, clientes e integrações
- `agenda/views.py`: lógica de negócio e renderização das telas
- `agenda/forms.py`: formulários do sistema
- `agenda/urls.py`: rotas da aplicação
- `agenda/services.py`: serviços auxiliares e regras
- `agenda/integrations/whatsapp.py`: integração com WhatsApp/Evolution
- `agenda/management/commands/send_whatsapp_reminders.py`: envio de lembretes
- `config/settings.py`: configuração do Django, banco e integrações

## Regras de desenvolvimento
- Sempre validar com testes relevantes antes de concluir mudanças.
- Se houver comportamento novo, preferir adicionar teste de regressão em `agenda/tests.py`.
- Evitar hardcode de URLs, tokens, números de WhatsApp e chaves secretas.
- Quando mexer em templates, manter a UI consistente com o estilo atual.
- Quando mexer em migrações, garantir que elas sejam compatíveis com o ambiente atual.

## Integração WhatsApp / Evolution API
- A integração pode depender de variáveis de ambiente e URL da API.
- Confirme os nomes das variáveis antes de alterar a configuração.
- Testar primeiro com ambiente local ou docker antes de mudar fluxos críticos.
- Em caso de falhas, verificar logs do container e da API de WhatsApp.

## Prompt útil para continuar o projeto
Use este prompt para a IA continuar o desenvolvimento:

> Quero continuar o desenvolvimento deste projeto Django em um ambiente com Docker. Analise o projeto, entenda a estrutura atual, identifique o arquivo correto para a mudança, execute os comandos necessários, valide com migrações/testes e me explique o que foi alterado e como rodar localmente.

## Objetivo da IA
A IA deve agir como assistente de desenvolvimento do projeto, mantendo o contexto do código, evitando mudanças destrutivas, e priorizando execução segura e verificável.

## Importante
O projeto é sensível a integrações externas e a dados de negócio. Sempre favorizar soluções estáveis, rastreáveis e bem documentadas.
