# Contexto do Projeto — Agenda Fácil

## 1. Visão geral do produto

O Agenda Fácil é um sistema web de agendamento e gestão de atendimentos para pequenos prestadores de serviços, como barbeiros, manicures, cabeleireiros, tatuadores, personal trainers, fotógrafos, professores particulares e técnicos empreendimetos que trabalham com agendamento de serviços em geral.

O objetivo do MVP é permitir que o empreendedor configure seu negócio, serviços e horários de funcionamento, preparando a base para que clientes realizem agendamentos posteriormente.

O sistema prioriza simplicidade de uso, manutenção e evolução incremental.

## 2. Stack utilizada

- Python 3.13.1
- Django 6.1
- Django Templates
- HTML
- JavaScript Vanilla
- SQLite no desenvolvimento
- Banco relacional usando o ORM do Django
- Ambiente virtual Python em `.venv`
- Git inicializado no projeto
- Dependência registrada em `requirements.txt`

Configurações atuais relevantes:

- Idioma: `pt-br`
- Timezone: `America/Cuiaba`
- Autenticação nativa do Django
- Templates globais em `templates/`
- `USE_TZ = True`

## 3. Etapas já implementadas

### 3.1 Fundação do projeto

**O que foi feito**

- Projeto Django criado.
- App `agenda` criada e registrada.
- Ambiente virtual criado.
- Django instalado.
- SQLite configurado.
- Git inicializado.
- README e `.gitignore` adicionados.
- Configuração de idioma, timezone e templates globais.

**Models e arquivos principais**

- `manage.py`
- `config/settings.py`
- `config/urls.py`
- `agenda/`
- `requirements.txt`
- `README.md`
- `.gitignore`

Não havia model próprio nesta etapa. Foram aplicadas as migrações padrão do Django para autenticação, sessões, admin e content types.

**Regras implementadas**

- Uso de SQLite no desenvolvimento.
- Uso do timezone `America/Cuiaba`.
- App `agenda` registrada no projeto.

**Testes**

- Nenhum teste próprio na fundação.
- `manage.py check` executado com sucesso.
- Migrações aplicadas com sucesso.

### 3.2 Autenticação do empreendedor

**O que foi feito**

- Cadastro de usuário.
- Login.
- Logout via `POST`.
- Dashboard protegida.
- Redirecionamento de usuários anônimos.
- Formulários protegidos com CSRF.

**Models e arquivos principais**

- `agenda/views.py`
- `agenda/urls.py`
- `config/urls.py`
- `config/settings.py`
- `templates/agenda/login.html`
- `templates/agenda/signup.html`
- `templates/agenda/dashboard.html`
- `templates/agenda/base.html`
- `agenda/tests.py`

Foi utilizada a autenticação padrão do Django, sem model de usuário customizado.

**Regras implementadas**

- Usuários não autenticados não acessam a dashboard.
- Cadastro válido cria e autentica o usuário.
- Cadastro inválido não cria usuário.
- Login válido autentica o usuário.
- Logout encerra a sessão.
- A dashboard exige autenticação.

**Testes**

4 testes diretamente relacionados à autenticação:

- Cadastro válido.
- Cadastro inválido.
- Redirecionamento de usuário anônimo.
- Login e logout.

### 3.3 Cadastro e edição do negócio

**O que foi feito**

- Model `Business`.
- Relação `User -> Business` usando `OneToOneField`.
- Cadastro do negócio.
- Edição do negócio.
- Slug automático.
- Verificação de unicidade do slug.
- Dashboard condicionada à existência do negócio.

**Models e arquivos principais**

- `agenda/models.py`
- `agenda/forms.py`
- `agenda/views.py`
- `agenda/urls.py`
- `agenda/tests.py`
- `templates/agenda/business_form.html`
- `templates/agenda/dashboard.html`
- `agenda/migrations/0001_initial.py`

**Model**

`Business` possui:

- `owner`
- `name`
- `slug`
- `description`

**Regras implementadas**

- Cada usuário pode possuir um único negócio.
- Usuário autenticado sem negócio é direcionado para `/business/`.
- Usuário com negócio acessa a dashboard.
- O slug é criado usando `slugify()`.
- Em caso de colisão, são usados sufixos incrementais, como `nome-2`.
- Durante a edição, o slug existente é preservado.
- O slug não é editável pelo formulário.

