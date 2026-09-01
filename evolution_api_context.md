# Contexto Técnico — Integração com Evolution API

## 1. Objetivo deste documento

Este documento deve ser usado como contexto técnico para uma IA responsável por implementar uma integração entre uma aplicação e a **Evolution API**, especialmente para conexão e gerenciamento de instâncias WhatsApp.

A IA deve tratar a documentação oficial e o código oficial da Evolution API como fontes de verdade. Não deve inventar endpoints, parâmetros, payloads, respostas ou comportamentos.

Documentação oficial:
- https://docs.evolutionfoundation.com.br/evolution-api
- https://github.com/evolution-foundation/docs-evolution
- https://github.com/evolution-foundation/evolution-api

A documentação oficial atualmente mantém referências para **v1 e v2**, com v2 como versão padrão. O repositório de documentação também contém os arquivos OpenAPI das versões. 

---

## 2. O que é a Evolution API

A Evolution API é uma API REST para integração com WhatsApp e outros canais de comunicação.

Ela pode trabalhar com diferentes provedores/conexões, incluindo:

- WhatsApp via Baileys;
- WhatsApp Cloud API;
- Webhooks;
- WebSocket;
- Integrações com serviços externos.

A aplicação que está sendo desenvolvida NÃO deve implementar diretamente o protocolo do WhatsApp. Ela deve conversar com a Evolution API por HTTP/REST e receber eventos assíncronos por webhook quando necessário.

Arquitetura conceitual:

```text
Aplicação
   |
   | HTTP / REST
   v
Evolution API
   |
   +--> Baileys / WhatsApp Web
   |
   +--> WhatsApp Cloud API
   |
   +--> Webhooks / eventos
```

---

## 3. Conceito de instância

A Evolution API trabalha com o conceito de **instance**.

Uma instância representa uma conexão configurada na Evolution API.

O sistema da aplicação deve manter seu próprio relacionamento entre:

```text
Usuário/Conta
    |
    +--> Instância Evolution
              |
              +--> Número WhatsApp
              |
              +--> Estado da conexão
```

A aplicação não deve assumir que o nome da instância é o número de telefone.

Exemplo conceitual:

```text
instanceName = cliente_123_whatsapp
```

O nome deve ser único e compatível com as regras da Evolution API.

---

# 4. Autenticação

A Evolution API utiliza uma API Key para autenticar requisições.

Normalmente a aplicação envia:

```http
apikey: SUA_API_KEY
```

A API Key da Evolution NÃO deve ser colocada diretamente no frontend.

A arquitetura recomendada é:

```text
Frontend
   |
   v
Backend da aplicação
   |
   | apikey
   v
Evolution API
```

A API Key deve permanecer em variável de ambiente ou mecanismo seguro de secrets.

Exemplo:

```env
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=chave-secreta
```

Nunca:

- colocar a API Key no JavaScript do navegador;
- colocar a API Key em código versionado;
- salvar a chave em banco sem necessidade;
- retornar a API Key para o frontend.

---

# 5. Fluxo geral de conexão

O fluxo esperado para conectar um WhatsApp é:

```text
1. Usuário solicita conexão
        |
        v
2. Backend cria uma instância
        |
        v
3. Backend solicita conexão da instância
        |
        v
4. Evolution API retorna QR Code / código de pareamento
        |
        v
5. Frontend exibe o QR Code
        |
        v
6. Usuário escaneia o QR Code no WhatsApp
        |
        v
7. Evolution API processa a conexão
        |
        v
8. Evolution envia evento de atualização da conexão
        |
        v
9. Backend atualiza o estado da instância
        |
        v
10. Frontend mostra "Conectado"
```

A aplicação deve ser orientada a eventos sempre que possível.

Não assumir que uma chamada de conexão significa que o WhatsApp já está conectado.

---

# 6. Criar uma instância

A Evolution API possui endpoint para criação de instância.

O fluxo conceitual é:

```http
POST /instance/create
```

O backend deve montar o payload conforme a versão da Evolution API efetivamente instalada e conforme a documentação/OpenAPI dessa versão.

A IA deve:

1. verificar a versão da Evolution API;
2. consultar o endpoint correspondente na documentação;
3. conferir o schema do request;
4. conferir o schema da resposta;
5. implementar exatamente o contrato encontrado.

