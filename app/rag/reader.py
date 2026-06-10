import os
import re
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

from app.config import DOCS_DIR


def _parse_category(filename: str) -> str:
    if "单身" in filename:
        return "单身"
    if "恋爱" in filename:
        return "恋爱"
    if "已婚" in filename:
        return "已婚"
    return Path(filename).stem


def list_markdown_files(docs_dir: str | None = None) -> list[str]:
    directory = docs_dir or DOCS_DIR
    if not os.path.isdir(directory):
        return []
    return sorted(
        name for name in os.listdir(directory) if name.lower().endswith(".md")
    )


def load_documents(docs_dir: str | None = None) -> list[Document]:
    directory = docs_dir or DOCS_DIR
    documents: list[Document] = []

    for filename in list_markdown_files(directory):
        file_path = os.path.join(directory, filename)
        loader = TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)
        docs = loader.load()
        category = _parse_category(filename)

        for doc in docs:
            doc.metadata["source"] = filename
            doc.metadata["category"] = category
            doc.metadata["file_path"] = file_path

        documents.extend(docs)

    return documents


def sanitize_upload_filename(filename: str) -> str:
    name = os.path.basename(filename.strip())
    if not name:
        raise ValueError("文件名不能为空")
    if not re.match(r"^[\w\u4e00-\u9fff\s\-—]+\.md$", name, re.IGNORECASE):
        raise ValueError("仅支持 .md 文件，且文件名不能包含特殊字符")
    return name
