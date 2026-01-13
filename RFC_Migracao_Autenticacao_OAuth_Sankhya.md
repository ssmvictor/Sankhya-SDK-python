# RFC — Migração Técnica de Autenticação: LEGADO → OAuth2 (Sankhya SDK)

**ID:** RFC-Auth-2026-001  
**Estado:** Draft  
**Autor:** ChatGPT (assistente técnico)  
**Última atualização:** 2026-01-12

---

## Sumário executivo

Este RFC define a especificação técnica para migrar a camada de autenticação do SDK/integrador Sankhya do modelo **legado** (username + password + appkey + token em XML) para **OAuth2** com payloads **JSON**. O documento avança o PRD anterior, fornecendo detalhes de API, contratos, modelos de dados, fluxos, considerações de segurança, testes, rollback e critérios de aceitação para implementação e revisão por engenharia.

Objetivo: criar uma especificação executável que permita ao time de engenharia implementar a migração com risco mínimo e alto grau de automação nos testes e rollout.

---

## Motivação

- Segurança: reduzir exposição de credenciais e adotar tokens de curta duração.
- Conformidade: alinhar integração com práticas modernas de APIs (OAuth2).
- Confiabilidade: padronizar tratamento de erros e renovação de sessão.
- Roadmap: reduzir dependência do fluxo legado que está sendo descontinuado.

---

## Escopo

**Incluído**
- Implementação cliente OAuth2 (`/authenticate`) com JSON.
- TokenManager: armazenamento, expiração, refresh (quando disponível).
- SankhyaSession: wrapper HTTP que injeta `Authorization: Bearer`.
- Fallback controlado para login legado (feature-flag).
- Documentação técnica e testes unitários/integration mocks.

**Excluído**
- Refatoração de payloads XML de negócio além do necessário para autenticação.
- Suporte a múltiplos provedores OAuth além da Sankhya.
- UI/CLI.

---

## Requisitos técnicos

### Requisitos funcionais (resumidos)
- RFC-F1: `POST /authenticate` com JSON (`client_id`, `client_secret` ou credenciais conforme spec Sankhya).
- RFC-F2: receber `access_token`, `expires_in` e opcional `refresh_token`.
- RFC-F3: armazenamento seguro do token e injeção automática no header `Authorization`.
- RFC-F4: renovação automática do token usando `refresh_token` quando disponível.
- RFC-F5: logout que invalida token e limpa storage.
- RFC-F6: fallback legado sob `SANKHYA_USE_LEGACY_LOGIN=true`, com warning no log.

### Requisitos não funcionais
- Compatível com Python 3.9+; design modular; dependências mínimas.
- Timeouts configuráveis; retry com backoff exponencial para erros 5xx e timeouts.
- Logs sem exposição de segredos (masking).
- Test coverage mínimo 80% para módulos core.

---

## Proposta de API / Contratos

### Endpoint principal (OAuth)
**Request**
```
POST {AUTH_BASE_URL}/authenticate
Content-Type: application/json

{
  "client_id": "<client_id>",
  "client_secret": "<client_secret>",
  "grant_type": "client_credentials" // ou conforme Sankhya docs
}
```

**Successful Response (200)**
```
{
  "access_token": "eyJ....",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "rft_...." // opcional
}
```

**Error Response (4xx/5xx)**
```
{
  "error": "invalid_client",
  "error_description": "Client credentials are invalid."
}
```

> Observação: adaptar nomes dos campos exatamente conforme a resposta real da Sankhya. O RFC espera validação com ambiente de homologação para confirmar nomes de campo.

### Token refresh (se aplicável)
```
POST {AUTH_BASE_URL}/token/refresh
Content-Type: application/json

{
  "refresh_token": "rft_...."
}
```

Resposta semelhante: novo `access_token`, `expires_in` e possivelmente novo `refresh_token`.

### Logout (se suportado)
```
POST {AUTH_BASE_URL}/logout
Authorization: Bearer <access_token>
```

Resposta 200 indica sucesso; caso contrário retornar erro.

---

## Modelos de dados (Python / Pydantic)

```py
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
```

TokenManager deverá manter:
- access_token
- expires_at (datetime calculada)
- refresh_token (opcional)
- client_id/client_secret (opcional: apenas se reauth automático for suportado)

---

## Componentes e Interfaces

### 1. OAuthClient
Responsável por chamadas diretas ao provedor de autenticação.

API pública:
- `authenticate(client_id, client_secret) -> AuthResponse`
- `refresh(refresh_token) -> AuthResponse` (se suportado)
- `revoke(access_token) -> None` (logout, se suportado)

Erros:
- Lança `AuthError` para 4xx, `AuthNetworkError` para problemas de rede.

### 2. TokenManager
Gerencia o ciclo de vida do token.

API pública:
- `get_token() -> str` (retorna token válido, renovando se necessário)
- `force_refresh() -> None`
- `clear() -> None`

Persistência:
- Em memória por padrão, com opção para plugin de armazenamento (file_encrypted, vault).

### 3. SankhyaSession
Wrapper HTTP que envia:
- Header `Authorization: Bearer <token>`
- `Content-Type: application/json` quando apropriado
- Retry/timeout
- Mapear erros HTTP para exceções do SDK

API pública:
- `get(path, **kwargs)`, `post(path, json=...)`, etc.

