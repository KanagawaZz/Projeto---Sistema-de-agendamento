# Contexto e objetivo

Você está trabalhando em um sistema que já está em desenvolvimento. **Não comece implementando imediatamente.**

Primeiro, analise cuidadosamente o projeto existente para entender sua arquitetura, tecnologias, estrutura de pastas, modelos, views, URLs, templates, autenticação, permissões, componentes de frontend, banco de dados e fluxo atual da aplicação.

O objetivo desta etapa é fazer você **entender o produto e o contexto do sistema antes de propor ou escrever código**.

## Nova funcionalidade que quero adicionar

Quero evoluir o sistema para que cada **empreendimento/negócio** possa possuir uma página pública própria, funcionando como uma espécie de Landing Page/Website do empreendimento.

A experiência deve ser moderna, elegante, bonita, simples e responsiva, tanto para:

* Administrador/empreendedor;
* Usuário/cliente final.

### Conceito principal

Cada empreendimento deverá possuir uma página pública.

O empreendedor terá a possibilidade de:

1. Utilizar uma Landing Page padrão fornecida pelo próprio sistema;
2. Personalizar sua Landing Page;
3. Fazer upload/importação de uma página HTML própria;
4. Dependendo da estrutura necessária, permitir o envio de uma pasta contendo HTML, CSS, JavaScript, imagens e demais arquivos necessários;
5. Caso o empreendedor não possua uma página personalizada, utilizar automaticamente uma Landing Page padrão do sistema.

A ideia é que o sistema consiga trabalhar com algo semelhante a:

```text
Empreendimento
       │
       ├── Landing Page padrão
       │
       └── Landing Page personalizada
                │
                ├── HTML
                ├── CSS
                ├── JavaScript
                ├── Imagens
                └── outros assets necessários
```

No painel administrativo, quero algo intuitivo como:

**Landing Page do empreendimento**

* Status da página;
* Página padrão/personalizada;
* Botão "Carregar página personalizada";
* Possibilidade de importar HTML ou estrutura completa da página;
* Visualizar página;
* Ativar/desativar página personalizada;
* Voltar para a página padrão;
* Se possível, visualizar uma prévia antes de publicar.

## O que você deve fazer AGORA

### 1. Analise o projeto inteiro

Antes de alterar qualquer coisa, examine:

* Estrutura de diretórios;
* Backend;
* Frontend;
* Frameworks utilizados;
* Banco de dados;
* Models;
* Views;
* URLs/rotas;
* Templates;
* Sistema de autenticação;
* Sistema de usuários;
* Sistema de permissões;
* Entidades relacionadas a empreendimentos;
* Painel administrativo;
* Área do cliente;
* Sistema de arquivos/uploads;
* Configurações existentes;
* Padrões de código;
* Componentes reutilizáveis;
* APIs existentes;
* Estratégia atual de armazenamento de arquivos.

Não presuma que determinada estrutura existe. **Confirme no código.**

### 2. Entenda o domínio do sistema

Identifique:

* O que representa um empreendimento;
* Quem é o administrador/empreendedor;
* Quem é o usuário/cliente;
* Como um empreendimento é identificado;
* Como o usuário acessa um empreendimento;
* Se já existe algum conceito de página pública;
* Como URLs públicas são construídas;
* Onde seria mais natural encaixar a Landing Page.

Explique brevemente como você entendeu o funcionamento atual do sistema.

### 3. Pense na arquitetura da funcionalidade

Antes de programar, proponha uma arquitetura para essa funcionalidade.

Analise principalmente:

* Como armazenar a Landing Page;
* Como armazenar arquivos HTML;
* Como armazenar CSS, JS e imagens;
* Se devemos armazenar os arquivos no banco ou no filesystem/storage;
* Como organizar os arquivos de cada empreendimento;
* Como identificar qual página está ativa;
* Como fazer fallback para a Landing Page padrão;
* Como servir uma página personalizada;
* Como lidar com assets relativos;
* Como permitir atualização da página;
* Como remover/substituir uma página anterior;
* Como criar uma prévia;
* Como publicar/despublicar;
* Como controlar permissões.