**Testes**

3 testes específicos da etapa:

- Redirecionamento de usuário sem negócio.
- Criação e unicidade do slug.
- Edição do negócio e preservação do slug.

### 3.4 Cadastro e gerenciamento de serviços

**O que foi feito**

- Model `Service`.
- Relação `Business -> Service` usando `ForeignKey`.
- Listagem de serviços.
- Cadastro.
- Edição.
- Ativação e desativação.
- Isolamento por negócio.
- Cálculo do tempo operacional.

**Models e arquivos principais**

- `agenda/models.py`
- `agenda/forms.py`
- `agenda/views.py`
- `agenda/urls.py`
- `agenda/tests.py`
- `templates/agenda/service_list.html`
- `templates/agenda/service_form.html`
- `agenda/migrations/0002_service.py`

**Model**

`Service` possui:

- `business`
- `name`
- `description`
- `price`
- `duration_minutes`
- `buffer_minutes`
- `is_active`

**Regras implementadas**

- Cada serviço pertence a um negócio.
- Um empreendedor só lista serviços do próprio negócio.
- Um empreendedor só edita serviços do próprio negócio.
- Um empreendedor só ativa ou desativa serviços do próprio negócio.
- Não existe exclusão física nesta etapa.
- Duração mínima é de 1 minuto.
- Preço não pode ser negativo.
- Tempo operacional é calculado como duração mais margem.
- O tempo operacional não é armazenado no banco.

**Testes**

4 testes específicos da etapa:

- Criação e cálculo do tempo operacional.
- Edição e recálculo do tempo operacional.
- Isolamento entre negócios.
- Ativação e desativação.

### 3.5 Configuração dos horários de funcionamento

**O que foi feito**

- Model `WorkingDay`.
- Model `WorkingHours`.
- Configuração dos sete dias da semana em uma tela única.
- Suporte a múltiplos intervalos no mesmo dia.
- Adição e remoção dinâmica de intervalos com JavaScript Vanilla.
- Salvamento da semana dentro de uma transação.
- Isolamento por negócio.

**Models e arquivos principais**

- `agenda/models.py`
- `agenda/forms.py`
- `agenda/views.py`
- `agenda/urls.py`
- `agenda/tests.py`
- `templates/agenda/working_hours.html`
- `agenda/migrations/0003_workingday_workinghours_and_more.py`

**Models**

`WorkingDay` possui:

- `business`
- `day_of_week`
- `is_closed`

`WorkingHours` possui:

- `working_day`
- `start_time`
- `end_time`

**Regras implementadas**

- Cada negócio possui no máximo um registro por dia da semana.
- `day_of_week` deve estar entre 0 e 6.
- Um dia fechado não pode possuir intervalos.
- O início deve ser anterior ao fim.
- Um dia pode possuir múltiplos intervalos.
- O empreendedor só configura horários do próprio negócio.
- Exceções por data e feriados ainda não existem.

**Testes**

5 testes específicos da etapa:

- Dia fechado sem intervalos.
- Dia fechado com intervalo rejeitado.
- Múltiplos intervalos no mesmo dia.
- Intervalo inválido rejeitado.
- Isolamento entre negócios.

### 3.6 Regras de disponibilidade estrutural

**O que foi feito**

- Campo `Business.slot_granularity_minutes`, com padrão de 15 minutos.
- Validação de sobreposição entre intervalos do mesmo dia.
- Função pura para calcular horários iniciais disponíveis.
- Consideração da duração operacional do serviço, incluindo a margem posterior.
- Filtro de horários passados usando o horário local.

**Models e arquivos principais**

- `agenda/models.py`
- `agenda/services.py`
- `agenda/tests.py`
- `agenda/migrations/0004_business_slot_granularity_minutes_alter_business_id_and_more.py`
- `config/settings.py`

**Regras implementadas**

- A granularidade padrão é de 15 minutos e pode ser alterada diretamente no `Business`.
- Serviço inativo ou de outro negócio não possui horários disponíveis.
- Dia fechado ou sem configuração retorna lista vazia.
- Os candidatos avançam conforme a granularidade dentro de cada intervalo.
- O tempo operacional deve caber integralmente em um único intervalo.
- A margem de segurança é aplicada somente depois do atendimento.
- Horários cujo início já passou não são oferecidos.
- Intervalos sobrepostos são rejeitados por `WorkingHours.full_clean()`.
- Intervalos adjacentes continuam permitidos.
- A função retorna `datetime` aware no timezone local configurado.

