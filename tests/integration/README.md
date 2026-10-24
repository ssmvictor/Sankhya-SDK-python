# Integration Tests - Sankhya SDK Python

Este diretório contém os testes de integração para o Sankhya SDK Python.

Os testes exercitam a API real do SDK (`SankhyaWrapper`, `SankhyaContext` e os
request wrappers) com o transporte HTTP simulado: `requests.Session` é
substituído por um servidor falso que responde no protocolo XML do Sankhya.
O comportamento esperado segue o SDK .NET de referência.

## Estrutura

```
tests/integration/
├── conftest.py                           # Servidor simulado, helpers e fixtures
├── test_authentication_flow.py           # Testes de autenticação
├── test_simple_crud_integration.py       # Testes de CRUD simples
├── test_end_to_end_workflows.py          # Testes de workflows completos
├── test_validation_integration.py        # Testes de validação
├── test_error_handling_integration.py    # Testes de tratamento de erros e retry
├── test_concurrency_integration.py       # Testes de concorrência
├── test_know_services_integration.py     # Testes de serviços conhecidos
├── test_on_demand_request_integration.py # Testes de processamento on-demand
├── test_paged_request_complete.py        # Testes de paginação (simulados)
├── test_paged_request_integration.py     # Testes de paginação (API real)
├── test_wrapper_integration.py           # Testes do wrapper principal
├── test_xml_serialization.py             # Serialização de requests/responses
├── test_transport_xml_serialization.py   # Serialização de entidades de transporte
├── test_complex_entities_xml.py          # XML de entidades complexas
└── README.md                             # Este arquivo
```

## Executando os Testes

### Executar todos os testes de integração

```bash
pytest tests/integration/ -v
```

### Executar com marcadores específicos

```bash
# Apenas testes de integração
pytest -m integration

# Excluir testes lentos
pytest tests/integration/ -v -m "not slow"

# Apenas testes assíncronos
pytest tests/integration/ -v -m asyncio
```

### Executar arquivo específico

```bash
pytest tests/integration/test_authentication_flow.py -v
```

### Executar com cobertura

```bash
pytest tests/integration/ --cov=sankhya_sdk --cov-report=html
```

### Testes contra um servidor real

Alguns testes só rodam com um servidor Sankhya de verdade e são ignorados
por padrão:

| Arquivo | Como habilitar |
|---------|----------------|
| `test_paged_request_integration.py` | Definir `SANKHYA_URL`, `SANKHYA_USERNAME`, `SANKHYA_PASSWORD` e, se diferente de 8180, `SANKHYA_PORT` (as mesmas variáveis de `SankhyaSettings`, ver `.env.example`) |
| `test_wrapper_integration.py` (`TestWrapperIntegration`) | `SANKHYA_SKIP_INTEGRATION=false` e as variáveis acima |

## Marcadores Disponíveis

| Marcador | Descrição |
|----------|-----------|
| `integration` | Todos os testes de integração |
| `slow` | Testes que podem demorar mais |
| `requires_api` | Testes que requerem API real |
| `asyncio` | Testes assíncronos |

## Servidor Simulado

### Sequência de autenticação

`SankhyaWrapper.authenticate()` faz **duas** requisições HTTP:

1. o login (`MobileLoginSP.login`);
2. o registro de user agent via DWR (`/mge/dwr/exec/DWRController.execute.dwr`).

Além disso, `SimpleCRUDRequestWrapper.initialize(context)` adquire uma
**sessão dedicada** (novo login + DWR), como
`Context.AcquireNewSession(ServiceRequestType.SimpleCrud)` no .NET, e o
`dispose()` faz o logout das duas sessões. Filas fixas de respostas
(`side_effect = [login, resposta, logout]`) quebram com essas requisições
extras; por isso os testes de wrappers usam o `FakeSankhyaServer`.

### `FakeSankhyaServer`

Instalado como `side_effect` de `requests.Session.request`, roteia cada
chamada pelo parâmetro `serviceName` da URL:

- login, logout e DWR respondem sempre com sucesso (cada login gera um
  JSESSIONID único) e são contados em `server.logins` / `server.logouts`;
- as demais chamadas de serviço consomem, em ordem, a fila de respostas;
  uma chamada além da fila falha com `AssertionError`;
- cada item da fila pode ser uma resposta HTTP, uma exceção (falha de
  transporte) ou uma função que recebe o corpo XML da requisição e devolve
  a resposta (útil em testes concorrentes, para responder de acordo com o
  que foi pedido e detectar respostas trocadas entre threads);
- o serviço e o corpo XML de cada chamada ficam registrados:
  `server.calls`, `server.calls_to(service)`, `server.bodies(service)`.

### Helpers de requisição/resposta

| Helper | Uso |
|--------|-----|
| `http_response(status_code, content)` | `requests.Response` real (`raise_for_status` lança em 4xx/5xx) |
| `entities_response(*rows, service=...)` | XML do CRUDServiceProvider com as entidades informadas |
| `create_success_response(entities, total_records)` | XML de sucesso com `<entities>` |
| `create_error_response(error_code, message)` | XML de erro (`status="0"` e `statusMessage`) |
| `create_login_response(session_id, user_code)` | XML de login |
| `create_logout_response()` | XML de logout |
| `create_authentication_responses()` | Respostas do login e do DWR, para filas fixas |
| `create_sessions_response(sessions)` | `<SESSIONS><SESSION ID USERID USERNAME HOST/></SESSIONS>` |
| `create_file_response(data, content_type, filename)` | Download de arquivo |
| `request_xml(body)` | Interpreta o corpo XML enviado |
| `find_criteria(body)` | Expressão em `dataSet/criteria` do loadRecords |
| `save_data_row(body)` | `(key, localFields)` do `dataRow` do saveRecord |