### 4. Considere diferentes formas de importação

Analise tecnicamente estas possibilidades:

#### Opção A — Upload de um arquivo HTML

Exemplo:

```text
index.html
```

Nesse caso, avalie como tratar CSS, JS e imagens externas ou incorporados.

#### Opção B — Upload de uma pasta

Exemplo:

```text
meu-site/
├── index.html
├── css/
│   └── style.css
├── js/
│   └── script.js
├── images/
│   ├── logo.png
│   └── banner.jpg
└── assets/
```

Avalie a melhor maneira de receber essa estrutura no navegador.

#### Opção C — Upload de ZIP

Considere se seria tecnicamente melhor permitir:

```text
meu-site.zip
```

e o sistema extrair e validar sua estrutura.

Compare as alternativas e indique qual é a mais adequada para o projeto atual.

### 5. Segurança

Essa parte é extremamente importante.

Uma página HTML personalizada enviada por um empreendedor pode conter:

* JavaScript;
* CSS;
* imagens;
* iframes;
* links externos;
* scripts de terceiros;
* formulários;
* códigos potencialmente perigosos.

Analise os riscos de permitir que usuários façam upload de HTML e JavaScript.

Identifique:

* XSS;
* acesso indevido;
* execução de código;
* manipulação de arquivos;
* path traversal;
* arquivos maliciosos;
* acesso a arquivos do sistema;
* problemas com MIME types;
* arquivos executáveis;
* isolamento entre empreendimentos;
* riscos para outros usuários;
* riscos para o próprio painel administrativo.

Proponha uma estratégia segura de armazenamento e publicação.

**Não implemente uma solução insegura apenas para fazer a funcionalidade funcionar.**

### 6. Landing Page padrão

Pense também na Landing Page padrão do sistema.

Ela deve ser:

* moderna;
* elegante;
* simples;
* responsiva;
* adaptável ao empreendimento;
* visualmente profissional.

Idealmente, ela poderia utilizar informações já cadastradas no empreendimento, como:

* Nome;
* Logo;
* Imagens;
* Descrição;
* Endereço;
* Contatos;
* WhatsApp;
* Redes sociais;
* Produtos/serviços;
* outras informações disponíveis no sistema.

Antes de criar novos campos, verifique se essas informações já existem.

### 7. Experiência do administrador

Proponha como essa funcionalidade deveria aparecer no painel administrativo.

Quero uma experiência simples, por exemplo:

```text
Landing Page
────────────────────────────────

Status: ● Publicada

Página atual:
[ Página padrão ]

[ Visualizar página ]

────────────────────────────────

Personalização

[ Carregar página personalizada ]

Formatos aceitos:
HTML / ZIP

[ Visualizar prévia ]

[ Publicar ]

────────────────────────────────

[ Restaurar página padrão ]
```

Não precisa seguir exatamente esse layout. Use-o apenas como referência conceitual.

### 8. Experiência do cliente

Analise como o cliente deverá acessar a página pública.

Considere:

* URL amigável;
* identificação do empreendimento;
* responsividade;
* carregamento rápido;
* SEO básico;
* favicon;
* título da página;
* metatags;
* Open Graph;
* compartilhamento em redes sociais.

Se o sistema já possui uma estratégia para URLs públicas, reutilize-a.

### 9. Banco de dados

Verifique se será necessário criar ou alterar Models.

Caso seja necessário, proponha:

* novos Models;
* relacionamentos;
* campos;
* status;
* timestamps;
* versionamento, se fizer sentido;
* histórico de páginas;
* página ativa.

Não crie tabelas ou campos desnecessários.

### 10. Não quebre o sistema existente