**Testes**

8 testes específicos da etapa, cobrindo sobreposição, adjacência, dias fechados, granularidade, múltiplos intervalos, duração, margem, horário passado, serviço inativo e isolamento.

### 3.7 Agendamento público inicial

**O que foi feito**

- Model `Appointment` com status confirmado/cancelado.
- Relações diretas com `Business` e `Service`.
- Criação pública usando serviço, data e horário disponíveis.
- Exclusão de horários ocupados por agendamentos confirmados.
- Liberação de horários após cancelamento.
- Cancelamento público protegido por token seguro.

**Models e arquivos principais**

- `agenda/models.py`
- `agenda/services.py`
- `agenda/forms.py`
- `agenda/views.py`
- `agenda/urls.py`
- `agenda/tests.py`
- `templates/agenda/public_services.html`
- `templates/agenda/booking.html`
- `templates/agenda/booking_confirmation.html`
- `templates/agenda/booking_cancel.html`
- `agenda/migrations/0005_appointment.py`

**Regras implementadas**

- Cliente informa nome e telefone.
- Todo novo agendamento nasce confirmado.
- Um appointment confirmado ocupa seu tempo operacional, incluindo margem posterior.
- Agendamentos cancelados não bloqueiam novos horários.
- Conflitos usam sobreposição estrita de intervalos; horários adjacentes são permitidos.
- O POST revalida o horário no servidor antes de criar o appointment.
- O cliente pode cancelar antes do início, usando o token seguro.
- Cancelamento após o início é rejeitado.
- Serviço inativo não aparece no fluxo público.
- A confirmação exibe o link de cancelamento; não há envio de e-mail ou mensagem.

**Testes**

7 testes específicos da etapa, cobrindo defaults/status/token, relações, timezone, criação pública, conflito, cancelamento e isolamento.

### 3.8 Agenda administrativa inicial

**O que foi feito**

- Listagem protegida dos agendamentos do próprio negócio.
- Cancelamento administrativo de agendamentos futuros.
- Isolamento por proprietário e por negócio.
- Proteção da operação de cancelamento com login e método `POST`.

**Models e arquivos principais**

- `agenda/views.py`
- `agenda/urls.py`
- `agenda/tests.py`
- `templates/agenda/appointment_list.html`
- `templates/agenda/dashboard.html`

**Regras implementadas**

- O empreendedor visualiza somente os agendamentos do próprio negócio.
- A lista inclui agendamentos confirmados e cancelados, ordenados pelo início.
- O empreendedor pode cancelar somente agendamentos confirmados ainda não iniciados.
- Agendamentos iniciados não podem ser cancelados pela operação administrativa.
- A operação não responde para outro negócio e não aceita `GET`.

**Testes**

4 testes específicos da etapa, cobrindo acesso, isolamento, cancelamento futuro, bloqueio após o início e exigência de `POST`.

### 3.9 Proteção contra reservas simultâneas

**O que foi feito**

- Centralização da confirmação em `create_confirmed_appointment()`.
- Bloqueio transacional do `Business` durante a confirmação.
- Revalidação da disponibilidade dentro da transação.
- Tratamento de disputa de escrita do SQLite como horário indisponível.

**Models e arquivos principais**

- `agenda/services.py`
- `agenda/views.py`
- `agenda/tests.py`

**Regras implementadas**

- Toda criação pública passa pelo serviço transacional.
- A disponibilidade é consultada novamente depois da abertura da transação.
- A segunda confirmação conflitante é rejeitada e não cria novo appointment.
- No PostgreSQL, `select_for_update()` serializa confirmações do mesmo negócio.
- No SQLite, bloqueios de escrita são convertidos em indisponibilidade; proteção contra concorrência real em múltiplos processos continua limitada pelo banco de desenvolvimento.

**Testes**

- Teste direto de duas confirmações conflitantes, garantindo apenas uma gravação.
- Suíte pública e administrativa preservada.

### 3.10 Revisão técnica e preparação para UX

**O que foi revisado e ajustado**

- Validação de sobreposição entre intervalos novos no mesmo formset.
- Otimização das consultas de disponibilidade com filtro por data e `select_related`.
- Correção do link público exibido no formulário do negócio.
- Configurações de segredo, hosts, HTTPS, cookies seguros e HSTS controladas por variáveis de ambiente.