### 4. LegacyClient (opcional)
- `login(username, password, appkey, token) -> AuthResponseCompat`
- Internamente adapta resposta para TokenManager.

---

## Fluxos de sequência (textual)

### Fluxo de autenticação inicial
1. Aplicação chama `OAuthClient.authenticate`.
2. `OAuthClient` faz `POST /authenticate` e parseia `AuthResponse`.
3. `TokenManager` armazena `access_token` e `expires_at`.
4. `SankhyaSession` consulta `TokenManager.get_token()` e injeta header.

### Fluxo de token expirado (com refresh)
1. `SankhyaSession` detecta 401 (unauthorized).
2. Chama `TokenManager.force_refresh()`:
   - Se `refresh_token` presente, chama `OAuthClient.refresh`.
   - Se refresh bem-sucedido, retry da requisição original.
   - Senão, se credenciais originais armazenadas e reauth permitido, chama `authenticate`.
   - Caso contrário, lança `TokenExpiredError`.

---

## Tratamento de erros e códigos

- 400 Bad Request -> `AuthError` (invalid_payload)
- 401 Unauthorized -> `TokenExpiredError` ou `AuthError` (conforme contexto)
- 403 Forbidden -> `AuthError` (insufficient_scope)
- 5xx -> `AuthNetworkError` (retry with backoff)

Logs devem registrar códigos, timestamps e ids de correlação quando disponíveis, sem incluir tokens.

---

## Backward compatibility & Rollback plan

- Implementar fallback legado controlado por flag `SANKHYA_USE_LEGACY_LOGIN`.
- Rollback: reabilitar flag para apontar para legacy client e reiniciar serviços.
- Depreciação: registrar telemetria sobre uso do legacy para planejar remoção do código.

---

## Segurança

- Não persistir `client_secret` em texto plano.
- Recomendar uso de secret manager; support plugin interface para `SecretProvider`.
- Rotação: documentar procedimento para rotacionar `client_secret` e invalidar tokens.
- Rate limiting: aplicar proteção contra exaustão de credenciais (retries limitados).

---

## Testes

### Unit tests
- Mockar `POST /authenticate` para respostas 200 e 401.
- Testar `TokenManager.get_token()` e renovação.
- Testar `SankhyaSession` retry behavior.

### Integration tests (mock / sandbox)
- Rodar suite contra sandbox Sankhya, validar contrato de resposta.
- Testar fluxo de logout/invalidação.

### Performance
- Medir latência da auth (padrão < 500ms em rede estável).
- Validar impacto de reauth automático sob carga.

---

## Rollout e rollout guards

- Deploy inicial: habilitar OAuth por padrão em homolog, manter legacy flag disponível.
- Monitoramento:
  - Taxa de falhas de autenticação (per minute).
  - Uso do fallback legado.
  - Latência média de autenticação.
- Rollout guard: se taxa de falhas > X% em 10 minutos, automático rollback via reversão de feature flag.

---

## Observability

- Em cada auth success/fail enviar métrica com tags: `env`, `service`, `reason`.
- Tracing: suportar propagação de headers de correlação (X-Request-ID).
- Logs: structured JSON logs com masked fields.

---

## Dependências externas

- Confirmação com Sankhya sobre nomes exatos de endpoints e campos de resposta.
- Ambiente de homologação da Sankhya.
- Secret Manager (opcional) para produção.

---

## Plano de implementação (tarefas técnicas)

1. Criar `auth/oauth_client.py` com função `authenticate` e `refresh`.
2. Criar `auth/token_manager.py`.
3. Criar `http/session.py` (SankhyaSession).
4. Adicionar `legacy_client.py` (feature-flagged).
5. Escrever testes unitários e integration mocks.
6. Atualizar docs e exemplos `examples/login_oauth.py`.
7. Realizar deploy em homolog e testes com integradores.
8. Monitorar e realizar rollout.

---

## Critérios de aceitação (técnicos)

- Testes unitários passam (>= 80% core coverage).
- Homolog: autenticação via OAuth executada e tokens utilizados em chamadas autenticadas.
- Monitoramento reporta < 1% auth failures nas 24h após rollout.
- Fallback legado ativável e funciona se necessário.

---

## Open questions (precisa confirmar com Sankhya / Product)
1. Nomes exatos dos campos retornados por `/authenticate` (e.g., `access_token`, `token`, `bearerToken`).
2. Endpoint, método e payload exato para refresh de token (se suportado).
3. Endpoint para revogação logout — existe suporte server-side?
4. Políticas de expiração padrão e possibilidade de refresh token.
5. Quais scopes/permissões são necessárias para as operações do SDK?

---

## Anexos
- PRD original (versão completa) — referência para objetivos de negócio.
- `login1.py` — implementação legada para referência (quando fornecido pelo integrador).
- Links para documentação Sankhya (a confirmar).

---

## Próximos passos recomendados
1. Validar campos de contrato com Sankhya (pegar exemplos reais de resposta).
2. Implementar MVP (OAuthClient + TokenManager + SankhyaSession).
3. Executar testes de integração em homolog com 2 integradores piloto.
4. Planejar data de desativação do legacy (comunicado e transição).

---

**Fim do RFC — RFC-Auth-2026-001 (Draft)**