Essa funcionalidade deve ser integrada ao sistema atual.

Priorize:

* reutilização;
* baixo acoplamento;
* separação de responsabilidades;
* segurança;
* manutenção futura;
* escalabilidade;
* compatibilidade com o código existente.

Não reestruture partes do sistema que não precisam ser alteradas.

## Como quero que você responda

**Nesta primeira etapa NÃO implemente a funcionalidade ainda.**

Depois de analisar o projeto, apresente:

### 1. Entendimento atual

Explique o que você entendeu do sistema.

### 2. Pontos do projeto envolvidos

Mostre quais arquivos, Models, Views, URLs, componentes ou módulos existentes provavelmente serão afetados.

### 3. Arquitetura proposta

Explique como você implementaria a funcionalidade.

### 4. Alternativas

Compare as possíveis estratégias de upload/importação:

* HTML;
* pasta;
* ZIP;
* outras alternativas que considerar relevantes.

Apresente vantagens, desvantagens e sua recomendação.

### 5. Segurança

Explique os principais riscos e como pretende isolá-los.

### 6. Banco de dados

Mostre quais alterações seriam necessárias, caso existam.

### 7. Fluxo da funcionalidade

Descreva o fluxo:

```text
Administrador
      ↓
Seleciona empreendimento
      ↓
Landing Page
      ↓
Carrega página personalizada
      ↓
Validação
      ↓
Armazenamento
      ↓
Pré-visualização
      ↓
Publicação
      ↓
Página pública
```

Adapte o fluxo conforme sua análise.

### 8. Plano de implementação

Divida a implementação em pequenas etapas.

Por exemplo:

```text
FASE 1 — Estrutura do banco
FASE 2 — Sistema de armazenamento
FASE 3 — Upload
FASE 4 — Validação
FASE 5 — Pré-visualização
FASE 6 — Publicação
FASE 7 — Landing Page padrão
FASE 8 — Interface administrativa
FASE 9 — Página pública
FASE 10 — Segurança e testes
```

Adapte as fases ao projeto real.

### 9. Só depois aguarde minha aprovação

Não escreva código ainda.

Depois de apresentar a análise e o plano, **pare e aguarde minha aprovação**.

Quando eu aprovar, implementaremos uma fase por vez.

## Regra importante

Você é um desenvolvedor trabalhando em um projeto existente.

Portanto:

> **Primeiro entender → depois analisar → depois propor → depois validar comigo → somente então implementar.**

Não invente estruturas que não existem no projeto.

Não altere arquivos sem necessidade.

Não tente implementar toda a funcionalidade de uma vez.

Sempre explique o impacto das alterações antes de realizá-las.

Priorize uma solução profissional, segura, simples de manter e coerente com a arquitetura já existente.



Outra Ideia:

# Análise de Viabilidade e Impacto — Sistema de Parâmetros e Fluxos Configuráveis

Você tem acesso completo ao código-fonte atual deste projeto.

O projeto é o **Agenda Fácil**, desenvolvido em Django, atualmente voltado para pequenos prestadores de serviços que trabalham com agendamento, como barbeiros, manicures, cabeleireiros, tatuadores, personal trainers, fotógrafos, professores particulares e outros negócios semelhantes.

Antes de implementar qualquer código, quero que você faça uma **análise técnica, arquitetural e de produto** sobre uma nova ideia que quero incorporar ao sistema.

## 1. Contexto da ideia

Quero tornar o Agenda Fácil mais flexível para diferentes tipos de negócios.

Atualmente, o sistema trabalha principalmente com a ideia tradicional de:

> cliente escolhe serviço → escolhe horário → realiza o agendamento.

Esse fluxo funciona muito bem para negócios onde o serviço possui um preço e duração previamente definidos.

Porém, existem negócios em que o processo comercial é diferente.

### Exemplo 1 — Serviço com preço definido

Uma manicure pode ter:

