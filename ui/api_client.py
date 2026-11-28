"""Typed HTTP client and Day 5 adapter stubs for the AI QueryDocs Streamlit UI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Sequence

from dotenv import load_dotenv
import httpx

load_dotenv()

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8000
HEALTH_TIMEOUT_SECONDS = 5.0
ASK_TIMEOUT_SECONDS = 30.0
MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
SUPPORTED_UPLOAD_EXTENSIONS = (".pdf", ".txt")


@dataclass(frozen=True, slots=True)
class ApiResult:
    """Structured result returned by all UI API client functions."""

    ok: bool
    data: Any = None
    error: str | None = None


def get_app_name() -> str:
    """Return the configured application display name."""
    raw = os.getenv("APP_NAME")
    if raw is None or not raw.strip():
        return "AI QueryDocs"
    return raw.strip()


def get_api_base_url() -> str:
    """Resolve the FastAPI base URL from environment variables."""
    explicit_url = os.getenv("API_BASE_URL")
    if explicit_url and explicit_url.strip():
        return explicit_url.strip().rstrip("/")

    raw_host = os.getenv("API_HOST")
    host = raw_host.strip() if raw_host and raw_host.strip() else DEFAULT_API_HOST
    if host in {"0.0.0.0", "::"}:
        host = DEFAULT_API_HOST

    raw_port = os.getenv("API_PORT")
    if raw_port is None or not raw_port.strip():
        port = DEFAULT_API_PORT
    else:
        try:
            port = int(raw_port.strip())
        except ValueError as exc:
            raise ValueError(
                f"API_PORT must be a valid integer, got {raw_port!r}."
            ) from exc

    return f"http://{host}:{port}"


def format_file_size(size_bytes: int) -> str:
    """Format a byte count into a concise human-readable label."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def _extract_error_detail(response: httpx.Response) -> str | None:
    """Extract a readable error detail from a failed HTTP response when available."""
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return text[:200] if text else None

    if isinstance(payload, dict) and "detail" in payload:
        detail = payload["detail"]
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
        if isinstance(detail, list) and detail:
            first = detail[0]
            if isinstance(first, dict) and first.get("msg"):
                return str(first["msg"])
    return None


