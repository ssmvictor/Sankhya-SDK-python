# Operações com Arquivos

Exemplos de download de arquivos do repositório e de imagens de entidades
(API XML legada).

Os downloads retornam um `ServiceFile` (`sankhya_sdk.core.types.ServiceFile`)
com `data` (bytes), `content_type`, `file_extension` e `filename` (do
`Content-Disposition`, quando o servidor o envia).

| Operação | Sessão principal | Sessão por token | `KnowServicesRequestWrapper` |
|----------|------------------|------------------|------------------------------|
| Arquivo pela chave | `wrapper.get_file(key)` / `ctx.get_file(key)` | `SankhyaContext.get_file_with_token(key, token)` | `get_file(key)` |
| Imagem de entidade | `wrapper.get_image("Produto", {"CODPROD": 100})` / `ctx.get_image(...)` | `SankhyaContext.get_image_with_token(entity, keys, token)` | `get_image(Product(code=100))` |

Todas têm versão assíncrona (`*_async`). A chave de um arquivo do
repositório é obtida com `KnowServicesRequestWrapper.open_file(caminho)`.

## Download de Arquivo

```python
from sankhya_sdk import SankhyaContext

# __enter__ retorna o SankhyaWrapper da sessão principal
with SankhyaContext.from_settings() as wrapper:
    # Baixa o arquivo pela chave (chaveArquivo)
    file = wrapper.get_file("CHAVE_DO_ARQUIVO")

    # Salva localmente
    with open(file.filename or f"arquivo.{file.file_extension}", "wb") as f:
        f.write(file.data)

    print(f"Arquivo baixado: {file.content_type}, {len(file.data)} bytes")
```

---

## Download de Imagem

`get_image` recebe o nome da entidade e as chaves primárias, e retorna
`None` se a entidade não tiver imagem (HTTP 404) ou se a requisição falhar:

```python
from sankhya_sdk import SankhyaContext

with SankhyaContext.from_settings() as wrapper:
    # Baixa imagem de produto
    image = wrapper.get_image("Produto", {"CODPROD": 100})

    if image is not None:
        # Salva imagem com a extensão do Content-Type (png, jpg...)
        with open(f"produto_100.{image.file_extension}", "wb") as f:
            f.write(image.data)
        print("Imagem baixada!")
    else:
        print("Produto sem imagem")
```

---

## Download em Lote

```python
import os

from sankhya_sdk import SankhyaContext
from sankhya_sdk.helpers import EntityQueryOptions
from sankhya_sdk.models.transport import Product
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

ctx = SankhyaContext.from_settings()
try:
    SimpleCRUDRequestWrapper.initialize(ctx)

    # Busca produtos ativos (no máximo 50)
    products = SimpleCRUDRequestWrapper.find_all(
        Product(is_active=True), EntityQueryOptions(max_results=50)
    )

    # Cria diretório
    os.makedirs("product_images", exist_ok=True)

    downloaded = 0
    for product in products:
        image = ctx.get_image("Produto", {"CODPROD": product.code})
        if image is not None:
            path = f"product_images/{product.code}.{image.file_extension}"
            with open(path, "wb") as f:
                f.write(image.data)
            downloaded += 1

    print(f"Baixadas: {downloaded}/{len(products)} imagens")
finally:
    SimpleCRUDRequestWrapper.dispose()
    ctx.dispose()
```

---

## Upload de Arquivo

A API XML legada não tem upload de arquivos, nem no SDK .NET. Para o
repositório de arquivos existem apenas `open_file` (obtém a chave),
`get_file` (baixa) e `delete_files` (remove), no
`KnowServicesRequestWrapper`.

---

## Usando KnowServicesRequestWrapper

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.models.transport import Product
from sankhya_sdk.request_wrappers import KnowServicesRequestWrapper

ctx = SankhyaContext.from_settings()
try:
    KnowServicesRequestWrapper.initialize(ctx)

    # Abre o arquivo do repositório e baixa pela chave
    key = KnowServicesRequestWrapper.open_file("/Relatorios/vendas.pdf")
    file = KnowServicesRequestWrapper.get_file(key)

    with open("vendas.pdf", "wb") as f:
        f.write(file.data)

    # Imagem a partir da entidade: nome ("Produto") e chaves (CODPROD)
    # vêm da própria instância
    image = KnowServicesRequestWrapper.get_image(Product(code=100))

    if image is not None:
        with open(f"produto_100.{image.file_extension}", "wb") as f:
            f.write(image.data)
finally:
    KnowServicesRequestWrapper.dispose()
    ctx.dispose()
