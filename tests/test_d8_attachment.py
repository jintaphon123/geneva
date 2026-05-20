"""Unit tests for D8 file attachment chain."""

from src.agent.conversation import Conversation


class TestMultimodalMessages:
    def test_add_user_message_with_images_builds_content_list(self):
        conv = Conversation()
        conv.add_user_message_with_images(
            "describe this image",
            [{"type": "base64", "media_type": "image/jpeg", "data": "abc123"}],
        )
        msgs = conv.get_messages()
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert isinstance(msgs[0]["content"], list)
        assert msgs[0]["content"][0] == {"type": "text", "text": "describe this image"}
        assert msgs[0]["content"][1]["type"] == "image"

    def test_text_only_message_still_string(self):
        conv = Conversation()
        conv.add_user_message("hello")
        msgs = conv.get_messages()
        assert msgs[0]["content"] == "hello"

    def test_images_chat_request_parsing(self):
        from src.geneva.web_api import chat_request_from_payload

        payload = {
            "message": "what is this?",
            "images": [{"type": "base64", "media_type": "image/png", "data": "abc"}],
        }
        req, err = chat_request_from_payload(payload)
        assert err is None
        assert req is not None
        assert len(req.images) == 1
        assert req.images[0]["data"] == "abc"

    def test_invalid_image_skipped(self):
        from src.geneva.web_api import chat_request_from_payload

        payload = {
            "message": "test",
            "images": [{"type": "url", "url": "http://evil.com"}],
        }
        req, err = chat_request_from_payload(payload)
        assert err is None
        assert req is not None
        assert req.images == []
