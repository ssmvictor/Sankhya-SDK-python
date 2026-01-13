# PRD — Migração de Autenticação Sankhya  
## De Login Legado (user/senha + appkey + token) para OAuth2 (JSON) — VERSÃO COMPLETA

**Última atualização:** 2026-01-12

---

## Sumário Executivo

Este documento descreve o Product Requirement Document (PRD) para a **migração da camada de autenticação** do SDK/integração com a Sankhya — saindo do modelo **legado (username + password + appkey + token, com payloads XML)** para o **modelo OAuth2 (JSON)** que retorna um `access_token` (Bearer Token). O foco é exclusivamente a **autenticação**: fluxo de login, armazenamento/renovação de token, logout, e comportamento esperado do client SDK.

---

## 1. Contexto

O ecossistema atual utiliza um fluxo legado de autenticação baseado em credenciais de usuário e appkey/token, trocando informações frequentemente em XML. A Sankhya vem disponibilizando endpoints modernos baseados em OAuth2 com payloads JSON e `bearerToken` como padrão recomendado. A migração aumenta segurança, padroniza integrações e reduz risco operacional devido à descontinuação planejada do fluxo legado.

**Nota:** Este PRD assume que a API Sankhya suporta `/authenticate` (OAuth2) retornando um access_token utilizável no header `Authorization: Bearer <token>`. O legacy `/login` será suportado apenas como fallback temporário (quando estritamente necessário) até o encerramento do suporte.

---

## 2. Objetivo

Migrar a autenticação do ambiente/integrador para:

- REMOVER dependência do login legado (XML + user/pass + appkey + token) como fluxo principal.
- IMPLEMENTAR OAuth2 via `/authenticate` com payloads JSON.
- USAR `Authorization: Bearer <access_token>` em todas as requisições autenticadas.
- GERENCIAR ciclo de vida do token (armazenamento seguro, renovação automática quando aplicável, logout).
- PROVIDENCIAR fallback controlado para o fluxo legado (feature-flag / ambiente) enquanto ainda for necessário.

---

## 3. Métricas e Critérios de Sucesso (OKRs / KRs)

- KR1: 100% das chamadas de autenticação em ambientes homologação e produção usam OAuth2 até final do rollout.
- KR2: SDK autentica com OAuth2 em _>= 95%_ dos cenários de integração automatizados (testes).
- KR3: Conversão de autenticação implementada sem expor credenciais em logs nem repositórios.
- KR4: Documentação e exemplos (README + examples) entregues e validados por 2 integradores.
- KR5: Testes unitários e integration (mock) cobrindo cenários de token expirado, token inválido e reautenticação.

---

## 4. Stakeholders

- Product Owner / Dono do projeto
- Equipe de Desenvolvimento (SDK integrador)
- DevOps / Segurança (manuseio de segredos)
- Time de Integração com Sankhya (revisão de compatibilidade)
- Usuários finais / Integradores (consumidores do SDK)

---

## 5. Escopo

### 5.1 In-Scope (o que será entregue nesta entrega)
- Implementação do cliente OAuth2 (`oauth_client.py`) que chama `/authenticate`.
- Gerenciamento de token (armazenamento em memória / arquivo criptografado opcional / integração com secret manager).
- `SankhyaSession` para injetar header `Authorization: Bearer <token>` em todas as requisições.
- Fluxo de logout que invalida token no servidor (quando suportado) e limpa armazenamento local.
- Mecanismo de refresh automático (se o endpoint fornecer `refresh_token`) ou re-login automático com credenciais guardadas de forma segura.
- Fallback controlado para login legado (`login_legacy`) via feature flag ou configuração de ambiente.
- Documentação completa (README, MIGRATION.md, exemplos).
- Testes: unitários + integration (mock).
- Warnings/telemetria quando o fallback legado for usado.

### 5.2 Out-of-Scope (não será tratado agora)
- Refatoração completa de endpoints do negócio para JSON (exceto o necessário para autenticação).
- Conversão automática e completa de payloads XML não relacionados à autenticação.
- Interface gráfica ou CLI completa.
- Suporte a múltiplos provedores OAuth além da Sankhya.

---

## 6. Requisitos Funcionais (RF)

**RF-01 — Login OAuth2 (Essencial)**  
- O sistema deve enviar um `POST /authenticate` com payload JSON contendo `client_id` e `client_secret` (ou outro esquema conforme a especificação da Sankhya) e receber um `access_token` no corpo da resposta.  
- O cliente deve validar o status HTTP e tratar erros (401, 400, 500) de forma padronizada.

