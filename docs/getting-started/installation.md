# Instalacao

Este guia detalha como instalar e configurar o Sankhya SDK Python em seu ambiente de desenvolvimento.

## Requisitos do Sistema

| Requisito | Versao Minima | Recomendada |
|-----------|---------------|-------------|
| Python | 3.10 | 3.11+ |
| pip | 21.0 | Ultima |
| Sistema Operacional | Windows/Linux/macOS | - |

## Instalacao via pip

### Modo Producao

```bash
# Instalacao basica
pip install sankhya-sdk-python

# Com suporte a operacoes assincronas
pip install sankhya-sdk-python[async]
```

### Modo Desenvolvimento

Para contribuir ou desenvolver localmente:

```bash
# Clone o repositorio
git clone https://github.com/ssmvictor/Sankhya-SDK-python.git
cd Sankhya-SDK-python

# Crie um ambiente virtual
python -m venv .venv

# Ative o ambiente virtual
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Instale em modo desenvolvimento
pip install -e ".[dev,async,docs]"
```

## Configuracao do Ambiente

### Credenciais OAuth2 (Recomendado)

O SDK utiliza autenticacao **OAuth2** com `client_id` e `client_secret`. Esta e a abordagem recomendada para novas integracoes.

#### 1. Obter Credenciais