**Resultado da revisão**

- Regras de negócio principais estão cobertas e funcionando.
- Autorização administrativa está isolada por proprietário e negócio.
- Formulários mutáveis usam CSRF e operações administrativas exigem `POST`.
- Não foram encontrados erros de diagnóstico nos arquivos revisados.
- `check --deploy` passa quando executado com configuração de produção completa.

**Débitos técnicos mantidos**

- Concorrência real em múltiplos processos ainda deve ser validada em PostgreSQL.
- Não há constraint de banco que represente conflito temporal ou a relação consistente entre `Business` e `Service`.
- A granularidade ainda não é editável no `BusinessForm`.
- O token de cancelamento é bearer token, sem expiração ou rotação.
- A experiência visual atual é funcional e ainda não recebeu a etapa de UX.

### 3.11 Landing page segura e personalizável

**O que foi feito**

- Model `BusinessPage` relacionado individualmente ao negócio.
- Personalização controlada de título, descrição, CTA e tema.
- Publicação e fallback automático para os dados do `Business`.
- Landing pública integrada à rota existente `/book/<slug>/`.
- Painel protegido para editar e visualizar a página pública.
- CSS responsivo versionado no projeto.

**Models e arquivos principais**

- `agenda/models.py`
- `agenda/forms.py`
- `agenda/views.py`
- `agenda/urls.py`
- `agenda/admin.py`
- `agenda/tests.py`
- `templates/agenda/public_services.html`
- `templates/agenda/business_page_form.html`
- `templates/agenda/base.html`
- `templates/agenda/dashboard.html`
- `static/agenda/site.css`
- `agenda/migrations/0006_businesspage.py`

**Regras implementadas**

- A landing usa o `Business.slug` já existente.
- Sem configuração publicada, nome e descrição do negócio são usados como fallback.
- Página despublicada também retorna ao fallback padrão.
- Apenas serviços ativos aparecem na landing.
- A personalização aceita somente dados e temas previstos pelo sistema.
- Não há upload de HTML, CSS, JavaScript, ZIP ou iframes fornecidos pelo usuário.
- A rota de agendamento existente permanece responsável pela criação dos appointments.

**Testes**

5 testes específicos da etapa, cobrindo fallback, publicação, despublicação, serviços ativos, autorização e isolamento.

### 3.12 Refinamento visual e UX

**O que foi feito**

- Sistema visual compartilhado para autenticação, painel, serviços, horários, agenda e fluxo público.
- Navegação global para o empreendedor.
- Formulários com hierarquia, foco visível, mensagens de erro e ações consistentes.
- Dashboard com cards de acesso rápido e estados vazios orientativos.
- Landing responsiva com temas oceano, floresta e pôr do sol.
- Layout mobile testado sem overflow horizontal.
- Configuração de `STATICFILES_DIRS` e `STATIC_ROOT` para servir e coletar os assets.

**Arquivos principais**

- `templates/agenda/base.html`
- `templates/agenda/*.html`
- `static/agenda/site.css`
- `config/settings.py`

**Regras preservadas**

- Nenhuma regra de negócio, URL ou fluxo de agendamento foi removida.
- A personalização visual continua limitada a dados estruturados e temas fixos.
- HTML, CSS, JavaScript e ZIP enviados pelo usuário continuam proibidos.

**Validação**

- 46 testes aprovados.
- `python manage.py check`: passou.
- `python manage.py makemigrations --check`: passou.
- Renderização verificada no navegador em desktop e mobile.

## 4. Decisões arquiteturais importantes

### DEC-001 — SQLite no desenvolvimento

**Decisão:** usar SQLite inicialmente.

**Motivo:** o projeto estava vazio e SQLite reduz configuração e dependências no ambiente Windows.

**Consequência:** a escolha do banco de produção ainda precisará ser avaliada antes do deploy.

### DEC-002 — Autenticação nativa do Django

**Decisão:** usar o sistema padrão de autenticação do Django.

**Motivo:** atende ao MVP sem necessidade de usuário customizado ou camadas adicionais.

**Consequência:** uma mudança futura no modelo de usuário exigirá decisão explícita e migração planejada.

### DEC-003 — Um negócio por usuário