**RF-02 — Armazenamento Seguro do Token**  
- O token deve ser mantido em memória por padrão e opcionalmente persistido em storage local seguro (arquivo criptografado) ou secret manager configurável.

**RF-03 — Injeção automática do Header**  
- As requisições subsequentes devem incluir `Authorization: Bearer <access_token>` e `Content-Type: application/json` quando apropriado.

**RF-04 — Renovação / Refresh**  
- Se o servidor retornar `refresh_token` e informações de expiração, o client deve implementar renovação automática sem intervenção do usuário.  
- Se não houver `refresh_token`, o client deve re-executar o fluxo de autenticação (se credenciais estiverem disponíveis) antes de retornar erro ao chamador.

**RF-05 — Logout**  
- Implementar `logout()` que invalida o token no servidor (quando suportado) e limpa qualquer armazenamento local do token.

**RF-06 — Fallback Legado (condicional)**  
- `login_legacy(username, password, appkey, token)` deve continuar disponível apenas por configuração e **emitir warning de depreciação** quando usado.  
- O fallback deve mapear o resultado para o mesmo formato de sessão/token do OAuth para que o resto do SDK use a mesma interface.

**RF-07 — Erros e Logs**  
- Não logar credenciais nem tokens.  
- Expor exceções tipadas: `AuthError`, `TokenExpiredError`, `AuthNetworkError`.

---

## 7. Requisitos Não-Funcionais (NFR)

- Compatibilidade com Python 3.9+.
- Dependências mínimas (preferir `requests`, `pydantic` apenas se necessário).
- Timeouts configuráveis (default 10s para auth).
- Retry em erros transitórios (com backoff exponencial).
- Logs estruturados (logger do módulo) com nível configurável.
- Documentação (em Markdown) e exemplos de uso.
- Segurança: seguir boas práticas para manuseio de segredos (variáveis de ambiente, não commitar segredos).

---

## 8. Arquitetura e Componentes

```
sankhya_sdk/
├── auth/
│   ├── oauth_client.py        # Implementa /authenticate
│   ├── legacy_client.py       # Opcional: encapsula /login legado
│   ├── token_manager.py       # Armazenamento & renovação
│   └── exceptions.py
├── http/
│   └── session.py             # SankhyaSession -> injeta Authorization
├── examples/
│   ├── login_oauth.py
│   └── login_legacy_example.py
├── docs/
│   └── MIGRATION.md
└── tests/
    ├── test_auth.py
    └── test_token_manager.py
```

### Responsabilidades principais
- **oauth_client.py**: encapsula chamadas ao endpoint `/authenticate`, parse do response, mapeamento de erro.
- **token_manager.py**: guarda token, verifica validade, aciona refresh/reauth.
- **session.py**: wrapper HTTP para inserir headers, tratar parsing JSON, retries.
- **legacy_client.py**: chama `/login` e adapta resposta para o modelo de token do token_manager (apenas se feature flag ativa).

---

## 9. Fluxos (Exemplos)

### 9.1 Login OAuth (fluxo básico)
1. `POST /authenticate` com JSON: `{"client_id":"...", "client_secret":"..."}`
2. Resposta: `{"access_token":"...","expires_in":3600,"refresh_token":"..."}`
3. Token armazenado no `token_manager`.
4. Futuras requisições enviam `Authorization: Bearer <access_token>`.

### 9.2 Token expirado com refresh_token
1. Token expira em uma requisição.
2. `token_manager` usa `refresh_token` para `POST /token/refresh` (ou endpoint documentado).
3. Se renovação OK, atualiza `access_token` e reexecuta a requisição.
4. Se renovação falhar, tenta login automático (se credenciais disponíveis) ou lança `TokenExpiredError`.

### 9.3 Fallback legado (feature-flag)
1. Configuração `USE_LEGACY_LOGIN=true` (somente homolog/test).
2. SDK chama `/login` com XML (ou adaptado em JSON conforme disponibilidade).
3. Resultado convertido para formato `access_token` interno.
4. Emitir warning de depreciação no log.

---

## 10. Exemplo de Código (Pseudo / Referência)

**Login OAuth (exemplo de uso)**
```python
from sankhya_sdk.auth.oauth_client import OAuthClient

oauth = OAuthClient(base_url="https://api.sankhya.com.br")
token = oauth.authenticate(client_id="MY_CLIENT_ID", client_secret="MY_SECRET")
# token: {access_token: "...", expires_in: 3600, refresh_token: "..."}

from sankhya_sdk.http.session import SankhyaSession
session = SankhyaSession(token_manager=oauth.token_manager)
resp = session.get("/gateway/v1/entities/cliente/123")
```

