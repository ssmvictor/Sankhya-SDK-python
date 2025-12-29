import pytest
from pathlib import Path
from sankhya_sdk.value_objects.service_file import ServiceFile


def test_service_file_creation():
    content = b"test data"
    sf = ServiceFile(
        content_type="text/plain",
        file_name="test.txt",
        file_extension=".txt",
        data=content,
    )
    assert sf.content_type == "text/plain"
    assert sf.file_name == "test.txt"
    assert sf.file_extension == ".txt"
    assert sf.data == content


def test_service_file_extension_validation():
    sf = ServiceFile(
        content_type="text/plain",
        file_name="test.txt",
        file_extension="txt",
        data=b"data",
    )
    assert sf.file_extension == ".txt"

    sf2 = ServiceFile(
        content_type="text/plain",
        file_name="test.txt",
        file_extension=".txt",
        data=b"data",
    )
    assert sf2.file_extension == ".txt"


def test_service_file_from_path(tmp_path):
    file_path = tmp_path / "test_file.txt"
    content = b"hello world"
    file_path.write_bytes(content)

    sf = ServiceFile.from_path(file_path)
    assert sf.file_name == "test_file.txt"
    assert sf.file_extension == ".txt"
    assert sf.data == content
    assert sf.content_type == "text/plain"


def test_service_file_from_path_not_found():
    with pytest.raises(FileNotFoundError):
        ServiceFile.from_path(Path("non_existent_file.xyz"))


def test_service_file_save_to(tmp_path):
    content = b"binary data"
    sf = ServiceFile(
        content_type="application/octet-stream",
        file_name="output.bin",
        file_extension=".bin",
        data=content,
    )

    save_dir = tmp_path / "output_dir"
    saved_path = sf.save_to(save_dir)

    assert saved_path.exists()
    assert saved_path.read_bytes() == content
    assert saved_path.name == "output.bin"


def test_service_file_serialization():
    sf = ServiceFile(
        content_type="text/plain",
        file_name="test.txt",
        file_extension=".txt",
        data=b"some data",
    )
    dump = sf.model_dump()
    assert dump["file_name"] == "test.txt"
    assert dump["data"] == b"some data"

    json_dump = sf.model_dump_json()
    assert "test.txt" in json_dump
