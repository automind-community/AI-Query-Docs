"""Document repository contract and the process-local implementation."""

from dataclasses import dataclass
from threading import Lock
from typing import Protocol
from uuid import UUID

from api.schemas import DocumentRecord


class DocumentConflictError(Exception):
    """The record conflicts with an existing document."""


@dataclass(frozen=True)
class StoredDocument:
    record: DocumentRecord
    raw_bytes: bytes


class DocumentStore(Protocol):
    """add must atomically enforce unique IDs and case-insensitive filenames."""

    def add(self, record: DocumentRecord, raw_bytes: bytes) -> None: ...
    def list_all(self) -> list[DocumentRecord]: ...
    def get(self, doc_id: UUID) -> StoredDocument | None: ...
    def delete(self, doc_id: UUID) -> bool: ...
    def exists_by_filename(self, filename: str) -> bool: ...
    def clear(self) -> None: ...


class InMemoryDocumentStore:
    def __init__(self) -> None:
        self._documents: dict[UUID, StoredDocument] = {}
        self._filenames: set[str] = set()
        self._lock = Lock()

    def add(self, record: DocumentRecord, raw_bytes: bytes) -> None:
        filename_key = record.filename.casefold()
        with self._lock:
            if filename_key in self._filenames:
                raise DocumentConflictError("A document with this filename already exists.")
            if record.doc_id in self._documents:
                raise DocumentConflictError("A document with this ID already exists.")
            self._documents[record.doc_id] = StoredDocument(record, raw_bytes)
            self._filenames.add(filename_key)

    def list_all(self) -> list[DocumentRecord]:
        with self._lock:
            # Later insertions come first even if the clock returns the same timestamp.
            records = [entry.record for entry in reversed(self._documents.values())]
        return sorted(records, key=lambda record: record.uploaded_at, reverse=True)

    def get(self, doc_id: UUID) -> StoredDocument | None:
        with self._lock:
            return self._documents.get(doc_id)

    def delete(self, doc_id: UUID) -> bool:
        with self._lock:
            entry = self._documents.pop(doc_id, None)
            if entry is None:
                return False
            self._filenames.remove(entry.record.filename.casefold())
            return True

    def exists_by_filename(self, filename: str) -> bool:
        with self._lock:
            return filename.casefold() in self._filenames

    def clear(self) -> None:
        with self._lock:
            self._documents.clear()
            self._filenames.clear()
