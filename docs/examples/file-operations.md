# Operações com Arquivos

Exemplos de download e upload de arquivos e imagens.

## Download de Arquivo

```python
from sankhya_sdk import SankhyaContext
from dotenv import load_dotenv

load_dotenv()

with SankhyaContext.from_settings() as ctx:
    # Baixa arquivo
    content = ctx.wrapper.get_file("relatorio.pdf")
    
    # Salva localmente
    with open("relatorio.pdf", "wb") as f:
        f.write(content)
    
    print("Arquivo baixado com sucesso!")
```

---

## Download de Imagem

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.transport_entities import Product

with SankhyaContext.from_settings() as ctx:
    # Baixa imagem de produto
    image_data = ctx.wrapper.get_image(
        primary_key={"CODPROD": 100},
        entity_name="Produto"
    )
    
    # Salva imagem
    with open("produto_100.jpg", "wb") as f:
        f.write(image_data)
    
    print("Imagem baixada!")
```

---

## Download em Lote

```python
import os
from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Product

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Busca produtos
    products = crud.find(Product, "ATIVO = 'S'", max_results=50)
    
    # Cria diretório
    os.makedirs("product_images", exist_ok=True)
    
    downloaded = 0
    for product in products:
        try:
            image = ctx.wrapper.get_image(
                {"CODPROD": product.code_product},
                "Produto"
            )
            
            if image:
                path = f"product_images/{product.code_product}.jpg"
                with open(path, "wb") as f:
                    f.write(image)
                downloaded += 1
        except Exception as e:
            print(f"Erro {product.code_product}: {e}")
    
    print(f"Baixadas: {downloaded}/{len(products)} imagens")
```

---

## Upload de Arquivo

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.service_models import ServiceRequest, RequestBody

with SankhyaContext.from_settings() as ctx:
    # Lê arquivo
    with open("documento.pdf", "rb") as f:
        file_content = f.read()
    
    # Prepara requisição de upload
    request = ServiceRequest(
        service_name="FileService.uploadFile",
        request_body=RequestBody(
            filename="documento.pdf",
            content=file_content
        )
    )
    
    response = ctx.wrapper.invoke_service("FileService.uploadFile", request)
    
    if response.is_success:
        print("Arquivo enviado!")
    else:
        print(f"Erro: {response.status_message}")
```

---

## Usando KnowServicesRequestWrapper

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import KnowServicesRequestWrapper

with SankhyaContext.from_settings() as ctx:
    services = KnowServicesRequestWrapper(ctx.wrapper)
    
    # Download de arquivo
    content = services.get_file("relatorio_vendas.pdf")
    
    with open("vendas.pdf", "wb") as f:
        f.write(content)
    
    # Download de imagem
    image = services.get_image(
        primary_key={"CODPARCEIRO": 1},
        entity_name="Parceiro"
    )
    
    with open("parceiro_1.jpg", "wb") as f:
        f.write(image)
```

---

## Tratamento de Erros

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.exceptions import ServiceRequestException

with SankhyaContext.from_settings() as ctx:
    try:
        content = ctx.wrapper.get_file("arquivo_inexistente.pdf")
        
    except ServiceRequestException as e:
        if "not found" in e.status_message.lower():
            print("Arquivo não encontrado")
        else:
            print(f"Erro: {e.status_message}")
    
    except Exception as e:
        print(f"Erro inesperado: {e}")
```

---

## Download Assíncrono

```python
import asyncio
from sankhya_sdk import AsyncSankhyaContext

async def download_file(ctx, filename):
    """Download assíncrono de arquivo."""
    content = await ctx.wrapper.get_file_async(filename)
    return content

async def main():
    async with AsyncSankhyaContext.from_settings() as ctx:
        # Download múltiplos arquivos em paralelo
        filenames = ["rel1.pdf", "rel2.pdf", "rel3.pdf"]
        
        tasks = [download_file(ctx, name) for name in filenames]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for filename, result in zip(filenames, results):
            if isinstance(result, Exception):
                print(f"Erro {filename}: {result}")
            else:
                with open(f"downloads/{filename}", "wb") as f:
                    f.write(result)
                print(f"Baixado: {filename}")

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

import os
from pathlib import Path
from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Product
from sankhya_sdk.exceptions import ServiceRequestException
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductImageDownloader:
    """Baixa imagens de produtos."""
    
    def __init__(self, context, output_dir="product_images"):
        self.context = context
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.downloaded = 0
        self.failed = 0
        self.skipped = 0
    
    def download_all(self, criteria="ATIVO = 'S'", max_products=100):
        """Baixa todas as imagens de produtos."""
        crud = SimpleCRUDRequestWrapper(self.context.wrapper)
        products = crud.find(Product, criteria, max_results=max_products)
        
        logger.info(f"Encontrados {len(products)} produtos")
        
        for i, product in enumerate(products, 1):
            self._download_product_image(product)
            
            if i % 10 == 0:
                logger.info(f"Progresso: {i}/{len(products)}")
        
        return self._summary()
    
    def _download_product_image(self, product):
        """Baixa imagem de um produto."""
        filepath = self.output_dir / f"{product.code_product}.jpg"
        
        # Pula se já existe
        if filepath.exists():
            self.skipped += 1
            return
        
        try:
            image = self.context.wrapper.get_image(
                {"CODPROD": product.code_product},
                "Produto"
            )
            
            if image and len(image) > 100:  # Ignora imagens muito pequenas
                filepath.write_bytes(image)
                self.downloaded += 1
            else:
                self.skipped += 1
                
        except ServiceRequestException as e:
            self.failed += 1
            logger.warning(f"Produto {product.code_product}: {e.status_message}")
        except Exception as e:
            self.failed += 1
            logger.error(f"Produto {product.code_product}: {e}")
    
    def _summary(self):
        """Retorna resumo do download."""
        return {
            "downloaded": self.downloaded,
            "failed": self.failed,
            "skipped": self.skipped,
            "total": self.downloaded + self.failed + self.skipped
        }


def main():
    with SankhyaContext.from_settings() as ctx:
        downloader = ProductImageDownloader(ctx)
        result = downloader.download_all(max_products=50)
        
        logger.info("=== Resumo ===")
        logger.info(f"Baixadas: {result['downloaded']}")
        logger.info(f"Falhas: {result['failed']}")
        logger.info(f"Puladas: {result['skipped']}")
        logger.info(f"Total: {result['total']}")


if __name__ == "__main__":
    main()
```

## Próximos Passos

- [Queries Avançadas](advanced-queries.md) - Filtros complexos
- [Tratamento de Erros](error-handling.md) - Exceções
- [Request Wrappers](../api-reference/request-wrappers.md) - API completa