Não deve copiar cegamente exemplos de v1 para uma instalação v2.

---

# 7. Conectar uma instância

Para iniciar a conexão de uma instância, a documentação possui o endpoint:

```http
GET /instance/connect/{instanceName}
```

Exemplo conceitual:

```http
GET /instance/connect/minha-instancia
apikey: SUA_API_KEY
```

A resposta pode fornecer informações relacionadas ao pareamento, incluindo QR Code em Base64 e/ou código de pareamento.

Exemplo conceitual:

```json
{
  "pairingCode": null,
  "code": "...",
  "base64": "data:image/png;base64,...",
  "count": 1
}
```

IMPORTANTE:

A IA deve validar o formato real da resposta da versão instalada antes de implementar.

Não deve assumir que:

- `base64` sempre estará preenchido;
- `pairingCode` sempre estará preenchido;
- `code` sempre representa um QR Code;
- o QR Code ficará disponível indefinidamente.

---

# 8. QR Code

Se a Evolution API retornar:

```text
data:image/png;base64,...
```

o backend pode repassar esse conteúdo ao frontend.

O frontend pode exibir a imagem diretamente usando o valor Base64.

Exemplo conceitual:

```html
<img src="data:image/png;base64,..." />
```

O backend NÃO precisa necessariamente salvar o QR Code como arquivo.

A aplicação deve preferir manter o QR Code temporariamente em memória/estado da interface, salvo quando houver uma necessidade real de persistência.

---

# 9. Pairing Code

Dependendo do método de conexão e da versão/configuração, a Evolution API pode disponibilizar um código de pareamento.

O sistema deve tratar QR Code e pairing code como possibilidades distintas.

Não criar uma regra artificial dizendo que um sempre substituirá o outro.

A interface pode apresentar:

```text
QR Code
OU
Código de pareamento
```

conforme o que a Evolution API efetivamente retornar.

---

# 10. Verificar estado da conexão

A Evolution API possui endpoint para verificar o estado da instância:

```http
GET /instance/connectionState/{instanceName}
```

O backend deve usar esse endpoint quando precisar consultar explicitamente o estado atual.

Porém, a aplicação também deve considerar os eventos recebidos via webhook.

Estados devem ser tratados de acordo com os valores realmente retornados pela Evolution API.

Não criar uma enumeração arbitrária sem verificar os valores oficiais da versão utilizada.

---

# 11. Webhooks

Webhooks são fundamentais para a integração.

A Evolution API pode enviar eventos para um endpoint HTTP da aplicação.

Fluxo:

```text
WhatsApp
   |
   v
Evolution API
   |
   | POST webhook
   v
Backend da aplicação
```

A aplicação deve disponibilizar um endpoint público/roteável, por exemplo:

```text
POST /api/evolution/webhook/
```

O nome exato da rota é decisão da aplicação.

A Evolution API precisa ser configurada para apontar para essa URL.

---

# 12. Eventos de conexão

Um dos eventos importantes para o fluxo de conexão é:

```text
CONNECTION_UPDATE
```

Esse evento pode informar alterações no estado da conexão.

Outro evento relevante durante o pareamento pode ser:

```text
QRCODE_UPDATED
```

O backend deve processar esses eventos para manter o estado local atualizado.

Exemplo conceitual:

```text
QRCODE_UPDATED
    -> atualizar QR Code temporário

CONNECTION_UPDATE
    -> atualizar status da instância
```

Não presumir o payload exato. A IA deve consultar a documentação/schema da versão instalada.

---

# 13. Eventos de mensagens

Para sistemas que também precisam receber mensagens, eventos como:

```text
MESSAGES_UPSERT
MESSAGES_UPDATE
SEND_MESSAGE
```

podem ser relevantes.

O sistema deve distinguir:

```text
mensagem recebida
```

de:

```text
mensagem enviada pela própria aplicação
```

e não criar loops acidentais.

---

# 14. Webhook deve ser tratado com segurança

O endpoint de webhook é externo.

Portanto:

- validar a origem quando o mecanismo de assinatura/validação estiver disponível;
- validar estrutura do payload;
- não confiar cegamente nos dados recebidos;
- registrar erros;
- evitar processamento duplicado;
- evitar que um webhook inválido derrube a aplicação;
- responder rapidamente ao webhook e delegar processamento pesado para uma fila/background job quando necessário.