**Decisão:** relação `User -> Business` usando `OneToOneField`.

**Motivo:** corresponde ao escopo atual e reduz complexidade de contexto e autorização.

**Consequência:** múltiplos negócios por usuário estão fora do escopo atual.

### DEC-004 — Slug automático

**Decisão:** gerar o slug automaticamente a partir do nome do negócio.

**Motivo:** o empreendedor não precisa lidar com um campo técnico.

**Consequência:** o slug é preservado durante a edição para evitar quebra futura de links públicos.

### DEC-005 — Tempo operacional calculado

**Decisão:** não salvar o tempo operacional no banco.

**Motivo:** evitar inconsistência quando duração ou margem forem alteradas.

**Consequência:** o valor é derivado por uma `property` de `Service`.

### DEC-006 — Horários em dois níveis

**Decisão:** separar `WorkingDay` e `WorkingHours`.

**Motivo:** permite representar dias fechados e múltiplos intervalos no mesmo dia.

**Consequência:** exceções específicas por data exigirão uma modelagem futura separada.

### DEC-007 — Horários semanais recorrentes

**Decisão:** os horários são fixos por semana.

**Motivo:** atende ao requisito atual do MVP com menor complexidade.

**Consequência:** feriados, folgas e exceções por data ainda não são suportados.

### DEC-008 — Disponibilidade por intervalo contínuo

**Decisão:** o atendimento ocupa `start_datetime + duration_minutes`, sem grade fixa de slots; conflitos futuros usam sobreposição de intervalos.

### DEC-009 — Granularidade configurável por negócio

**Decisão:** `Business.slot_granularity_minutes` define o passo dos horários oferecidos e possui padrão de 15 minutos.

### DEC-010 — Margem depois do atendimento

**Decisão:** `buffer_minutes` é somado ao final do atendimento por meio de `Service.operational_minutes`.

### DEC-011 — Sobreposição rejeitada

**Decisão:** intervalos sobrepostos do mesmo `WorkingDay` são rejeitados por validação do model.

### DEC-012 — Agendamento confirmado

**Decisão:** o model `Appointment` nasce confirmado, mantendo suporte para confirmado/cancelado.

### DEC-013 — Cancelamento sem prazo mínimo

**Decisão:** no MVP, o cliente poderá cancelar antes do horário marcado, sem prazo mínimo.

### DEC-014 — Referência de horário passado

**Decisão:** usar `timezone.now()` convertido com `timezone.localtime()`.

### DEC-015 — Limite de um intervalo

**Decisão:** o tempo operacional precisa caber integralmente em um único `WorkingHours`.

### DEC-016 — Timezone local

**Decisão:** cálculos usam o horário local do sistema, com `TIME_ZONE = America/Cuiaba`.

### DEC-017 — Confirmação transacional

**Decisão:** a confirmação deve ocorrer por uma função transacional que bloqueia o `Business`, revalida o horário e só então grava o appointment.

**Motivo:** impedir que duas confirmações conflitantes sejam aceitas quando o banco de produção oferecer bloqueio de linha.

**Consequência:** PostgreSQL suporta a serialização por `select_for_update()`; SQLite não oferece o mesmo bloqueio de linha, portanto a concorrência real em múltiplos processos deve ser validada novamente quando o banco de produção for definido.

### DEC-018 — Landing sem código executável enviado pelo usuário

**Decisão:** a primeira landing será renderizada por template confiável e aceitará apenas campos estruturados e temas fixos.

**Motivo:** preservar a segurança da aplicação e evitar XSS, acesso a cookies e execução de código arbitrário na mesma origem.

**Consequência:** upload de HTML/ZIP e JavaScript personalizado ficam fora do escopo até existir origem isolada, sandbox e validação específica.

## 5. Fora do escopo até agora

As funcionalidades abaixo foram deliberadamente deixadas para o futuro:

- Bloqueios específicos.
- Feriados.
- Exceções por data.
- Fila.
- Lista de espera.
- Pagamentos online.
- Google Calendar.
- WhatsApp API.
- SMS.
- Sistema financeiro.
- Estoque.
- CRM.
- Marketplace.
- Aplicativo mobile.
- Múltiplos profissionais.
- Inteligência artificial.
- Relatórios avançados.

**Motivo geral:** permanecem fora do escopo atual por não serem necessárias para o fluxo inicial de agendamento.