```

---

## Tratamento de Erros

Quando a chave é inválida ou o arquivo não existe, o servidor responde com
uma página HTML de erro e `get_file` lança
`ServiceRequestFileNotFoundException`:

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.exceptions import ServiceRequestFileNotFoundException

with SankhyaContext.from_settings() as wrapper:
    try:
        file = wrapper.get_file("INEXISTENTE_123")

    except ServiceRequestFileNotFoundException as e:
        print(f"Arquivo não encontrado: {e}")

    except Exception as e:  # ex.: requests.HTTPError (status HTTP de erro)
        print(f"Erro inesperado: {e}")
```

---

## Download Assíncrono

Não existe `AsyncSankhyaContext`: o `SankhyaContext` suporta `async with`, e
os métodos `*_async` do wrapper executam o download numa thread
(`asyncio.to_thread`):

```python
import asyncio
import os

from sankhya_sdk import SankhyaContext, SankhyaWrapper


async def download_file(wrapper: SankhyaWrapper, key: str) -> bytes:
    """Download assíncrono de arquivo."""
    file = await wrapper.get_file_async(key)
    return file.data


async def main() -> None:
    os.makedirs("downloads", exist_ok=True)

    async with SankhyaContext.from_settings() as wrapper:
        # Download de múltiplos arquivos em paralelo
        keys = ["CHAVE_1", "CHAVE_2", "CHAVE_3"]

        tasks = [download_file(wrapper, key) for key in keys]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for key, result in zip(keys, results):
            if isinstance(result, BaseException):
                print(f"Erro {key}: {result}")
            else:
                with open(f"downloads/{key}.pdf", "wb") as f:
                    f.write(result)
                print(f"Baixado: {key}")


asyncio.run(main())
```

---

## Exemplo Completo

```python
#!/usr/bin/env python3
"""
Exemplo completo de operações com arquivos.

Demonstra download em lote com progresso e tratamento de erros.
"""

import logging
from pathlib import Path
from typing import Dict

from sankhya_sdk import SankhyaContext
from sankhya_sdk.helpers import EntityQueryOptions
from sankhya_sdk.models.transport import Product
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductImageDownloader:
    """Baixa imagens de produtos."""

    def __init__(self, context: SankhyaContext, output_dir: str = "product_images"):
        self.context = context
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.downloaded = 0
        self.failed = 0
        self.skipped = 0

    def download_all(self, max_products: int = 100) -> Dict[str, int]:
        """Baixa as imagens dos produtos ativos."""
        products = SimpleCRUDRequestWrapper.find_all(
            Product(is_active=True), EntityQueryOptions(max_results=max_products)
        )

        logger.info(f"Encontrados {len(products)} produtos")

        for i, product in enumerate(products, 1):
            self._download_product_image(product)

            if i % 10 == 0:
                logger.info(f"Progresso: {i}/{len(products)}")

        return self._summary()

    def _download_product_image(self, product: Product) -> None:
        """Baixa imagem de um produto."""
        # Pula se já existe (qualquer extensão)
        if any(self.output_dir.glob(f"{product.code}.*")):
            self.skipped += 1
            return

        try:
            image = self.context.get_image("Produto", {"CODPROD": product.code})

            if image is not None and len(image.data) > 100:  # Ignora imagens muito pequenas
                filepath = self.output_dir / f"{product.code}.{image.file_extension}"
                filepath.write_bytes(image.data)
                self.downloaded += 1
            else:
                self.skipped += 1

        except Exception as e:
            self.failed += 1
            logger.error(f"Produto {product.code}: {e}")

    def _summary(self) -> Dict[str, int]:
        """Retorna resumo do download."""
        return {
            "downloaded": self.downloaded,
            "failed": self.failed,
            "skipped": self.skipped,
            "total": self.downloaded + self.failed + self.skipped,
        }


def main() -> None:
    ctx = SankhyaContext.from_settings()
    try:
        SimpleCRUDRequestWrapper.initialize(ctx)
        downloader = ProductImageDownloader(ctx)
        result = downloader.download_all(max_products=50)

        logger.info("=== Resumo ===")
        logger.info(f"Baixadas: {result['downloaded']}")
        logger.info(f"Falhas: {result['failed']}")
        logger.info(f"Puladas: {result['skipped']}")
        logger.info(f"Total: {result['total']}")
    finally:
        SimpleCRUDRequestWrapper.dispose()
        ctx.dispose()


if __name__ == "__main__":
    main()
```

## Próximos Passos

- [Queries Avançadas](advanced-queries.md) - Filtros complexos
- [Tratamento de Erros](error-handling.md) - Exceções
- [Request Wrappers](../api-reference/request-wrappers.md) - API completa
