from pathlib import Path
from typing import Optional
import mimetypes
from pydantic import BaseModel, Field, field_validator


class ServiceFile(BaseModel):
    """Representa um arquivo usado em um serviço Sankhya."""

    content_type: str = Field(..., description="Tipo MIME do arquivo")
    file_name: str = Field(..., description="Nome do arquivo")
    file_extension: str = Field(..., description="Extensão do arquivo")
    data: bytes = Field(..., description="Dados binários do arquivo")

    @field_validator("file_extension")
    @classmethod
    def validate_extension(cls, v: str) -> str:
        """Garante que a extensão do arquivo comece com ponto."""
        if v and not v.startswith("."):
            return f".{v}"
        return v

    @classmethod
    def from_path(cls, file_path: Path) -> "ServiceFile":
        """Cria uma instância de ServiceFile a partir de um caminho de arquivo."""
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        content_type, _ = mimetypes.guess_type(str(file_path))
        if content_type is None:
            content_type = "application/octet-stream"

        return cls(
            content_type=content_type,
            file_name=file_path.name,
            file_extension=file_path.suffix,
            data=file_path.read_bytes(),
        )

    def save_to(self, directory: Path) -> Path:
        """Salva o arquivo no diretório especificado."""
        if not directory.exists():
            directory.mkdir(parents=True)

        file_path = directory / self.file_name
        file_path.write_bytes(self.data)
        return file_path