## 6. Estado da suíte de testes

A suíte possuía 46 testes nesta etapa histórica; após os incrementos de agendamento manual, agenda diária, estados de atendimento, histórico de clientes, notificações internas e contato via WhatsApp, possui atualmente **62 testes** em `agenda/tests.py`.

Último estado validado:

- `python manage.py check`: passou.
- `python manage.py test`: passou.
- `python manage.py makemigrations --check`: passou.
- Resultado: 62 testes aprovados.
- Nenhum erro de diagnóstico nos arquivos principais analisados.

Distribuição por etapa:

- Autenticação: 4 testes.
- Negócio: 3 testes.
- Serviços: 4 testes.
- Horários: 5 testes.
- Disponibilidade: 8 testes.
- Agendamento: 12 testes.
- Agenda administrativa: 4 testes.
- Landing page: 5 testes.

Observação importante:

Os testes de validação de horários também exercitam diretamente `full_clean()` para a regra de sobreposição.

## 7. Próxima etapa recomendada

A próxima etapa recomendada é aprofundar a UX visual da landing e dos fluxos de agendamento.

**Motivo:**

- O negócio já existe.
- Os serviços já possuem duração e margem de segurança.
- Os horários semanais já estão configurados.
- O model `Appointment`, conflitos, confirmação e cancelamento público já estão implementados.
- A listagem e o cancelamento básico pelo empreendedor já estão implementados.
- A proteção transacional contra duas reservas simultâneas já está implementada.
- A landing segura e personalizável já está integrada à entrada pública.

Essa próxima etapa deve continuar incremental, sem implementar pagamentos, integrações ou funcionalidades futuras.

## 8. Pontos em aberto e débitos técnicos

Pontos para evolução futura:

- Validar concorrência real em PostgreSQL.
- Evoluir a agenda administrativa com filtros por data e estados mais visuais.
- Avaliar campos adicionais de contato, logo e redes sociais somente quando necessários.

Débitos técnicos conhecidos:

- A granularidade está persistida, mas ainda não é editável no `BusinessForm`.
- Não há teste paralelo real em múltiplos processos; essa validação depende da configuração do banco de produção.
- Não há envio de e-mail, SMS ou WhatsApp para o link de cancelamento.

As decisões DEC-008 a DEC-018 foram fechadas e incorporadas nas etapas correspondentes.

## 9. Plano de evolução do produto

As funcionalidades abaixo foram avaliadas considerando o `PromptMestre`, a arquitetura atual e a necessidade de evolução incremental:

- Agenda diária com filtros, impressão e compartilhamento.
- Interface otimizada para celular.
- Histórico simples do cliente por telefone.
- Notificação ao empreendedor a cada novo agendamento.
- Confirmações e lembretes automáticos via WhatsApp.
- Painel financeiro básico.
- Múltiplos profissionais por negócio.
- Cobrança opcional de sinal ou depósito.

A ordem aproximada de esforço técnico, da mais simples à mais difícil, é: agenda diária; UX mobile; histórico do cliente; notificações; WhatsApp oficial; financeiro; múltiplos profissionais; sinal ou depósito.

A ordem recomendada de produto é:

1. Agenda diária, filtros, impressão e compartilhamento.
2. Estados de atendimento e histórico do cliente.
3. Melhorias mobile na agenda e no fluxo público.
4. Eventos e infraestrutura de notificações.
5. Confirmação e lembrete via WhatsApp oficial.
6. Múltiplos profissionais.
7. Painel financeiro básico.
8. Sinal ou depósito integrado a gateway.

### 9.1 Dependências arquiteturais

- Antes do histórico e do financeiro, criar uma entidade `Customer`, normalizar o telefone e preservar snapshots do serviço e do preço no `Appointment`.
- Antes das notificações, criar eventos de domínio, registro de entregas, controle de tentativas e idempotência.
- O WhatsApp deve usar API oficial, consentimento do cliente, templates aprovados e processamento assíncrono. Falhas externas não podem impedir a criação do agendamento.
- Antes de múltiplos profissionais, criar `Professional`, associar serviços e agendamentos a profissionais e revisar a disponibilidade semanal.
- Antes de pagamentos, definir estados financeiros, expiração, cancelamento, reembolso e reconciliação.
- A concorrência real e as integrações devem ser validadas em PostgreSQL antes do uso em produção.