def _request_json(
    method: str,
    path: str,
    *,
    base_url: str | None = None,
    json_payload: dict[str, Any] | None = None,
    timeout: float = HEALTH_TIMEOUT_SECONDS,
) -> ApiResult:
    """Execute an HTTP JSON request and map failures to user-friendly ApiResult objects."""
    try:
        resolved_base_url = (base_url or get_api_base_url()).rstrip("/")
    except ValueError as exc:
        return ApiResult(ok=False, error=str(exc))

    url = f"{resolved_base_url}{path}"
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.request(method, url, json=json_payload)
            response.raise_for_status()
            payload = response.json()
    except httpx.ConnectError:
        return ApiResult(
            ok=False,
            error=(
                f"Cannot connect to the FastAPI server at {resolved_base_url}. "
                "Please ensure the backend is running."
            ),
        )
    except httpx.TimeoutException:
        return ApiResult(
            ok=False,
            error=(
                f"The request to {path} timed out after {timeout:.0f}s. "
                "Please try again."
            ),
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        detail = _extract_error_detail(exc.response)
        message = f"API returned HTTP {status_code}"
        if detail:
            message = f"{message}: {detail}"
        return ApiResult(ok=False, error=message)
    except httpx.RequestError as exc:
        return ApiResult(
            ok=False,
            error=f"Network error while contacting the API: {exc}",
        )
    except ValueError:
        return ApiResult(
            ok=False,
            error=f"The API returned an invalid JSON response from {path}.",
        )

    return ApiResult(ok=True, data=payload)


def check_health(
    *,
    base_url: str | None = None,
    timeout: float = HEALTH_TIMEOUT_SECONDS,
) -> ApiResult:
    """Call GET /health on the FastAPI backend and return a structured ApiResult."""
    result = _request_json(
        "GET",
        "/health",
        base_url=base_url,
        timeout=timeout,
    )
    if not result.ok:
        return result
    if not isinstance(result.data, dict):
        return ApiResult(
            ok=False,
            error="Unexpected /health response format: expected a JSON object.",
        )
    return result


def ask_question(
    question: str,
    *,
    base_url: str | None = None,
    timeout: float = ASK_TIMEOUT_SECONDS,
) -> ApiResult:
    """Call POST /ask with a validated user question and return normalized answer and sources."""
    cleaned_question = question.strip()
    if not cleaned_question:
        return ApiResult(
            ok=False,
            error="Please enter a non-empty question before submitting.",
        )

    result = _request_json(
        "POST",
        "/ask",
        base_url=base_url,
        json_payload={"question": cleaned_question},
        timeout=timeout,
    )
    if not result.ok:
        return result
    if not isinstance(result.data, dict):
        return ApiResult(
            ok=False,
            error="Unexpected /ask response format: expected a JSON object.",
        )

    raw_sources = result.data.get("sources")
    normalized_sources: list[dict[str, Any]] = []
    if isinstance(raw_sources, list):
        for item in raw_sources:
            if not isinstance(item, dict):
                continue
            raw_page = item.get("page")
            page_num = (
                raw_page
                if isinstance(raw_page, int) and not isinstance(raw_page, bool)
                else None
            )
            normalized_sources.append(
                {
                    "doc": str(item.get("doc") or "Unknown document"),
                    "page": page_num,
                    "snippet": str(item.get("snippet") or ""),
                }
            )

    answer = str(result.data.get("answer") or "")
    return ApiResult(
        ok=True,
        data={
            "answer": answer,
            "sources": normalized_sources,
        },
    )


def validate_upload_files(
    files: Sequence[dict[str, Any]],
    existing_documents: Sequence[dict[str, Any]] | None = None,
    *,
    max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate candidate upload payloads for extension, file size, and duplicate names."""
    existing_names = {
        str(doc.get("filename", "")).strip().lower()
        for doc in (existing_documents or [])
        if str(doc.get("filename", "")).strip()
    }
    seen_in_batch: set[str] = set()
    valid_files: list[dict[str, Any]] = []
    errors: list[str] = []

    for item in files:
        filename = str(item.get("name") or "").strip()
        size_bytes = int(item.get("size_bytes") or 0)
        ext = Path(filename).suffix.lower()
        normalized_name = filename.lower()

        if not filename:
            errors.append("Skipped an unnamed file.")
            continue
        if ext not in SUPPORTED_UPLOAD_EXTENSIONS:
            errors.append(
                f"{filename}: unsupported file type '{ext or 'none'}'. "
                "Only PDF and TXT files are supported."
            )
            continue
        if size_bytes <= 0:
            errors.append(f"{filename}: file is empty (0 bytes).")
            continue
        if size_bytes > max_size_bytes:
            errors.append(
                f"{filename}: exceeds the {format_file_size(max_size_bytes)} limit "
                f"({format_file_size(size_bytes)})."
            )
            continue
        if normalized_name in existing_names:
            errors.append(
                f"{filename}: already uploaded in this session (duplicate filename)."
            )
            continue
        if normalized_name in seen_in_batch:
            errors.append(
                f"{filename}: duplicate filename within the selected upload batch."
            )
            continue

        seen_in_batch.add(normalized_name)
        valid_files.append(
            {
                "name": filename,
                "extension": ext,
                "size_bytes": size_bytes,
            }
        )

    return valid_files, errors


# TODO: wire to POST /upload and GET /documents once backend schema is confirmed
def upload_documents(
    files: Sequence[dict[str, Any]],
    existing_documents: Sequence[dict[str, Any]] | None = None,
    *,
    max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
) -> ApiResult:
    """Preview-mode upload adapter that validates files and prepares session records."""
    valid_files, errors = validate_upload_files(
        files,
        existing_documents=existing_documents,
        max_size_bytes=max_size_bytes,
    )
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    added_records = [
        {
            "filename": item["name"],
            "file_type": item["extension"].lstrip(".").upper(),
            "size_bytes": item["size_bytes"],
            "size_label": format_file_size(item["size_bytes"]),
            "uploaded_at": timestamp,
            "status": "Preview (session only)",
        }
        for item in valid_files
    ]

    if not added_records:
        summary_error = (
            errors[0] if len(errors) == 1 else "No valid files were available to upload."
        )
        return ApiResult(
            ok=False,
            data={"added": [], "rejected": errors, "preview_mode": True},
            error=summary_error,
        )

    return ApiResult(
        ok=True,
        data={
            "added": added_records,
            "rejected": errors,
            "preview_mode": True,
        },
    )


# TODO: wire to POST /upload and GET /documents once backend schema is confirmed
def list_documents(session_documents: Sequence[dict[str, Any]]) -> ApiResult:
    """Preview-mode documents listing adapter returning normalized session records."""
    return ApiResult(
        ok=True,
        data={
            "documents": list(session_documents),
            "preview_mode": True,
        },
    )


# TODO: wire to POST /upload and GET /documents once backend schema is confirmed
def remove_document(
    filename: str,
    session_documents: Sequence[dict[str, Any]],
) -> ApiResult:
    """Preview-mode document removal adapter removing a file by filename."""
    target = filename.strip().lower()
    remaining = [
        doc
        for doc in session_documents
        if str(doc.get("filename", "")).strip().lower() != target
    ]
    return ApiResult(
        ok=True,
        data={
            "documents": remaining,
            "removed": filename,
            "preview_mode": True,
        },
    )
