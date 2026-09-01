# Copilot Instructions

Este repositório é um sistema de agendamento em Django com integração de WhatsApp/Evolution API.

## Contexto do projeto
- App principal: `agenda/`
- Configuração: `config/`
- Templates: `templates/agenda/`
- Estáticos: `static/agenda/`
- Banco: SQLite por padrão
- Execução recomendada: Docker Compose

## Comandos principais
```bash
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose logs -f
```

## Regras
- Não remover migrações sem necessidade clara.
- Não hardcodear secrets, tokens ou URLs de produção.
- Priorizar mudanças pequenas e organizadas.
- Sempre verificar o impacto em models, views, forms e templates relacionados.
- Preferir adicionar testes em `agenda/tests.py` quando houver nova regra de negócio.
- Quando ajustar a integração WhatsApp/Evolution, verificar logs e variáveis de ambiente antes de assumir a causa.

## Estrutura relevante
- `agenda/models.py`
- `agenda/views.py`
- `agenda/forms.py`
- `agenda/urls.py`
- `agenda/services.py`
- `agenda/integrations/whatsapp.py`
- `agenda/management/commands/send_whatsapp_reminders.py`
- `config/settings.py`

## Objetivo
Ajudar a continuar o desenvolvimento do projeto de forma segura, documental e compatível com a arquitetura atual.
