# Sankhya SDK Python

Biblioteca Python para integração com a API Sankhya, oferecendo uma interface moderna e intuitiva para operações CRUD, gerenciamento de sessões e serviços específicos.

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } __Início Rápido__

    ---

    Configure o SDK e crie sua primeira integração em minutos.

    [:octicons-arrow-right-24: Começar](getting-started/index.md)

-   :material-book-open-variant:{ .lg .middle } __Conceitos Fundamentais__

    ---

    Entenda a arquitetura, sessões e sistema de entidades.

    [:octicons-arrow-right-24: Conceitos](core-concepts/index.md)

-   :material-code-tags:{ .lg .middle } __Referência da API__

    ---

    Documentação completa de classes, métodos e tipos.

    [:octicons-arrow-right-24: API Reference](api-reference/index.md)

-   :material-file-document-multiple:{ .lg .middle } __Exemplos__

    ---

    Exemplos práticos para casos de uso comuns.

    [:octicons-arrow-right-24: Exemplos](examples/index.md)

</div>

## Instalação

```bash
pip install sankhya-sdk-python
```

## Exemplo Rápido

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Partner
from dotenv import load_dotenv

load_dotenv()

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    partners = crud.find(Partner, "ATIVO = 'S'", max_results=10)
    
    for partner in partners:
        print(f"{partner.code_partner}: {partner.name}")
```

## Recursos Principais

| Recurso | Descrição |
|---------|-----------|
| **Operações CRUD** | Find, Insert, Update, Remove com entidades tipadas |
| **Paginação** | Consultas paginadas para grandes volumes de dados |
| **Sessões** | Gerenciamento de múltiplas sessões e multi-threading |
| **Async/Await** | Suporte completo a operações assíncronas |
| **Serviços Específicos** | NF-e, faturamento, arquivos e imagens |
| **Validações** | Sistema de validação de entidades |

## Compatibilidade

- **Python**: 3.10+
- **Sankhya API**: Todas as versões suportadas
- **Sistemas**: Windows, Linux, macOS

## Licença

Este projeto está licenciado sob a MIT License.