### 9.2 Fase concluída: agenda diária

A agenda administrativa foi evoluída de uma lista geral para uma visão diária:

- O padrão é o dia atual no timezone `America/Cuiaba`.
- A data pode ser selecionada pelo parâmetro `date`.
- Existem controles para dia anterior, hoje, próximo dia e impressão.
- Somente agendamentos do dia selecionado e do negócio autenticado são exibidos.
- A impressão oculta controles e ações administrativas.
- A criação manual de agendamentos continua disponível pela agenda.

Validação desta fase:

- `python manage.py check`: aprovado.
- `python manage.py makemigrations --check`: aprovado.
- `python manage.py test`: aprovado após a conclusão da fase.

### 9.3 Fase concluída: estados de atendimento

O ciclo administrativo do agendamento foi ampliado:

- `Appointment.Status` agora possui `confirmed`, `cancelled`, `completed` e `no_show`.
- O empreendedor pode marcar um atendimento iniciado como `Concluído`.
- O empreendedor pode registrar `Não compareceu` para um atendimento iniciado.
- Agendamentos futuros não podem ser marcados como concluídos ou ausentes.
- Agendamentos cancelados não podem receber outro estado.
- As ações exigem autenticação, pertencimento ao negócio, método `POST` e proteção CSRF.
- A migração `0007_alter_appointment_status.py` registra a alteração do campo.

Validação desta fase:

- `python manage.py test agenda.tests.AppointmentTests`: aprovado.
- A suíte completa e as verificações globais devem ser executadas ao concluir o incremento.

### 9.4 Fase concluída: histórico simples do cliente

Foi criada a entidade `Customer`, vinculada ao `Business`, com telefone normalizado para conter somente dígitos. Novos agendamentos públicos e administrativos reutilizam o mesmo cliente quando o telefone pertence ao mesmo negócio.

- O telefone normalizado possui unicidade por negócio.
- O agendamento mantém `client_name` e `client_phone` para preservar o registro da ocasião.
- A agenda exibe a quantidade de atendimentos concluídos e o último serviço conhecido.
- Clientes de negócios diferentes não podem ser associados ao mesmo agendamento.
- Agendamentos antigos permanecem válidos com o vínculo de cliente vazio; novos agendamentos passam a criar ou reutilizar `Customer`.
- A migração `0008_customer_appointment_customer_and_more.py` registra a estrutura.

Validação desta fase:

- `python manage.py check`: aprovado.
- `python manage.py makemigrations --check`: aprovado.
- `python manage.py test`: 58 testes aprovados.

### 9.5 Fase concluída: experiência mobile

A interface foi refinada para uso frequente em telas pequenas, sem alterar regras de negócio ou integrações:

- O cabeçalho reorganiza marca e navegação em duas linhas.
- Os links principais permanecem visíveis no celular, incluindo Serviços.
- A agenda diária usa controles que ocupam melhor a largura disponível.
- As ações de atendimento possuem áreas maiores para toque.
- Botões de formulários, reservas e serviços ocupam a largura disponível quando necessário.
- Cards e itens da agenda permitem quebra de conteúdo sem sobreposição.
- A suíte existente permanece aprovada com 58 testes.

Validação desta fase:

- `python manage.py test`: 58 testes aprovados.
- Nenhum diagnóstico encontrado no CSS ou nos templates alterados.

### 9.6 Diretrizes para notificações externas

O próximo incremento recomendado é criar a infraestrutura de notificações desacopladas:

1. Definir eventos internos para agendamento criado e cancelado.
2. Criar registro de entrega, tentativas e falhas.
3. Evitar que uma falha de notificação impeça a reserva.
4. Começar com uma notificação simples no painel ou e-mail.
5. Só depois avaliar a integração oficial com WhatsApp e processamento assíncrono.

### 9.7 Fase concluída: notificações internas

Foi criada uma primeira camada de notificações internas para dar visibilidade ao empreendedor sem depender de serviços externos:

- `BusinessNotification` pertence a um negócio e pode estar ligada a um agendamento.
- Novo agendamento gera uma notificação dentro da mesma transação da reserva.
- Cancelamento público ou administrativo gera uma notificação de cancelamento.
- O dashboard exibe as cinco notificações mais recentes.
- Notificações de negócios diferentes permanecem isoladas.
- Falhas de serviços externos ainda não interferem no agendamento, pois nenhum provedor externo é chamado nesta fase.
- A migração `0009_businessnotification.py` registra a estrutura.