### `simple_crud_session()`

Context manager que autentica um `SankhyaWrapper`, cria o `SankhyaContext`,
inicializa o `SimpleCRUDRequestWrapper` e libera tudo ao final, inclusive se
a inicialização falhar.

### Isolamento entre testes

`SankhyaContext` guarda os wrappers de todas as sessões num dicionário de
classe, e o `__del__` de um contexto não descartado finaliza todas as sessões
registradas. A fixture autouse `_isolate_shared_sdk_state` suspende a coleta
automática do GC durante cada teste (um contexto vazado por outro teste não é
finalizado no meio dele), coleta a geração jovem ao final e libera os
wrappers estáticos (`SimpleCRUDRequestWrapper`, `KnowServicesRequestWrapper`).

## Exemplos

### Teste de autenticação (fila fixa)

```python
@patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
def test_successful_authentication(self, mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    # Login + registro de user agent (DWR) + logout no dispose
    mock_session.request.side_effect = [
        *create_authentication_responses("SESSION123", 1),
        create_mock_response(200, create_logout_response()),
    ]
    
    wrapper = SankhyaWrapper(host="http://test.local", port=8180)
    wrapper.authenticate("user", "pass")
    try:
        assert wrapper.session_id == "SESSION123"
    finally:
        wrapper.dispose()
```

### Teste de CRUD

Não existe `create()`: criação e atualização usam
`SimpleCRUDRequestWrapper.update`, que invoca `CRUDServiceProvider.saveRecord`
(sem chave primária o servidor cria o registro), como no .NET.

```python
@patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
def test_create_partner(self, mock_session_class):
    server = FakeSankhyaServer([
        http_response(200, create_success_response([
            {"CODPARC": "100", "NOMEPARC": "Novo Parceiro"}
        ])),
    ])
    mock_session_class.return_value.request.side_effect = server
    
    with simple_crud_session():
        result = SimpleCRUDRequestWrapper.update(Partner(name="Novo Parceiro"))
    
    assert result.code == 100
    assert result.name == "Novo Parceiro"
    
    # XML enviado (ServiceRequestExtensions.HandleService no .NET)
    (body,) = server.bodies(ServiceName.CRUD_SERVICE_SAVE)
    assert save_data_row(body) == ({}, {"NOMEPARC": "Novo Parceiro"})
```

Sem o helper, o padrão equivalente é:

```python
wrapper = SankhyaWrapper(host="http://test.local", port=8180)
wrapper.authenticate("user", "pass")
context = SankhyaContext(wrapper)
try:
    SimpleCRUDRequestWrapper.initialize(context)
    ...
finally:
    SimpleCRUDRequestWrapper.dispose()
    context.dispose()
```

### Teste de erro

```python
@patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
def test_handle_duplicate_key_error(self, mock_session_class):
    server = FakeSankhyaServer([
        http_response(200, create_error_response("DUPLICATE_KEY", "Chave duplicada")),
    ])
    mock_session_class.return_value.request.side_effect = server
    
    with simple_crud_session():
        with pytest.raises(SankhyaException):
            SimpleCRUDRequestWrapper.update(Partner(code=1, name="Duplicado"))
    
    # Erro sem tratamento específico não é retentado
    assert server.calls_to(ServiceName.CRUD_SERVICE_SAVE) == 1
```

### Teste com retry

Atrasos de retry chamam `time.sleep` em `sankhya_sdk.core.wrapper`; os testes
devem substituí-lo (sem espera real) e, quando relevante, verificar o atraso
solicitado:

```python
@patch("sankhya_sdk.core.wrapper.time.sleep")
@patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
def test_deadlock_retry(self, mock_session_class, mock_sleep):
    ...
    assert mock_sleep.call_args_list == [call(RequestRetryDelay.STABLE)]
```

## Boas Práticas

1. **Sempre usar o transporte simulado**: os testes de integração não acessam a rede; isso garante determinismo e velocidade.

2. **Cleanup explícito**: sempre liberar wrappers e contextos (`dispose()`), preferencialmente em `finally` ou via context manager, cobrindo também a inicialização.

3. **Verificar o que foi enviado**: além do resultado, conferir o XML da requisição (`server.bodies`) e a sequência de serviços (`server.calls`).

4. **Sem esperas fixas**: nada de `time.sleep` para "dar tempo" a threads; usar sincronização (eventos, `join`, espera por condição) e substituir os atrasos de retry por mocks.

5. **Isolar testes**: cada teste deve ser independente, inicializando e limpando seus próprios recursos.

6. **Marcar testes corretamente**: usar marcadores apropriados (`@pytest.mark.integration`, `@pytest.mark.slow`, etc.).

## Contribuindo

Ao adicionar novos testes:

1. Seguir o padrão de nomenclatura: `test_<funcionalidade>_<cenário>.py`
2. Usar os helpers de `conftest.py` para simular o servidor
3. Adicionar marcadores apropriados
4. Documentar cenários complexos nos docstrings
5. Garantir cleanup adequado de recursos
