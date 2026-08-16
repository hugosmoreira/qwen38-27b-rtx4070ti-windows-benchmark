import unittest

from qwen_bench.sse import SSEProtocolError, iter_sse_json


class SSEParsingTests(unittest.TestCase):
    def test_parses_data_and_stops_at_done(self) -> None:
        lines = [
            b": keepalive\n",
            b"event: message\n",
            b'data: {"choices":[]}\n',
            b"\n",
            b"data: [DONE]\n",
            b'data: {"ignored":true}\n',
        ]
        self.assertEqual(list(iter_sse_json(lines)), [{"choices": []}])

    def test_rejects_invalid_json(self) -> None:
        with self.assertRaises(SSEProtocolError):
            list(iter_sse_json(["data: {broken}\n"]))

    def test_rejects_non_object_json(self) -> None:
        with self.assertRaises(SSEProtocolError):
            list(iter_sse_json(["data: [1, 2]\n"]))


if __name__ == "__main__":
    unittest.main()