---

# 15. Idempotência

Eventos podem ser repetidos.

O backend deve ser projetado para tolerar duplicidade.

Para mensagens/eventos que possuem identificador único, utilizar esse identificador para evitar processamento duplicado.

Conceito:

```text
evento recebido
     |
     v
já processado?
   /      \
 SIM       NÃO
 |          |
ignorar    processar
```

Não assumir que cada evento será recebido exatamente uma vez.

---

# 16. Envio de mensagem

Para envio de texto, a Evolution API possui endpoint na categoria de mensagens:

```http
POST /message/sendText/{instanceName}
```

A IA deve consultar o schema da versão utilizada para determinar exatamente os campos obrigatórios.

Conceitualmente:

```json
{
  "number": "5511999999999",
  "text": "Olá!"
}
```

O payload acima é apenas ilustrativo.

A implementação final deve usar o schema oficial da versão instalada.

---

# 17. Fluxo de envio

```text
Frontend
   |
   | "Enviar mensagem"
   v
Backend
   |
   | POST Evolution API
   v
Evolution API
   |
   v
WhatsApp
```

O frontend não deve precisar conhecer:

- API Key da Evolution;
- URL interna da Evolution;
- detalhes de autenticação;
- estrutura interna da integração.

---

# 18. Desconectar

A Evolution API possui operação para logout/desconexão da instância.

A aplicação deve diferenciar:

```text
desconectar WhatsApp
```

de:

```text
excluir instância
```

São operações diferentes.

Antes de excluir definitivamente uma instância, a aplicação deve confirmar a intenção do usuário.

---

# 19. Excluir instância

A Evolution API também possui operação para exclusão de instância.

A aplicação deve:

1. confirmar a operação;
2. solicitar exclusão na Evolution;
3. somente depois atualizar/remover o registro local;
4. tratar falha parcial.

Nunca remover o registro local primeiro sem considerar o que acontece se a Evolution API falhar.

---

# 20. Reiniciar instância

Existe também operação de restart da instância.

Ela pode ser usada quando houver necessidade de reinicialização da conexão, mas não deve ser usada indiscriminadamente como solução para qualquer erro.

A aplicação deve primeiro identificar o estado e o motivo da falha.

---

# 21. Modelo de dados sugerido

A aplicação pode ter uma entidade semelhante a:

```text
EvolutionInstance
-------------------------
id
owner/user/account
instance_name
phone_number
status
provider
qr_code
pairing_code
last_connection_update
created_at
updated_at
```

Os campos exatos dependem do projeto.

Recomendação:

- não armazenar QR Code permanentemente sem necessidade;
- não armazenar API Key por instância se uma chave global já for suficiente;
- guardar o estado local apenas como representação/cache do estado da Evolution;
- manter timestamps de atualização.

---

# 22. Estado local x estado da Evolution

O banco da aplicação não deve ser considerado a fonte absoluta da verdade sobre a conexão.

Existem duas fontes:

```text
Banco da aplicação
      |
      | estado conhecido
      v
Evolution API
      |
      | estado real
      v
WhatsApp
```

Quando houver dúvida:

1. consultar a Evolution;
2. atualizar o estado local.

Webhooks podem manter o estado local sincronizado.

---

# 23. Arquitetura recomendada

Separar a integração em uma camada própria.

Exemplo:

```text
app/
├── integrations/
│   └── evolution/
│       ├── client
│       ├── services
│       ├── schemas
│       ├── webhook
│       └── exceptions
```

O restante da aplicação não deveria fazer requests HTTP diretamente para a Evolution.

Em vez disso:

```python
evolution_service.create_instance(...)
evolution_service.connect_instance(...)
evolution_service.get_connection_state(...)
evolution_service.send_text(...)
```

Isso facilita:

- testes;
- manutenção;
- troca de versão;
- tratamento de erros;
- mocks;
- futura troca de provedor.

---

# 24. Cliente HTTP

Criar um cliente centralizado para a Evolution API.

Conceitualmente:

```python
class EvolutionClient:
    def get(...)
    def post(...)
    def put(...)
    def delete(...)
```

Esse cliente deve cuidar de:

- URL base;
- API Key;
- timeout;
- headers;
- tratamento de HTTP errors;
- parsing JSON;
- logs;
- correlation/request ID quando aplicável.

