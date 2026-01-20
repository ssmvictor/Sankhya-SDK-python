# Sankhya SDK Python

SDK Python para API Sankhya (ERP).

![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)

## Sobre o Projeto

Este SDK oferece uma interface robusta e tipada para integração com o ERP Sankhya.

Embora o projeto tenha referências no [Sankhya-SDK-dotnet](https://github.com/guibranco/Sankhya-SDK-dotnet), ele evoluiu independentemente para aproveitar os recursos modernos do Python, trazendo diversas melhorias arquiteturais, suporte nativo a assincronismo e validações robustas.

## 📚 Documentação

A documentação completa, incluindo detalhes técnicos, configurações avançadas e referência da API, está disponível em:

👉 **[https://datavi.ia.br/docs-site-sdk/](https://datavi.ia.br/docs-site-sdk/)**

Você também pode consultar a documentação local na pasta [`docs/`](docs/) e exemplos práticos em [`examples/`](examples/).

## Instalação

```bash
pip install -e ".[dev]"
```

## Exemplo Rápido

```python
from sankhya_sdk.auth import OAuthClient
from sankhya_sdk.http import SankhyaSession

# 1. Autenticação
oauth = OAuthClient(base_url="https://api.sankhya.com.br")
oauth.authenticate(client_id="SEU_ID", client_secret="SEU_SECRET")

# 2. Uso da Sessão
with SankhyaSession(oauth_client=oauth) as session:
    # O token é gerenciado e renovado automaticamente
    response = session.get("/gateway/v1/mge/teste")
    print(response)
```

## Principais Recursos

*   **Autenticação Inteligente**: OAuth2 com renovação automática de tokens (thread-safe).
*   **Tipagem e Validação**: DTOs baseados em Pydantic.
*   **Flexibilidade**: Suporte a JSON Gateway e XML.
*   **Alta Performance**: Preparado para operações assíncronas.

## Licença

Este projeto está licenciado sob a mesma licença do projeto original. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