Validação desta fase:

- `python manage.py check`: aprovado.
- `python manage.py makemigrations --check`: aprovado.
- `python manage.py test`: 63 testes aprovados.

### 9.8 Fase concluída: contato via WhatsApp com `wa.me`

Foi adicionada uma primeira integração externa de baixo risco usando links oficiais de clique para conversar:

- O negócio pode cadastrar seu número de WhatsApp no formulário de dados do negócio.
- A confirmação pública exibe o botão `Falar pelo WhatsApp` somente quando o número está configurado.
- A URL usa o formato `https://wa.me/` e inclui uma mensagem pronta com serviço e horário.
- Telefones brasileiros com 10 ou 11 dígitos recebem o código internacional `55`.
- O texto da mensagem é codificado na URL.
- A solução não envia mensagens automaticamente e não exige API, token, webhook ou fila.
- O cliente continua livre para escolher se deseja abrir a conversa.
- O campo é opcional; a ausência do WhatsApp não impede o agendamento.
- A migração `0010_business_whatsapp_phone.py` registra o novo campo.

Esta fase não deve ser descrita como lembrete automático. Automação real exigirá WhatsApp Business oficial, consentimento, templates aprovados, controle de entrega e processamento assíncrono.

Validação desta fase:

- `python manage.py check`: aprovado.
- `python manage.py makemigrations --check`: aprovado.
- `python manage.py test`: 62 testes aprovados.

### 9.9 Próxima fase

O próximo incremento deve avaliar uma primeira entrega externa de baixo risco, preferencialmente e-mail ou link de WhatsApp, antes da API oficial:

1. Definir preferências e consentimento do negócio/cliente.
2. Configurar o backend de e-mail corretamente ou validar um link `wa.me`.
3. Registrar status, tentativas e falhas de entrega.
4. Evitar chamadas externas dentro da requisição principal.
5. Só depois introduzir fila, tarefas agendadas e WhatsApp Business oficial.

### 9.10 Fase concluída: indicadores históricos do dashboard

O dashboard agora apresenta um resumo acumulado dos atendimentos concluídos:

- Top 10 clientes mais frequentes, ordenados pela quantidade de atendimentos `Concluído`.
- Top 10 serviços mais realizados, também considerando somente `Concluído`.
- Empates são ordenados alfabeticamente para manter o resultado estável.
- Os rankings são isolados pelo negócio do usuário autenticado.
- Clientes e serviços sem atendimentos concluídos exibem estado vazio orientativo.
- Esta fase não calcula receita nem usa preço atual do serviço; o painel financeiro será tratado separadamente com valor histórico e status de pagamento.

Validação desta fase:

- `python manage.py check`: aprovado.
- `python manage.py makemigrations --check`: aprovado.
- `python manage.py test`: 63 testes aprovados.

### 9.11 Fase concluída: contato manual com clientes via `wa.me`

O link `wa.me` foi ampliado para também apoiar o empreendedor no contato manual com clientes:

- Cada agendamento exibido na agenda pode apresentar o botão `WhatsApp` quando o telefone é válido.
- A mensagem é pré-preenchida com nome do cliente, negócio, serviço e horário.
- O link usa o telefone registrado no agendamento, preservando o contexto histórico daquela reserva.
- O contato é aberto em nova aba e o envio continua dependendo da confirmação manual no WhatsApp.
- A consulta da agenda continua limitada ao negócio do empreendedor autenticado, evitando exposição de contatos entre negócios.
- Não há envio automático, API, webhook, fila ou lembrete agendado nesta fase.

Validação desta fase:

- `python manage.py test agenda.tests.AppointmentTests agenda.tests.AuthenticationTests`: aprovado.
- A suíte completa permanece com 63 testes aprovados.

### 9.12 Próxima fase

O próximo incremento deve avaliar automação real somente após definir consentimento e rastreabilidade:

1. Definir preferências de comunicação e consentimento do cliente.
2. Modelar entrega, tentativas, falhas e idempotência.
3. Avaliar WhatsApp Business oficial e templates aprovados.
4. Executar notificações fora da requisição web, com fila ou tarefa agendada.
5. Manter o link `wa.me` como alternativa manual mesmo após uma futura automação.