Acesse o [Portal do Desenvolvedor Sankhya](https://areadev.sankhya.com.br/):

1. Crie uma **Solucao**
2. Crie um **Componente de Integracao**
3. Copie o **Client ID** e **Client Secret**
4. Obtenha o **X-Token** no Sankhya OM > Configuracoes Gateway > Chave do Cliente

#### 2. Variaveis de Ambiente

Crie um arquivo `.env` na raiz do seu projeto:

```ini
# .env
# Configuracoes OAuth2 Sankhya

# Credenciais OAuth2 (obrigatorias)
SANKHYA_CLIENT_ID=seu_client_id
SANKHYA_CLIENT_SECRET=seu_client_secret

# URL base da API
SANKHYA_AUTH_BASE_URL=https://api.sankhya.com.br

# Token de Integracao (X-Token)
SANKHYA_TOKEN=seu_x_token

# Configuracoes Opcionais
SANKHYA_TIMEOUT=30
SANKHYA_LOG_LEVEL=INFO
```

!!! warning "Seguranca"
    Nunca versione arquivos `.env` com credenciais reais. Adicione `.env` ao seu `.gitignore`.

### Exemplo de .gitignore

```gitignore
# Arquivos de configuracao sensiveis
.env
.env.local
*.key

# Ambiente virtual
.venv/
venv/

# Cache Python
__pycache__/
*.pyc
```

## Verificacao da Instalacao

Execute o seguinte script para verificar se a instalacao esta correta:

```python
#!/usr/bin/env python3
"""Verifica a instalacao do Sankhya SDK."""

import os
from dotenv import load_dotenv

# Carrega variaveis de ambiente
load_dotenv()

# Verifica versao
from sankhya_sdk import __version__
print(f"Sankhya SDK Python v{__version__}")
print("-" * 40)

# Verifica configuracao OAuth2
client_id = os.getenv("SANKHYA_CLIENT_ID")
client_secret = os.getenv("SANKHYA_CLIENT_SECRET")
base_url = os.getenv("SANKHYA_AUTH_BASE_URL", "https://api.sankhya.com.br")
x_token = os.getenv("SANKHYA_TOKEN")

if not client_id or not client_secret:
    print("Erro: SANKHYA_CLIENT_ID e SANKHYA_CLIENT_SECRET sao obrigatorios")
    exit(1)

print(f"Client ID: {client_id[:8]}...")
print(f"Base URL: {base_url}")
print(f"X-Token: {'Configurado' if x_token else 'Nao configurado'}")

# Testa conexao
try:
    from sankhya_sdk.auth import OAuthClient
    from sankhya_sdk.http import SankhyaSession, GatewayClient

    oauth = OAuthClient(base_url=base_url, token=x_token)
    oauth.authenticate(client_id=client_id, client_secret=client_secret)
    
    session = SankhyaSession(oauth_client=oauth, base_url=base_url)
    client = GatewayClient(session)
    
    print("Conexao OAuth2 estabelecida!")
    
    # Teste rapido
    result = client.load_records("Parceiro", ["CODPARC"], criteria="ROWNUM <= 1")
    if GatewayClient.is_success(result):
        print("Consulta de teste OK!")
    
except Exception as e:
    print(f"Erro de conexao: {e}")
    exit(1)

print("-" * 40)
print("Instalacao verificada com sucesso!")
```

## Primeiro Uso: Quick Start

Apos a instalacao, voce pode comecar a usar o SDK:

```python
import os
from dotenv import load_dotenv
from sankhya_sdk.auth import OAuthClient
from sankhya_sdk.http import SankhyaSession, GatewayClient

load_dotenv()

# 1. Autenticar via OAuth2
oauth = OAuthClient(
    base_url=os.getenv("SANKHYA_AUTH_BASE_URL", "https://api.sankhya.com.br"),
    token=os.getenv("SANKHYA_TOKEN")
)
oauth.authenticate(
    client_id=os.getenv("SANKHYA_CLIENT_ID"),
    client_secret=os.getenv("SANKHYA_CLIENT_SECRET")
)

# 2. Criar sessao e cliente
session = SankhyaSession(oauth_client=oauth, base_url=os.getenv("SANKHYA_AUTH_BASE_URL"))
client = GatewayClient(session)

# 3. Consultar dados
result = client.load_records(
    entity="Parceiro",
    fields=["CODPARC", "NOMEPARC", "CGC_CPF"],
    criteria="ATIVO = 'S'"
)

# 4. Processar resultados
records = GatewayClient.extract_records(result)
for r in records[:5]:
    print(f"{r['CODPARC']}: {r['NOMEPARC']}")

# 5. Atualizar registro (UPDATE PARCIAL - novo!)
client.save_record(
    entity="Parceiro",
    fields={"EMAIL": "novo@email.com"},
    pk={"CODPARC": 1}  # Envia apenas campos alterados
)
```

## Estrutura do Projeto Recomendada

```
meu-projeto/
    .env                    # Configuracoes OAuth2 (nao versionado)
    .gitignore
    requirements.txt
    src/
        __init__.py
        integracao.py       # Seu codigo de integracao
    tests/
        test_integracao.py
    README.md
```

## Dependencias

O SDK inclui as seguintes dependencias principais:

| Pacote | Versao | Descricao |
|--------|--------|-----------|
| `requests` | >=2.31.0 | Cliente HTTP |
| `pydantic` | >=2.5.0 | Validacao de dados |
| `pydantic-settings` | >=2.1.0 | Configuracoes |
| `python-dotenv` | >=1.0.0 | Variaveis de ambiente |
| `lxml` | >=5.0.0 | Processamento XML |

### Dependencias Opcionais

| Pacote | Grupo | Descricao |
|--------|-------|-----------|
| `httpx` | async | Cliente HTTP assincrono |
| `aiofiles` | async | I/O de arquivos assincrono |
| `pytest` | dev | Framework de testes |
| `mkdocs` | docs | Documentacao |

## Solucao de Problemas

### Erro: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'sankhya_sdk'
```

**Solucao:** Verifique se o ambiente virtual esta ativado e o pacote instalado:

```bash
pip list | grep sankhya
```

### Erro: AuthError - Invalid Credentials

```
AuthError: Authentication failed
```

**Solucoes:**

1. Verifique `SANKHYA_CLIENT_ID` e `SANKHYA_CLIENT_SECRET`
2. Confirme que o componente esta ativo no Portal do Desenvolvedor
3. Verifique se o `X-Token` esta correto (se exigido)

### Erro: Conexao Recusada

```
ConnectionError: Unable to connect to API
```

**Solucoes:**

1. Verifique a URL no `.env` (`SANKHYA_AUTH_BASE_URL`)
2. Teste conectividade de rede
3. Verifique se ha firewall bloqueando

### Erro: Token Expirado

O SDK renova automaticamente tokens expirados. Se persistir:

```python
# Forcaar renovacao manual
oauth.authenticate(client_id=..., client_secret=...)
```

## Configuracao Legada (Opcional)

Para compatibilidade com integracoes existentes, o SDK ainda suporta autenticacao via usuario/senha:

```ini
# .env (modo legado)
SANKHYA_BASE_URL=https://api.sankhya.com.br
SANKHYA_USERNAME=seu_usuario
SANKHYA_PASSWORD=sua_senha
```

```python
from sankhya_sdk import SankhyaContext

with SankhyaContext.from_settings() as ctx:
    # Usar wrappers legados...
    pass
```

!!! warning "Recomendacao"
    Para novas integracoes, sempre prefira OAuth2 (`OAuthClient` + `SankhyaSession`).

## Proximos Passos

- [Inicio Rapido](quick-start.md) - Crie sua primeira integracao
- [Autenticacao](authentication.md) - Aprofunde-se em autenticacao OAuth2
- [Gateway Client](../api-reference/gateway-client.md) - Referencia completa da API
