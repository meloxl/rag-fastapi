from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter

HEADERS_TO_SPLIT_ON = [
    ("#", "section"),
    ("####", "question"),
]

_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=HEADERS_TO_SPLIT_ON,
    strip_headers=False,
)


def split_documents(documents: list[Document]) -> list[Document]:
    splits: list[Document] = []

    for doc in documents:
        header_splits = _splitter.split_text(doc.page_content)
        for split in header_splits:
            split.metadata = {**doc.metadata, **split.metadata}
            splits.append(split)

    return splits