* Serviço: Manicure
* Preço: R$ 50
* Duração: 60 minutos

Nesse caso, faz sentido:

> Cliente → escolhe serviço → vê preço → escolhe horário → agenda.

### Exemplo 2 — Tatuador

Um tatuador pode precisar conversar com o cliente antes.

O preço pode depender de:

* tamanho;
* local do corpo;
* complexidade;
* quantidade de sessões;
* desenho;
* orçamento personalizado.

Nesse cenário, o fluxo pode ser:

> Cliente → entra em contato → negocia orçamento → define serviço → agenda.

Ou seja, nem sempre o agendamento deve ser necessariamente o primeiro passo.

## 2. Nova ideia

Quero avaliar a criação de uma área de **Parâmetros do Negócio**.

Nessa tela, o empreendedor poderia ativar ou desativar determinados comportamentos do sistema.

A ideia inicial é utilizar parâmetros simples, por exemplo:

> [✓] Cancelar automaticamente agendamentos quando o cliente não comparecer

Descrição:

> Após o horário do agendamento, caso o atendimento ainda não tenha sido confirmado como realizado, o sistema poderá classificá-lo automaticamente como "Não compareceu".

Porém, perceba que essa regra provavelmente exige outro mecanismo:

* confirmação de comparecimento;
* confirmação manual pelo empreendedor;
* ou alguma outra forma de determinar se o cliente realmente compareceu.

Portanto, **não quero que você simplesmente implemente esse exemplo**.

Quero que você analise o conceito como uma possível arquitetura geral do sistema.

## 3. Objetivo principal

Quero descobrir se é viável transformar o Agenda Fácil em um sistema onde cada negócio possa configurar determinados comportamentos sem precisar alterar código.

O empreendedor poderia ter uma tela semelhante a:

### Parâmetros do negócio

**Agendamento**

[✓] Permitir que clientes façam agendamentos diretamente

Descrição:
Permite que clientes realizem reservas diretamente pela página pública.

[ ] Exigir confirmação do empreendedor antes de confirmar um agendamento

Descrição:
O cliente solicita o horário e o agendamento fica aguardando aprovação do empreendedor.

[✓] Permitir cancelamento pelo cliente

Descrição:
Permite que o cliente cancele seu próprio agendamento através do link de cancelamento.

[ ] Exigir antecedência mínima para cancelamento

Descrição:
Define um período mínimo antes do atendimento para que o cliente possa cancelar.

### Atendimento

[✓] Permitir marcar cliente como "Não compareceu"

Descrição:
Permite registrar quando um cliente não comparece ao atendimento.

[ ] Solicitar confirmação de comparecimento

Descrição:
Permite registrar se o cliente compareceu antes de finalizar automaticamente o atendimento.

### Preço

[✓] Exibir preço dos serviços na página pública

Descrição:
Quando desativado, os preços não serão exibidos para os clientes.

### Fluxo comercial

[✓] Permitir contato antes do agendamento

Descrição:
Permite que o cliente entre em contato com o empreendedor antes de realizar uma reserva.

E assim por diante.

## 4. Atenção: não quero apenas uma lista de flags

Quero que você avalie profundamente a arquitetura.

Analise se seria melhor utilizar:

* campos booleanos diretamente em `Business`;
* uma entidade `BusinessSettings`;
* uma entidade de parâmetros configuráveis;
* enums;
* regras de negócio;
* estratégia/pattern de configuração;
* serviços responsáveis por interpretar as configurações;
* outro modelo arquitetural.

O principal objetivo é evitar uma arquitetura onde futuramente existam dezenas de condições espalhadas pelo código como:

`if business.allow_booking`
`if business.require_confirmation`
`if business.show_price`
`if business.auto_cancel`
`if business.allow_customer_cancel`
etc.

Quero que você avalie como manter o código sustentável conforme o número de configurações crescer.

## 5. Analise o projeto atual