Não espalhar:

```python
requests.get(...)
requests.post(...)
```

pela aplicação inteira.

---

# 25. Tratamento de erros

A integração deve diferenciar:

```text
Erro de autenticação
Erro de conexão
Timeout
Instância inexistente
Instância já conectada
WhatsApp desconectado
Payload inválido
Erro interno da Evolution
Erro interno da aplicação
```

Não transformar todos em:

```text
"Erro ao conectar"
```

O frontend deve receber uma mensagem amigável, enquanto os logs devem preservar detalhes técnicos suficientes para diagnóstico.

---

# 26. Timeouts e indisponibilidade

A Evolution API pode estar:

- desligada;
- reiniciando;
- sem banco;
- sem Redis;
- temporariamente indisponível;
- com uma instância desconectada.

O backend deve ter timeout HTTP.

Não deixar uma requisição web esperando indefinidamente.

---

# 27. Concorrência

Evitar duas operações simultâneas para a mesma instância quando elas forem incompatíveis.

Exemplo:

```text
Usuário clica "Conectar"
Usuário clica "Conectar" novamente
```

Não criar duas instâncias ou disparar múltiplos processos de conexão sem necessidade.

O backend deve verificar se já existe uma operação em andamento.

---

# 28. Frontend

O frontend deve conversar somente com o backend da aplicação.

Exemplo:

```text
Frontend
   |
   +--> POST /api/whatsapp/connect
   |
   +--> GET /api/whatsapp/status
   |
   +--> POST /api/whatsapp/disconnect
```

O backend conversa com:

```text
Evolution API
```

Isso mantém a arquitetura segura e desacoplada.

---

# 29. Atualização em tempo real

Existem três estratégias possíveis:

### Opção A — polling

Frontend pergunta periodicamente:

```text
GET /api/whatsapp/status
```

É simples e pode ser suficiente para projetos pequenos.

### Opção B — WebSocket/SSE

Backend envia atualização para o frontend assim que receber:

```text
CONNECTION_UPDATE
```

Melhor experiência em tempo real.

### Opção C — híbrida

Usar webhook para atualização do backend e polling como fallback.

Para um projeto simples, começar com polling pode ser aceitável. Não adicionar WebSocket apenas porque existe suporte na Evolution API.

---

# 30. Princípio: simples bem feito

A integração deve começar pelo menor fluxo funcional:

```text
Criar instância
      ↓
Conectar
      ↓
Mostrar QR Code
      ↓
Receber CONNECTION_UPDATE
      ↓
Mostrar conectado
      ↓
Enviar mensagem
      ↓
Receber mensagem
```

Somente depois adicionar:

- múltiplas instâncias;
- grupos;
- mídia;
- filas;
- WebSocket;
- Redis;
- armazenamento de mídia;
- automações;
- IA;
- analytics.

Não construir complexidade antes de existir necessidade real.

---

# 31. Variáveis de ambiente

Exemplo mínimo:

```env
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=
```

Em produção:

```env
EVOLUTION_API_URL=https://evolution.seudominio.com
EVOLUTION_API_KEY=
```

Nunca versionar secrets.

Usar:

```text
.env
```

ou secret manager apropriado.

---

# 32. Instalação da Evolution API

Se a própria IA também precisar configurar a Evolution API, deve consultar a documentação oficial da versão instalada.

A documentação atual de v2 considera serviços como PostgreSQL e Redis no ambiente de instalação.

Exemplo conceitual:

```text
Docker
   |
   +--> Evolution API
   |
   +--> PostgreSQL
   |
   +--> Redis
```

A instalação deve seguir os arquivos oficiais da versão utilizada.

Não copiar uma configuração antiga sem verificar compatibilidade.

---

# 33. Versionamento

Este ponto é obrigatório.

Antes de implementar:

```text
qual versão da Evolution API está rodando?
```

A IA deve descobrir/confirmar isso.

Depois:

```text
documentação da versão
        +
OpenAPI da versão
        +
código da versão
```

devem ser utilizados para validar a implementação.

A documentação oficial atualmente diferencia v1 e v2.

---

# 34. Fonte de verdade

Prioridade:

1. Código oficial da versão instalada;
2. OpenAPI oficial da versão;
3. Documentação oficial da versão;
4. Exemplos oficiais;
5. Issues oficiais do GitHub;
6. Outras fontes somente como apoio.

