import os
import unittest
from unittest.mock import patch

from intention_commerce.llm import ApiClient, LLMError, OllamaClient, parse_json_object


class LLMClientTests(unittest.TestCase):
    def test_json_fence_is_accepted(self):
        self.assertEqual(parse_json_object('```json\n{"dn":"DN_OrdersDraft"}\n```'), {"dn": "DN_OrdersDraft"})

    def test_non_object_json_is_rejected(self):
        with self.assertRaises(LLMError):
            parse_json_object('[1,2,3]')

    @patch("intention_commerce.llm.post_json")
    def test_ollama_chat_response_is_decoded(self, post_json):
        post_json.return_value = {"message": {"content": '{"dn":"DN_OrdersSubmit","arguments":{"order_id":"ORD-1"}}'}}
        with patch.dict(os.environ, {"OLLAMA_MODEL": "gemma3:4b"}, clear=False):
            action = OllamaClient().complete_json("system", "user")
        self.assertEqual(action["arguments"]["order_id"], "ORD-1")
        payload = post_json.call_args.args[1]
        self.assertEqual(payload["model"], "gemma3:4b")
        self.assertFalse(payload["stream"])

    def test_api_client_requires_explicit_model_and_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(LLMError, "API_KEY"):
                ApiClient()
        with patch.dict(os.environ, {"API_KEY": "test-only"}, clear=True):
            with self.assertRaisesRegex(LLMError, "API_MODEL"):
                ApiClient()

    @patch("intention_commerce.llm.post_json")
    def test_api_chat_response_is_decoded_without_logging_secret(self, post_json):
        post_json.return_value = {"choices": [{"message": {"content": '{"finish":true}'}}]}
        with patch.dict(os.environ, {"API_KEY": "test-secret", "API_MODEL": "test-model"}, clear=True):
            action = ApiClient().complete_json("system", "user")
        self.assertTrue(action["finish"])
        self.assertEqual(post_json.call_args.args[1]["model"], "test-model")
        self.assertEqual(post_json.call_args.args[2]["Authorization"], "Bearer test-secret")


if __name__ == "__main__":
    unittest.main()