**Fallback legado (usado somente se habilitado)**
```python
from sankhya_sdk.auth.legacy_client import LegacyClient
legacy = LegacyClient(base_url="https://api.sankhya.com.br")
session_token = legacy.login(username="user", password="pw", appkey="abc", token="xyz")
# session_token adaptado para o token_manager
```

---

## 11. Testes e Critérios de Aceitação

### Testes Unitários
- `test_oauth_authenticate_success`
- `test_oauth_authenticate_error_handling`
- `test_token_renewal_with_refresh_token`
- `test_token_expiry_path_without_refresh`

### Testes de Integração (mock)
- Simular `/authenticate` retornando 200, 401, 500.
- Simular renovação de token e falha na renovação.

### Critérios de Aceitação
- SDK consegue autenticar via OAuth e realizar ao menos 5 chamadas autenticadas em sequência (mocked/integration).
- Token é renovado automaticamente quando possível.
- Fallback legado só funciona quando explicitamente habilitado e emite warning.
- Nenhum segredo/credencial presente em logs durante execução dos testes.

---

## 12. Migração e Rollout

### Estratégia de Rollout
1. Desenvolver em branch isolada `feature/oauth-auth`.
2. Testes unitários e integração com mock.
3. Deploy em ambiente de homologação.
4. Validar com 2-3 integradores reais (smoke tests).
5. Habilitar em produção como padrão (feature OFF para legacy).
6. Desativar código legado parcialmente e manter por curto período para rollback.

### Migração de Configuração
- Novas variáveis de ambiente:
  - `SANKHYA_CLIENT_ID`
  - `SANKHYA_CLIENT_SECRET`
  - `SANKHYA_AUTH_BASE_URL` (opcional)
  - `SANKHYA_USE_LEGACY_LOGIN` (boolean)

---

## 13. Segurança e Compliance

- **Mascarar logs**: Tokens e secrets nunca devem aparecer em logs.
- **Vault/Secret Manager**: Recomendar uso de secret manager (HashiCorp Vault, AWS Secrets Manager, etc.)
- **Rotação de credenciais**: Implementar processos para rotacionar `client_secret`.
- **Mínimos privilégios**: Aplicar princípio do menor privilégio nas credenciais.
- **Auditoria**: Registrar eventos de autenticação (success/fail) sem incluir segredos.

---

## 14. Dependências Externas

- Documentação oficial da Sankhya sobre `/authenticate` e possíveis endpoints de refresh.
- Ambiente de homologação da Sankhya para testes end-to-end.
- Secret manager opcional (infraestrutura).

---

## 15. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---:|---:|---|
| Endpoint OAuth diferente do esperado | Médio | Alto | Ter fallback controlado; coordenar com Sankhya para especificação exata |
| Falta de refresh_token | Alto | Médio | Implementar reauth automática usando credenciais em storage seguro |
| Ambientes que ainda exigem XML | Médio | Médio | Manter legacy_client e adaptador (feature-flag) |
| Vazamento de tokens em logs | Baixo | Alto | Políticas de logging e masking; revisão de código |

---

## 16. Deliverables

- Código:
  - `oauth_client.py`, `token_manager.py`, `session.py`, `legacy_client.py` (opcional)
- Documentação:
  - `MIGRATION.md`, `README.md` com exemplos, `PRD` (este arquivo)
- Testes:
  - Unitários e integration (mocks)
- Scripts de exemplo:
  - `examples/login_oauth.py`, `examples/login_legacy_example.py`

---

## 17. Cronograma sugerido (estimativo, sem datas fixas)

- Sprint 0 — Análise e design (2 dias)
- Sprint 1 — Implementação oauth_client + token_manager (5 dias)
- Sprint 2 — Session wrapper + exemplos (3 dias)
- Sprint 3 — Testes e docs (3 dias)
- Sprint 4 — Homologação e rollout (2-5 dias)

---

## 18. Observações finais

- O PRD tem foco único na autenticação — outras migrações (XML → JSON em payloads de negócio) devem ser tratadas em PRDs subsequentes.  
- Recomendado alinhamento com o time Sankhya para obter contrato de API final e confirmar propriedades de resposta (nomes de campos, rotas de refresh, políticas de expiração).

---

## 19. Appendices / Referências

- Arquivo local de referência (ex: `login1.py`) usado para validar fluxo legado (se presente no repositório do usuário).  
- Documentação Sankhya (consultar /authenticate e endpoints relacionados).

---

**Fim do PRD — Migração de Autenticação (Versão Completa)**  