Antes de sugerir qualquer alteração, percorra e compreenda a arquitetura atual.

Analise principalmente:

* `Business`
* `Service`
* `Appointment`
* `Customer`
* `WorkingDay`
* `WorkingHours`
* `BusinessNotification`
* views
* forms
* services
* URLs
* templates
* testes
* migrations
* regras de disponibilidade
* fluxo público de agendamento
* fluxo administrativo
* estados dos agendamentos
* landing page
* dashboard

Considere também as decisões arquiteturais já tomadas no projeto.

Não substitua decisões existentes sem justificar tecnicamente.

## 6. Analise de impacto

Identifique quais partes do sistema seriam afetadas pela introdução de um sistema de parâmetros.

Classifique cada impacto como:

* baixo;
* médio;
* alto;
* crítico.

Para cada impacto, explique:

1. qual arquivo/model/view/service seria afetado;
2. por que seria afetado;
3. que tipo de alteração seria necessária;
4. se existe risco de quebrar funcionalidades existentes.

## 7. Analise especificamente o fluxo de agendamento

Avalie como tornar configurável o fluxo atual.

Hoje existe um fluxo onde o cliente seleciona:

* negócio;
* serviço;
* data;
* horário;
* nome;
* telefone;

e o agendamento é criado como confirmado.

Analise como poderíamos suportar diferentes comportamentos, por exemplo:

### Fluxo A — Agendamento direto

Cliente escolhe serviço → horário → confirma.

### Fluxo B — Agendamento sujeito à aprovação

Cliente escolhe serviço → horário → solicita → empreendedor aprova → confirmado.

### Fluxo C — Contato antes do agendamento

Cliente escolhe serviço → entra em contato → negocia → depois realiza o agendamento.

### Fluxo D — Serviço sem preço definido

Cliente pode visualizar o serviço, mas o preço não é apresentado ou é apresentado como "Sob consulta".

### Fluxo E — Serviço personalizado

O empreendedor pode precisar coletar informações adicionais antes de confirmar o atendimento.

Não implemente esses fluxos.

Apenas avalie se a arquitetura atual conseguiria suportá-los e qual seria a melhor forma de preparar o sistema para isso.

## 8. Analise o exemplo do "não comparecimento"

Avalie especificamente esta ideia:

> "Após passar o horário do agendamento e o cliente não tiver comparecido, cancelar automaticamente."

Quero que você identifique problemas conceituais nessa regra.

Por exemplo:

* Como o sistema saberia que o cliente não compareceu?
* Deveria existir confirmação de comparecimento?
* O empreendedor deveria confirmar presença?
* O sistema poderia considerar automaticamente como `no_show` depois de determinado tempo?
* Deveria existir uma janela de tolerância?
* Deveria existir um parâmetro como "tempo de tolerância após o horário"?
* O status `no_show` atual já é suficiente?
* Seria melhor criar novos estados?
* Seria necessário algum job/task agendado?
* Como isso funcionaria sem Celery atualmente?
* Essa regra poderia ser executada sob demanda?
* Quais problemas poderiam ocorrer se o sistema ficar algumas horas sem ser acessado?

Analise essas possibilidades.

## 9. Descubra conflitos entre parâmetros

Uma preocupação importante é que parâmetros configuráveis podem gerar combinações inválidas.

Exemplo:

* exigir confirmação do empreendedor;
* cancelar automaticamente após o horário;
* não permitir alteração manual;
* não permitir cancelamento pelo cliente.

Quero que você identifique possíveis conflitos desse tipo.

Crie exemplos de combinações problemáticas e explique como a arquitetura poderia impedir configurações incoerentes.

## 10. Diferencie configuração de regra de negócio

Quero que você determine quais comportamentos realmente deveriam ser configuráveis pelo empreendedor e quais deveriam permanecer como regras internas do sistema.

Por exemplo:

### Possivelmente configurável

