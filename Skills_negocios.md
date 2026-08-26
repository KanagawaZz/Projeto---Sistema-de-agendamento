---
name: agenda-facil-dominio-negocio
description: Use esta skill sempre que for necessário entender, discutir ou tomar decisões sobre o domínio de negócio do Agenda Fácil — sistema de agendamento para pequenos prestadores de serviço. Cobre público-alvo, glossário, fluxos de empreendedor e cliente, regras de negócio, casos de borda e filosofia do produto. Use ao planejar novas funcionalidades, revisar regras, escrever textos para a página pública, ou validar se uma ideia faz sentido para o negócio.
---

# Domínio de Negócio: Agenda Fácil

## Visão geral

O Agenda Fácil é um sistema web de agendamento e gestão de atendimentos para
pequenos prestadores de serviços, como barbeiros, manicures, cabeleireiros,
tatuadores, personal trainers, fotógrafos, professores particulares e
técnicos/empreendedores que trabalham com agendamento de serviços em geral.

**Objetivo real do produto:** não é escalar para milhares de clientes. É
atender bem um número pequeno de prestadores locais (região de
Cuiabá/Várzea Grande), cobrando uma mensalidade simples, funcionando como
renda extra. Isso significa que decisões de produto devem priorizar
simplicidade operacional e confiabilidade sobre recursos avançados ou
crescimento agressivo.

**Filosofia:** "simples por fora, inteligente por dentro" — a experiência do
usuário (empreendedor e cliente) deve ser mínima e direta, mesmo quando a
lógica por trás (concorrência de horários, regras de disponibilidade) é
sofisticada.

## Público-alvo e personas

- **O empreendedor (usuário pagante):** dono de um pequeno negócio de
  serviços agendados. Geralmente não é técnico, quer resolver um problema
  prático — parar de agendar por WhatsApp/papel e evitar choque de horários.
  Tem baixa tolerância a telas complexas ou fluxos de configuração longos.
- **O cliente final (usuário do empreendedor):** a pessoa que agenda um
  horário com o empreendedor. Não tem conta no sistema, não quer se cadastrar,
  só quer escolher serviço + horário disponível e confirmar rápido, pelo
  celular.

## Glossário de domínio

- **Negócio (Business):** a entidade que representa o empreendedor dentro do
  sistema. Cada usuário tem exatamente um negócio.
- **Serviço (Service):** algo que o negócio oferece (ex: "corte masculino"),
  com preço, duração e margem de segurança (buffer) entre atendimentos.
- **Margem de segurança:** tempo extra somado à duração do serviço, para
  evitar que um atraso em um atendimento afete o próximo.
- **Horário de funcionamento (WorkingDay / WorkingHours):** configuração por
  dia da semana, podendo ter múltiplos intervalos no mesmo dia (ex: manhã e
  tarde) e podendo marcar o dia como fechado.
- **Página pública:** endereço único do negócio (via slug), acessível sem
  login, onde o cliente vê os serviços ativos e agenda.
- **Agendamento (Appointment):** reserva de um horário específico, vinculando
  serviço + data/hora + dados do cliente (nome e telefone, sem conta).
- **Token de cancelamento:** identificador seguro que permite ao cliente
  cancelar seu próprio agendamento sem precisar de login.
- **Disponibilidade:** o conjunto de horários que ainda podem ser reservados,
  calculado a partir do horário de funcionamento menos os agendamentos já
  confirmados e considerando duração + margem de segurança do serviço.

## Fluxo principal (ponta a ponta)

1. Empreendedor se cadastra e faz login.
2. Cadastra o negócio (gera slug automático único, editável mantendo
   identidade do negócio).
3. Cadastra serviços (preço, duração, margem de segurança) — pode
   ativar/desativar sem excluir.
4. Define horários de funcionamento por dia da semana, com múltiplos
   intervalos.
5. Publica a página pública (pode personalizar título, descrição, botão,
   tema visual; pode despublicar, caindo em um fallback com dados básicos).
6. Cliente acessa o link público, vê os serviços ativos, escolhe um,
   consulta datas/horários disponíveis.
7. Cliente agenda sem criar conta, informando apenas nome e telefone.
8. Sistema revalida a disponibilidade no servidor antes de confirmar
   (proteção contra condição de corrida — dois clientes tentando o mesmo
   horário).
9. Agendamento confirmado; cliente pode cancelar depois via token seguro;
   empreendedor pode cancelar agendamentos futuros pelo painel.

## Regras de negócio importantes

- Cada usuário possui **um único negócio** (relação 1:1).
- Serviços **inativos não aparecem** para o cliente, mas não são excluídos
  (preserva histórico).
- O cálculo de disponibilidade **sempre considera duração + margem de
  segurança** do serviço, não só a duração pura.
- Horários já ocupados **não são reexibidos** como disponíveis.
- **Isolamento total de dados entre negócios** — um empreendedor nunca acessa
  dados de outro.
- Toda reserva passa por **revalidação no servidor dentro de uma
  transação**, para evitar dois clientes reservando o mesmo horário
  simultaneamente. Quem perde a corrida recebe mensagem de indisponibilidade.
- Página pública usa apenas templates confiáveis do sistema — **cliente
  nunca pode subir HTML/JS/arquivos** para a página.
- Operações administrativas exigem autenticação, autorização e proteção
  CSRF.

## Casos de borda e decisões relevantes

- **Negócio despublicado:** a página pública cai em um fallback com dados
  básicos em vez de sumir — evita links quebrados que já foram compartilhados.
- **Dia marcado como fechado não pode ter intervalo de horário** (validação
  ativa).
- **Tipos de negócio com preço/negociação variável** (ex: tatuadores, que
  negociam valor antes de fechar) são um caso ainda em aberto — motivou a
  ideia de uma tela de parâmetros/flags configuráveis por tipo de negócio
  (ex: negócio de valor fixo vs. negócio que negocia antes; flag de
  cancelamento automático se o cliente não confirmar presença após o
  horário).
- **Concorrência real em produção:** SQLite (ambiente de desenvolvimento)
  não tem bloqueio de linha real como PostgreSQL — a garantia completa de
  concorrência simultânea só é validada após migração para PostgreSQL.

## Como pensar sobre novas funcionalidades

Ao avaliar uma ideia nova para o Agenda Fácil, priorize nesta ordem:

1. **Resolve uma dor real de um prestador pequeno e não-técnico?** (validado
   com conversas reais com empreendedores, não suposição)
2. **Mantém o fluxo do cliente sem conta/sem fricção?**
3. **Não adiciona complexidade operacional desproporcional** ao tamanho do
   negócio (evitar overengineering: sem microsserviços, sem frontend
   separado, sem features que só fazem sentido em escala grande).
4. **Preserva isolamento de dados e proteção contra condição de corrida** em
   qualquer fluxo que envolva reserva de horário.

Se uma ideia não passa nesses critérios, provavelmente não é prioridade para
o estágio atual do produto.