Nunca usar um tutorial aleatório como autoridade quando houver divergência com a implementação oficial.

---

# 35. Atenção à documentação

A documentação pode ficar incompleta, mudar ou conter exemplos de versões diferentes.

O repositório oficial de documentação atualmente possui referências OpenAPI separadas para v1 e v2.

Se houver dúvida sobre:

- endpoint;
- parâmetro;
- resposta;
- evento;
- nome de campo;

a IA deve consultar o OpenAPI e/ou código-fonte correspondente antes de decidir.

---

# 36. Regra contra alucinação

A IA DEVE seguir esta regra:

> Se não houver confirmação na documentação, OpenAPI ou código da versão utilizada, não inventar.

Em vez disso, informar:

```text
"Não consegui confirmar esse comportamento na versão X."
```

e investigar a fonte oficial.

---

# 37. Regra para endpoints

Nunca assumir que:

```text
v1 == v2
```

Mesmo que o endpoint pareça semelhante.

Antes de implementar:

```text
versão
endpoint
método HTTP
headers
path parameters
query parameters
body
response
erros
```

devem ser conferidos.

---

# 38. Regra para webhooks

O webhook deve ser implementado como uma API externa confiável apenas após validação.

O sistema deve:

```text
receber
  ↓
validar
  ↓
identificar evento
  ↓
identificar instância
  ↓
identificar entidade/evento
  ↓
garantir idempotência
  ↓
processar
  ↓
responder
```

Não misturar toda essa lógica dentro de uma única função gigante.

---

# 39. Regra para logs

Registrar informações úteis:

```text
instance_name
event_type
request_id
status_code
tempo da requisição
erro
```

Não registrar:

```text
API Key
tokens secretos
credenciais
dados sensíveis desnecessários
```

Cuidado também com logs contendo conteúdo integral de mensagens de usuários.

---

# 40. Testes mínimos

Antes de considerar a integração concluída, testar:

### Instância

- criar;
- consultar;
- conectar;
- verificar estado;
- reiniciar;
- desconectar;
- excluir.

### QR Code

- QR disponível;
- QR ausente;
- QR atualizado;
- QR expirado/trocado.

### Conexão

- conectando;
- conectado;
- desconectado;
- erro;
- reconexão.

### Mensagens

- envio de texto;
- erro de número;
- instância desconectada;
- Evolution indisponível.

### Webhook

- evento válido;
- evento inválido;
- evento duplicado;
- evento desconhecido;
- payload incompleto.

---

# 41. Critério de conclusão

A primeira versão da integração pode ser considerada funcional quando:

```text
[ ] Evolution API está acessível
[ ] Backend autentica corretamente
[ ] Instância pode ser criada
[ ] Instância pode ser conectada
[ ] QR Code pode ser exibido
[ ] Usuário consegue escanear
[ ] CONNECTION_UPDATE é recebido
[ ] Banco é atualizado
[ ] Interface mostra conectado
[ ] Mensagem de texto pode ser enviada
[ ] Mensagem recebida pode ser processada
[ ] Desconexão funciona
[ ] Erros básicos são tratados
[ ] API Key não é exposta
```

---

# 42. Instrução final para a IA desenvolvedora

Você deve atuar como um desenvolvedor responsável pela integração.

Antes de escrever código:

1. Entenda a arquitetura existente.
2. Identifique a versão da Evolution API.
3. Consulte a documentação oficial.
4. Consulte o OpenAPI quando necessário.
5. Identifique os endpoints realmente necessários.
6. Defina o fluxo mínimo.
7. Só então implemente.

Durante a implementação:

- faça alterações pequenas;
- não reescreva partes não relacionadas;
- não adicione dependências sem necessidade;
- não crie abstrações prematuras;
- mantenha a integração isolada;
- trate erros explicitamente;
- escreva testes para o comportamento crítico.

Quando houver dúvida:

```text
NÃO INVENTE.
INVESTIGUE.
```

Ao final de cada etapa, explique:

```text
O que foi implementado
O que foi alterado
Como testar
O que ainda falta
Quais decisões foram tomadas
Quais pontos dependem da versão da Evolution API
```

O objetivo é uma integração **simples, segura, testável e sustentável**, e não reproduzir toda a capacidade da Evolution API dentro da aplicação.