* mostrar ou ocultar preço;
* permitir cancelamento pelo cliente;
* exigir aprovação;
* permitir agendamento direto;
* tempo de tolerância;
* permitir contato antes do agendamento;
* comportamento de notificações.

### Possivelmente não configurável

* isolamento entre negócios;
* segurança;
* autorização;
* proteção CSRF;
* integridade dos dados;
* prevenção de conflitos de horários;
* regras de concorrência;
* proteção contra manipulação de parâmetros.

Analise essa separação.

## 11. UX da tela de parâmetros

Avalie como essa tela deveria funcionar.

Quero algo simples para o empreendedor.

Não quero apresentar conceitos técnicos.

Cada configuração deveria possuir:

* nome;
* descrição clara;
* controle de ativação/desativação;
* eventualmente um campo adicional quando necessário;
* indicação de dependências quando existir;
* eventualmente aviso quando uma configuração afetar outra.

Analise se seria melhor organizar em categorias, por exemplo:

* Agendamentos
* Atendimento
* Clientes
* Preços
* Notificações
* Página pública
* Comunicação
* Outros

Também avalie se determinadas configurações deveriam aparecer somente quando outra configuração estiver ativada.

## 12. Impacto no banco de dados

Proponha uma possível modelagem.

Compare pelo menos:

### Opção A

Adicionar diversos campos diretamente em `Business`.

### Opção B

Criar `BusinessSettings` com campos de configuração.

### Opção C

Criar uma estrutura genérica de parâmetros.

Para cada opção, explique:

* vantagens;
* desvantagens;
* escalabilidade;
* facilidade de manutenção;
* tipagem;
* validação;
* consultas;
* migrações;
* performance;
* facilidade de testes;
* risco de virar uma estrutura excessivamente genérica.

No final, recomende uma abordagem.

## 13. Impacto nos testes

Analise como essa mudança afetaria os testes existentes.

Atualmente o projeto possui uma suíte significativa de testes e o último estado registrado indica 62 testes aprovados.

Não quero simplesmente aumentar testes indiscriminadamente.

Quero uma estratégia.

Explique:

* quais regras novas precisam de testes;
* quais combinações precisam de testes;
* quais testes existentes precisam ser adaptados;
* como evitar explosão combinatória de testes;
* como criar testes parametrizados quando fizer sentido.

## 14. Compatibilidade com o sistema atual

A implementação deve ser incremental.

Um negócio existente não pode quebrar simplesmente porque o sistema ganhou parâmetros.

Defina como deveria funcionar:

* valores padrão;
* migração;
* negócios antigos;
* novos negócios;
* ausência de configuração;
* comportamento de fallback.

Idealmente, um negócio existente deveria continuar funcionando exatamente como funciona hoje caso nenhum parâmetro seja alterado.

Avalie isso.

## 15. Compatibilidade com futuras funcionalidades

Analise se essa arquitetura poderia futuramente suportar:

* WhatsApp;
* e-mail;
* pagamentos;
* sinal;
* múltiplos profissionais;
* fila;
* lista de espera;
* calendário externo;
* diferentes tipos de serviços;
* orçamentos;
* aprovação de agendamento;
* clientes recorrentes;
* promoções;
* diferentes políticas de cancelamento.

O objetivo não é implementar essas funcionalidades agora.

Quero apenas saber se a arquitetura proposta deixaria o sistema preparado para crescer.

## 16. Segurança

Analise se permitir que o empreendedor altere comportamentos poderia criar riscos.

Considere:

* autorização;
* manipulação de parâmetros;
* acesso entre negócios;
* alteração via POST;
* CSRF;
* exposição de informações;
* alteração de regras críticas;
* configurações que poderiam comprometer integridade dos agendamentos.

## 17. Performance

Avalie o impacto de consultar parâmetros constantemente.

Por exemplo:

Se uma página de agendamento precisa verificar 5 ou 10 configurações, isso poderia gerar consultas adicionais ao banco?

