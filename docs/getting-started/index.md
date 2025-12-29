# Início Rápido

Bem-vindo à seção de início rápido do Sankhya SDK Python! Aqui você encontrará tudo o que precisa para começar a usar o SDK.

## Primeiros Passos

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } __Instalação__

    ---

    Configure o SDK em seu ambiente de desenvolvimento em minutos.

    [:octicons-arrow-right-24: Instalação](installation.md)

-   :material-rocket-launch:{ .lg .middle } __Início Rápido__

    ---

    Crie sua primeira integração com a API Sankhya em poucos passos.

    [:octicons-arrow-right-24: Início Rápido](quick-start.md)

-   :material-shield-key:{ .lg .middle } __Autenticação__

    ---

    Gerencie credenciais e sessões de forma segura.

    [:octicons-arrow-right-24: Autenticação](authentication.md)

</div>

## Pré-requisitos

Antes de começar, certifique-se de ter:

- **Python 3.10+** instalado
- Acesso a uma instância Sankhya (produção ou homologação)
- Credenciais válidas (usuário e senha)

## Exemplo Mínimo

```python
from sankhya_sdk import SankhyaContext

# Conecta usando variáveis de ambiente
with SankhyaContext.from_settings() as ctx:
    print(f"Conectado como: {ctx.user_code}")
```

## Próximos Passos

Após configurar o SDK, explore as seções de **Conceitos Fundamentais** e **Exemplos** para aprofundar seu conhecimento.
