# Instalação

Este guia detalha como instalar e configurar o Sankhya SDK Python em seu ambiente de desenvolvimento.

## Requisitos do Sistema

| Requisito | Versão Mínima | Recomendada |
|-----------|---------------|-------------|
| Python | 3.10 | 3.11+ |
| pip | 21.0 | Última |
| Sistema Operacional | Windows/Linux/macOS | - |

## Instalação via pip

### Modo Produção

```bash
# Instalação básica
pip install sankhya-sdk-python

# Com suporte a operações assíncronas
pip install sankhya-sdk-python[async]
```

### Modo Desenvolvimento

Para contribuir ou desenvolver localmente:

```bash
# Clone o repositório
git clone https://github.com/onixbrasil/Sankhya-SDK-python.git
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

## Configuração do Ambiente

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do seu projeto:

```ini
# .env
# Configurações de Conexão Sankhya

# URL base da API (sem barra final)
SANKHYA_BASE_URL=https://api.sankhya.com.br

# Credenciais
SANKHYA_USERNAME=seu_usuario
SANKHYA_PASSWORD=sua_senha

# Ambiente (producao, homologacao, treinamento)
SANKHYA_ENVIRONMENT=producao

# Configurações Opcionais
SANKHYA_TIMEOUT=30
SANKHYA_MAX_RETRIES=3
SANKHYA_LOG_LEVEL=INFO
```

!!! warning "Segurança"
    Nunca versione arquivos `.env` com credenciais reais. Adicione `.env` ao seu `.gitignore`.

### Exemplo de .gitignore

```gitignore
# Arquivos de configuração sensíveis
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

### Configuração Alternativa: Arquivo .key

Para ambientes mais seguros, você pode usar um arquivo de chave encriptado:

```python
from sankhya_sdk import SankhyaContext, SankhyaSettings

settings = SankhyaSettings.from_key_file("caminho/para/credenciais.key")
ctx = SankhyaContext(settings)
```

## Verificação da Instalação

Execute o seguinte script para verificar se a instalação está correta:

```python
#!/usr/bin/env python3
"""Verifica a instalação do Sankhya SDK."""

from sankhya_sdk import __version__
from sankhya_sdk import SankhyaContext, SankhyaSettings
from dotenv import load_dotenv
import os

# Carrega variáveis de ambiente
load_dotenv()

print(f"Sankhya SDK Python v{__version__}")
print("-" * 40)

# Verifica configuração
try:
    settings = SankhyaSettings()
    print(f"✅ URL Base: {settings.base_url}")
    print(f"✅ Usuário: {settings.username}")
    print(f"✅ Ambiente: {settings.environment}")
except Exception as e:
    print(f"❌ Erro na configuração: {e}")
    exit(1)

# Testa conexão
try:
    with SankhyaContext.from_settings() as ctx:
        print(f"✅ Conexão estabelecida!")
        print(f"✅ Código do usuário: {ctx.user_code}")
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
    exit(1)

print("-" * 40)
print("Instalação verificada com sucesso! 🎉")
```

## Estrutura do Projeto Recomendada

```
meu-projeto/
├── .env                    # Configurações (não versionado)
├── .gitignore
├── requirements.txt
├── src/
│   ├── __init__.py
│   └── integracao.py       # Seu código de integração
├── tests/
│   └── test_integracao.py
└── README.md
```

## Dependências

O SDK inclui as seguintes dependências principais:

| Pacote | Versão | Descrição |
|--------|--------|-----------|
| `requests` | ≥2.31.0 | Cliente HTTP |
| `pydantic` | ≥2.5.0 | Validação de dados |
| `pydantic-settings` | ≥2.1.0 | Configurações |
| `python-dotenv` | ≥1.0.0 | Variáveis de ambiente |
| `lxml` | ≥5.0.0 | Processamento XML |

### Dependências Opcionais

| Pacote | Grupo | Descrição |
|--------|-------|-----------|
| `httpx` | async | Cliente HTTP assíncrono |
| `aiofiles` | async | I/O de arquivos assíncrono |
| `pytest` | dev | Framework de testes |
| `mkdocs` | docs | Documentação |

## Solução de Problemas

### Erro: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'sankhya_sdk'
```

**Solução:** Verifique se o ambiente virtual está ativado e o pacote instalado:

```bash
pip list | grep sankhya
```

### Erro: Conexão Recusada

```
ConnectionError: Unable to connect to API
```

**Soluções:**

1. Verifique a URL no `.env`
2. Teste conectividade de rede
3. Verifique se há firewall bloqueando

### Erro: Credenciais Inválidas

```
ServiceRequestInvalidAuthorizationException: Invalid credentials
```

**Soluções:**

1. Verifique usuário e senha
2. Confirme que o usuário tem acesso à API
3. Verifique o ambiente (produção vs homologação)

## Próximos Passos

- [Início Rápido](quick-start.md) - Crie sua primeira integração
- [Autenticação](authentication.md) - Aprofunde-se em autenticação
- [Arquitetura](../core-concepts/architecture.md) - Entenda a estrutura do SDK