Analise possibilidades como:

* `select_related`;
* cache;
* carregar configurações uma vez;
* objeto de configuração em memória durante a requisição;
* outras estratégias.

Não implemente cache sem necessidade. Quero uma avaliação de custo/benefício.

## 18. Não implemente ainda

IMPORTANTE:

Nesta etapa você NÃO deve alterar o código.

Não crie migrations.

Não altere models.

Não crie views.

Não crie templates.

Não escreva código de implementação.

Primeiro quero apenas a análise.

## 19. Entregável esperado

Ao final, entregue um relatório dividido exatamente nestas partes:

### 1. Resumo executivo

Diga se a ideia é:

* inviável;
* viável com grandes alterações;
* viável com alterações moderadas;
* altamente viável.

Explique resumidamente o motivo.

### 2. Diagnóstico da arquitetura atual

Explique como o sistema está estruturado hoje e quais características favorecem ou dificultam essa evolução.

### 3. Impacto técnico

Tabela:

| Área | Impacto | Motivo | Alteração necessária |
| ---- | ------- | ------ | -------------------- |

### 4. Arquiteturas possíveis

Compare as alternativas de modelagem.

### 5. Arquitetura recomendada

Escolha uma abordagem e justifique tecnicamente.

### 6. Modelo conceitual

Descreva como funcionaria:

> Business → Configurações → Regras → Serviços → Fluxos

Se necessário, proponha novas entidades conceituais.

### 7. Parâmetros iniciais recomendados

Liste aproximadamente 10 a 20 parâmetros que fariam sentido para o Agenda Fácil.

Para cada um:

* nome;
* tipo;
* valor padrão;
* descrição para o empreendedor;
* impacto no sistema;
* dependências.

Não implemente esses parâmetros.

### 8. Regras de dependência

Mostre quais parâmetros dependem de outros.

### 9. Fluxos que poderiam ser suportados

Mostre como a mesma arquitetura poderia suportar:

* agendamento direto;
* aprovação;
* orçamento antes do agendamento;
* contato antes do agendamento;
* serviço sem preço;
* serviço personalizado.

### 10. Exemplo do no-show

Explique uma arquitetura adequada para lidar com comparecimento e ausência.

### 11. Impacto nos testes

Proponha estratégia de testes.

### 12. Impacto na segurança

Liste riscos e medidas.

### 13. Impacto na performance

Liste riscos e medidas.

### 14. Compatibilidade com o que já existe

Explique como preservar o comportamento atual.

### 15. Roadmap de implementação

Divida a implementação em pequenas etapas.

Exemplo:

Fase 1 — infraestrutura de configurações

Fase 2 — tela de parâmetros

Fase 3 — primeiro parâmetro real

Fase 4 — segundo parâmetro

etc.

Não implemente nenhuma dessas fases agora.

### 16. Riscos arquiteturais

Liste o que pode dar errado se essa ideia for implementada de forma inadequada.

### 17. Veredito final

Responda objetivamente:

**Devemos implementar essa ideia?**

E dê uma nota de 0 a 10 para:

* viabilidade técnica;
* valor para o produto;
* complexidade;
* risco;
* escalabilidade.

## 20. Regra fundamental da análise

Não quero uma resposta genérica.

Baseie sua análise no código e na arquitetura REAL existente neste projeto.

Sempre que citar uma conclusão técnica, procure relacioná-la aos models, services, views, testes e decisões arquiteturais existentes.

Não invente arquivos, models ou funcionalidades que não existam.

Se algo não puder ser determinado apenas analisando o projeto, diga explicitamente:

> "Não foi possível determinar isso com segurança a partir do código analisado."

Também diferencie claramente:

* o que já existe;
* o que você está inferindo;
* o que é recomendação arquitetural.

Mais importante:

**não comece a implementar.**

Esta etapa é exclusivamente de análise e planejamento.
