# Integration Tests - Sankhya SDK Python

Este diretório contém os testes de integração para o Sankhya SDK Python.

## Estrutura

```
tests/integration/
├── conftest.py                          # Fixtures e helpers compartilhados
├── test_authentication_flow.py          # Testes de autenticação
├── test_simple_crud_integration.py      # Testes de CRUD simples
├── test_paged_request_complete.py       # Testes de paginação
├── test_on_demand_request_integration.py# Testes de processamento on-demand
├── test_know_services_integration.py    # Testes de serviços conhecidos
├── test_end_to_end_workflows.py         # Testes de workflows completos
├── test_error_handling_integration.py   # Testes de tratamento de erros
├── test_validation_integration.py       # Testes de validação
├── test_concurrency_integration.py      # Testes de concorrência
├── test_wrapper_integration.py          # Testes do wrapper principal
└── README.md                            # Este arquivo
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

## Marcadores Disponíveis

| Marcador | Descrição |
|----------|-----------|
| `integration` | Todos os testes de integração |
| `slow` | Testes que podem demorar mais |
| `requires_api` | Testes que requerem API real |
| `asyncio` | Testes assíncronos |

## Fixtures Principais

### `mock_session`
Mock do `requests.Session` para simular respostas HTTP.

### `authenticated_wrapper`
Wrapper autenticado pronto para uso.

### `sample_partner`
Instância de exemplo de `Partner`.

### `sample_product`
Instância de exemplo de `Product`.

### `sample_xml_responses`
Dicionário com respostas XML pré-configuradas.

## Helpers de Mock

### `create_mock_response(status_code, xml_content, headers)`
Cria um mock de resposta HTTP.

### `create_success_response(entities, total_records)`
Cria resposta XML de sucesso.

### `create_error_response(error_code, message)`
Cria resposta XML de erro.

### `create_login_response(session_id, user_code)`
Cria resposta XML de login.

### `create_logout_response()`
Cria resposta XML de logout.

### `create_paged_response(entities, page, total_records)`
Cria resposta XML paginada.

### `create_sessions_response(sessions)`
Cria resposta XML com lista de sessões.

### `create_file_response(data, content_type, filename)`
Cria resposta de download de arquivo.

## Exemplos

### Teste de autenticação

```python
@patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
def test_successful_authentication(self, mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    login_resp = create_mock_response(200, create_login_response())
    mock_session.request.side_effect = [login_resp]
    
    wrapper = SankhyaWrapper(host="http://test.local", port=8180)
    wrapper.authenticate("user", "pass")
    
    assert wrapper.session_id is not None
```

### Teste de CRUD

```python
@patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
def test_create_partner(self, mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    login_resp = create_mock_response(200, create_login_response())
    create_resp = create_mock_response(
        200, create_success_response([
            {"CODPARC": "100", "NOMEPARC": "Novo Parceiro"}
        ])
    )
    logout_resp = create_mock_response(200, create_logout_response())
    
    mock_session.request.side_effect = [login_resp, create_resp, logout_resp]
    
    wrapper = SankhyaWrapper(host="http://test.local", port=8180)
    wrapper.authenticate("user", "pass")
    
    SimpleCRUDRequestWrapper.initialize(wrapper)
    
    try:
        partner = Partner(name="Novo Parceiro")
        result = SimpleCRUDRequestWrapper.create(partner)
        
        assert result.code == 100
        assert result.name == "Novo Parceiro"
    finally:
        SimpleCRUDRequestWrapper.dispose()
        wrapper.dispose()
```

### Teste de erro

```python
@patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
def test_handle_duplicate_key_error(self, mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    login_resp = create_mock_response(200, create_login_response())
    error_resp = create_mock_response(
        200, create_error_response("DUPLICATE_KEY", "Chave duplicada")
    )
    logout_resp = create_mock_response(200, create_logout_response())
    
    mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
    
    wrapper = SankhyaWrapper(host="http://test.local", port=8180)
    wrapper.authenticate("user", "pass")
    
    SimpleCRUDRequestWrapper.initialize(wrapper)
    
    try:
        with pytest.raises(SankhyaException):
            SimpleCRUDRequestWrapper.create(Partner(code=1, name="Duplicado"))
    finally:
        SimpleCRUDRequestWrapper.dispose()
        wrapper.dispose()
```

## Boas Práticas

1. **Sempre usar mocks**: Os testes de integração usam mocks para garantir determinismo e velocidade.

2. **Cleanup explícito**: Sempre chamar `dispose()` nos wrappers, preferencialmente em bloco `finally`.

3. **Verificar chamadas de rede**: Usar `mock_session.request.call_count` para verificar quantas requisições foram feitas.

4. **Isolar testes**: Cada teste deve ser independente, inicializando e limpando seus próprios recursos.

5. **Marcar testes corretamente**: Usar marcadores apropriados (`@pytest.mark.integration`, `@pytest.mark.slow`, etc.).

## Contribuindo

Ao adicionar novos testes:

1. Seguir o padrão de nomenclatura: `test_<funcionalidade>_<cenário>.py`
2. Usar os helpers de `conftest.py` para criar mocks
3. Adicionar marcadores apropriados
4. Documentar cenários complexos nos docstrings
5. Garantir cleanup adequado de recursos
