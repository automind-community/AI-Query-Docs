"""HTTP contract and repository integration tests. Run with unittest discover."""

import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from api.config import Settings
from api.main import create_app
from api.schemas import AskResponse
from api.services.storage import InMemoryDocumentStore


class APIContractTests(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryDocumentStore()
        self.app = create_app(settings=Settings(), document_store=self.store)
        self.client = self.enterContext(TestClient(self.app))

    def upload(self, filename, content, mime="application/octet-stream"):
        return self.client.post("/upload", files={"file": (filename, content, mime)})

    def documents(self):
        response = self.client.get("/documents")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def assert_api_error(self, response, status, detail_fragment=None):
        self.assertEqual(response.status_code, status, response.text)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertEqual(set(response.json()), {"detail"})
        detail = response.json()["detail"]
        self.assertIsInstance(detail, str)
        self.assertTrue(detail.strip())
        if detail_fragment:
            self.assertIn(detail_fragment, detail)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "ok", "app": "AI QueryDocs", "environment": "development",
        })

    def test_ask_preserves_mock_answer_and_citations(self):
        payloads = [{"question": "What is RAG?"}, {"question": "What is RAG?", "context": "old client"}]
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/ask", json=payload)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {
                    "answer": "Test answer [1]",
                    "sources": [{"doc": "file.pdf", "page": 3, "snippet": "..."}],
                })

    def test_ask_rejects_empty_whitespace_and_non_string_questions(self):
        for value in ("", " \t\n", None, 42):
            with self.subTest(value=value):
                response = self.client.post("/ask", json={"question": value})
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["detail"][0]["loc"], ["body", "question"])

    def test_ask_calls_injected_service_with_trimmed_question(self):
        class EchoQAService:
            def answer(self, question):
                return AskResponse(answer=question, sources=[])

        with TestClient(create_app(settings=Settings(), qa_service=EchoQAService())) as client:
            response = client.post("/ask", json={"question": "  Which page?  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"answer": "Which page?", "sources": []})

    def test_upload_returns_full_record_and_retains_original_bytes(self):
        cases = [
            ("Résumé.TxT", "Résumé\n".encode("utf-8-sig"), "TXT"),
            ("guide.PDF", b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF", "PDF"),
        ]
        for name, content, file_type in cases:
            with self.subTest(name=name):
                response = self.upload(name, content)
                self.assertEqual(response.status_code, 201, response.text)
                body = response.json()
                self.assertEqual(set(body), {"document", "message"})
                self.assertEqual(body["message"], "Document stored.")
                document = body["document"]
                self.assertEqual(set(document), {
                    "doc_id", "filename", "file_type", "size_bytes", "uploaded_at", "status",
                })
                doc_id = UUID(document["doc_id"])
                self.assertEqual(str(doc_id), document["doc_id"])
                uploaded_at = datetime.fromisoformat(document["uploaded_at"])
                self.assertEqual(uploaded_at.utcoffset(), timedelta(0))
                self.assertEqual(document["filename"], name)
                self.assertEqual(document["file_type"], file_type)
                self.assertEqual(document["size_bytes"], len(content))
                self.assertEqual(document["status"], "stored_mock")
                self.assertEqual(self.store.get(doc_id).raw_bytes, content)

    def test_rejects_invalid_uploads_without_storing_them(self):
        cases = [
            ("report.docx", b"report", "extension"),
            ("program.exe", b"MZ", "extension"),
            ("fake.pdf", b"prefix %PDF-1.4", "%PDF-"),
            ("invalid.txt", b"\xff\xfe", "UTF-8"),
            ("binary.txt", b"abc\x00def", "control"),
            ("utf16.txt", "notes".encode("utf-16"), "UTF-8"),
            ("blank.txt", " \r\n\t\u2003".encode(), "non-whitespace"),
            ("bom.txt", b"\xef\xbb\xbf", "non-whitespace"),
            ("empty.txt", b"", "empty"),
            ("empty.pdf", b"", "empty"),
            ("../", b"x", "filename"),
        ]
        for name, content, fragment in cases:
            with self.subTest(name=name):
                self.assert_api_error(self.upload(name, content), 400, fragment)
        self.assertEqual(self.documents(), {"documents": [], "total": 0})

    def test_explicit_empty_filename_and_missing_file(self):
        # Keep filename="" on the wire. HTTP clients can omit it when building forms.
        body = (b'--boundary\r\nContent-Disposition: form-data; name="file"; filename=""'
                b"\r\nContent-Type: text/plain\r\n\r\nhello\r\n--boundary--\r\n")
        response = self.client.post("/upload", content=body, headers={
            "Content-Type": "multipart/form-data; boundary=boundary",
        })
        self.assert_api_error(response, 400, "filename")
        self.assertEqual(self.client.post("/upload").status_code, 422)

    def test_size_limit_is_inclusive_and_both_413_paths_return_json(self):
        limit = 10 * 1024 * 1024
        response = self.upload("at-limit.txt", b"a" * limit)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["document"]["size_bytes"], limit)
        for size in (limit + 1, limit + 1024 * 1024):
            with self.subTest(size=size):
                self.assert_api_error(self.upload("over.txt", b"a" * size), 413, "limit")
        self.assertEqual(self.documents()["total"], 1)

    def test_sanitizes_posix_and_windows_paths(self):
        for path, name in [("../../evil.txt", "evil.txt"), (r"C:\folder\guide.pdf", "guide.pdf")]:
            with self.subTest(path=path):
                response = self.upload(path, b"%PDF-1.4\n")
                self.assertEqual(response.status_code, 201, response.text)
                self.assertEqual(response.json()["document"]["filename"], name)

    def test_single_file_contract_rejects_multiple_files_without_partial_storage(self):
        response = self.client.post("/upload", files=[
            ("file", ("one.txt", b"first")), ("file", ("two.txt", b"second")),
        ])
        self.assert_api_error(response, 400)
        self.assertEqual(self.documents(), {"documents": [], "total": 0})

    def test_duplicate_checks_use_the_sanitized_casefolded_name(self):
        first = self.upload("Notes.TXT", b"first")
        self.assertEqual(first.status_code, 201)
        self.assert_api_error(self.upload("../notes.txt", b"second"), 409, "already exists")
        self.assertEqual(self.documents(), {"documents": [first.json()["document"]], "total": 1})
        self.assertTrue(self.store.exists_by_filename("NOTES.txt"))

    def test_concurrent_uploads_claim_a_filename_once(self):
        start = Barrier(2)

        def submit(name):
            start.wait(timeout=10)
            return self.upload(name, b"notes").status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, ["report.txt", "REPORT.TXT"]))
        self.assertCountEqual(results, [201, 409])
        self.assertEqual(self.documents()["total"], 1)

    def test_documents_are_listed_newest_first_with_matching_total(self):
        self.assertEqual(self.documents(), {"documents": [], "total": 0})
        older = self.upload("z.txt", b"one").json()["document"]
        newer = self.upload("a.txt", b"two").json()["document"]
        self.assertEqual(self.documents(), {"documents": [newer, older], "total": 2})

    def test_delete_removes_content_and_releases_filename(self):
        record = self.upload("notes.txt", b"first").json()["document"]
        doc_id = record["doc_id"]
        response = self.client.delete(f"/documents/{doc_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "doc_id": doc_id, "deleted": True, "message": "Document deleted.",
        })
        self.assertIsNone(self.store.get(UUID(doc_id)))
        self.assertEqual(self.documents(), {"documents": [], "total": 0})
        self.assert_api_error(self.client.delete(f"/documents/{doc_id}"), 404)
        uploaded = self.upload("notes.txt", b"replacement")
        self.assertEqual(uploaded.status_code, 201)
        self.assertNotEqual(uploaded.json()["document"]["doc_id"], doc_id)

    def test_unknown_document_returns_404(self):
        for doc_id in (str(uuid4()), "unknown-id"):
            with self.subTest(doc_id=doc_id):
                self.assert_api_error(self.client.delete(f"/documents/{doc_id}"), 404)

    def test_app_instances_are_isolated_and_repository_clear_releases_names(self):
        self.assertEqual(self.upload("test.txt", b"text").status_code, 201)
        with TestClient(create_app(settings=Settings())) as other:
            self.assertEqual(other.get("/documents").json(), {"documents": [], "total": 0})
        self.store.clear()
        self.assertFalse(self.store.exists_by_filename("test.txt"))
        self.assertEqual(self.documents(), {"documents": [], "total": 0})

    def test_cors_preflight_and_actual_response_headers(self):
        for origin in ("http://localhost:8501", "http://127.0.0.1:8501"):
            with self.subTest(origin=origin):
                response = self.client.options("/upload", headers={
                    "Origin": origin, "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type",
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["access-control-allow-origin"], origin)
                self.assertIn("POST", response.headers["access-control-allow-methods"])
                actual = self.client.get("/documents", headers={"Origin": origin})
                self.assertEqual(actual.headers["access-control-allow-origin"], origin)
        denied = self.client.options("/upload", headers={
            "Origin": "https://other.example", "Access-Control-Request-Method": "POST",
        })
        self.assertEqual(denied.status_code, 400)
        self.assertNotIn("access-control-allow-origin", denied.headers)

    def test_openapi_declares_multipart_models_and_error_responses(self):
        spec = self.client.get("/openapi.json").json()
        self.assertEqual(spec["info"]["version"], "0.2.0")
        upload = spec["paths"]["/upload"]["post"]
        self.assertIn("multipart/form-data", upload["requestBody"]["content"])
        self.assertIn("OCR", upload["description"])
        delete = spec["paths"]["/documents/{doc_id}"]["delete"]
        listing = spec["paths"]["/documents"]["get"]
        for operation, expected in [
            (upload, {"201": "UploadResponse", "400": "ErrorResponse",
                      "409": "ErrorResponse", "413": "ErrorResponse"}),
            (listing, {"200": "DocumentListResponse"}),
            (delete, {"200": "DeleteDocumentResponse", "404": "ErrorResponse"}),
        ]:
            for status, model in expected.items():
                schema = operation["responses"][status]["content"]["application/json"]["schema"]
                self.assertEqual(schema["$ref"], f"#/components/schemas/{model}")
        record = spec["components"]["schemas"]["DocumentRecord"]
        self.assertEqual(record["properties"]["doc_id"]["format"], "uuid")
        self.assertEqual(record["properties"]["uploaded_at"]["format"], "date-time")
        self.assertEqual(set(record["required"]), set(record["examples"][0]))


class SettingsTests(unittest.TestCase):
    def test_dotenv_types_origin_formats_and_environment_precedence(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            config_file = Path(directory) / "settings.env"
            config_file.write_text(
                'CORS_ORIGINS=["https://docs.example"]\nAPI_PORT=9001\nMAX_FILE_SIZE_MB=2\n',
                encoding="utf-8",
            )
            settings = Settings.from_env(config_file)
            self.assertEqual(settings.API_PORT, 9001)
            self.assertEqual(settings.CORS_ORIGINS, ("https://docs.example",))
            self.assertEqual(settings.max_file_size_bytes, 2 * 1024 * 1024)
            os.environ["CORS_ORIGINS"] = "http://localhost:8501, https://team.example"
            self.assertEqual(Settings.from_env(config_file).CORS_ORIGINS, (
                "http://localhost:8501", "https://team.example",
            ))
