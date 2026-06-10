import os
import shutil

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import CHROMA_DIR
from app.rag.embeddings import get_embeddings


def is_kb_built(persist_dir: str | None = None) -> bool:
    directory = persist_dir or CHROMA_DIR
    return os.path.isdir(directory) and bool(os.listdir(directory))


def build_vector_store(
    chunks: list[Document],
    persist_dir: str | None = None,
) -> Chroma:
    directory = persist_dir or CHROMA_DIR
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory, exist_ok=True)

    return Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=directory,
    )


def load_vector_store(persist_dir: str | None = None) -> Chroma:
    directory = persist_dir or CHROMA_DIR
    if not is_kb_built(directory):
        raise FileNotFoundError("向量库尚未构建，请先调用 POST /build_kb")

    return Chroma(
        persist_directory=directory,
        embedding_function=get_embeddings(),
    )
