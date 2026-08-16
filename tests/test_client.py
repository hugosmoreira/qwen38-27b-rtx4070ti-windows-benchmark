import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from qwen_bench.client import ClientError, LlamaCppClient, require_loopback_uri


class _Handler(BaseHTTPRequestHandler):
    model_path = ""

    def do_GET(self) -> None:
        values = {
            "/health": {"status": "ok"},
            "/v1/models": {"data": [{"id": "test-model"}]},
            "/props": {
                "model_path": self.model_path,
                "total_slots": 1,
                "default_generation_settings": {"n_ctx": 4096},
            },
        }
        self._json(values[self.path])

    def do_POST(self) -> None:
        length = int(self.headers["Content-Length"])
        json.loads(self.rfile.read(length))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        chunks = [
            {
                "choices": [{"delta": {"content": "hello"}, "finish_reason": None}],
                "system_fingerprint": "test-fingerprint",
            },
            {
                "choices": [{"delta": {"content": " world"}, "finish_reason": "length"}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 2, "total_tokens": 4},
                "timings": {"cache_n": 0, "prompt_per_second": 10.0, "predicted_per_second": 20.0},
            },
        ]
        for chunk in chunks:
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")

    def _json(self, value: object) -> None:
        payload = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return


class ClientTests(unittest.TestCase):
    def test_refuses_non_loopback_or_credentialed_uri(self) -> None:
        with self.assertRaises(ClientError):
            require_loopback_uri("https://example.com")
        with self.assertRaises(ClientError):
            require_loopback_uri("http://user:password@127.0.0.1:8090")

    def test_preflight_and_streaming_chat(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model.gguf"
            model.touch()
            _Handler.model_path = str(model)
            server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                client = LlamaCppClient(f"http://127.0.0.1:{server.server_port}", timeout_seconds=5)
                preflight = client.validate_server(
                    model_alias="test-model",
                    expected_context_size=4096,
                    expected_parallel_slots=1,
                    expected_model_path=str(model),
                )
                self.assertEqual(preflight["status"], "passed")
                result = client.stream_chat({"model": "test-model", "stream": True})
                self.assertEqual(result.content, "hello world")
                self.assertEqual(result.finish_reason, "length")
                self.assertEqual(result.usage["completion_tokens"], 2)
                self.assertEqual(result.timings["cache_n"], 0)
                self.assertIsNotNone(result.time_to_first_content_token_ms)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(5)


if __name__ == "__main__":
    unittest.main()
