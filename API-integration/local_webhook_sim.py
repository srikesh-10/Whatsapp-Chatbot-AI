import os
from unittest.mock import patch

# Use dummy values for local simulation without requiring real secrets.
os.environ.setdefault("WHATSAPP_TOKEN", "dummy-token")
os.environ.setdefault("WHATSAPP_PHONE_NUMBER_ID", "123456789")
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "hello123")

import whatsapp


class MockResp:
    def __init__(self, json_data=None, content=b""):
        self._json = json_data or {}
        self.content = content

    def json(self):
        return self._json


def run() -> None:
    client = whatsapp.app.test_client()

    payload_non_audio = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "919999999999",
                                    "type": "text",
                                    "text": {"body": "hello"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    payload_audio = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "919888888888",
                                    "type": "audio",
                                    "audio": {"id": "mock-media-id"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    print("--- Non-audio payload test ---")
    with patch.object(whatsapp, "send_message") as send_message_mock:
        resp = client.post("/webhook", json=payload_non_audio)
        print("status=", resp.status_code, "body=", resp.data.decode())
        print("send_message_called=", send_message_mock.called)
        print("send_message_args=", send_message_mock.call_args)

    print("\n--- Audio payload test (fully mocked externals) ---")
    with (
        patch.object(whatsapp, "send_message") as send_message_mock,
        patch.object(
            whatsapp.requests,
            "get",
            side_effect=[
                MockResp({"url": "https://mock.local/audio.bin"}),
                MockResp(content=b"fake-opus-bytes"),
            ],
        ) as get_mock,
        patch.object(whatsapp, "convert_to_wav") as convert_mock,
        patch.object(
            whatsapp,
            "transcribe_audio",
            return_value="Drinking turmeric water cures diabetes",
        ) as transcribe_mock,
        patch.object(
            whatsapp.GoogleTranslator,
            "translate",
            return_value="Drinking turmeric water cures diabetes",
        ) as translate_mock,
        patch.object(
            whatsapp,
            "run_pipeline",
            return_value={
                "claim": "Drinking turmeric water cures diabetes",
                "verdict": "LIKELY FALSE",
                "confidence": 21,
                "sources": ["https://example.org/factcheck"],
                "explanation": "Mock explanation",
                "counter_message": "MOCK_FACTCHECK_REPORT",
            },
        ) as pipeline_mock,
        patch.object(whatsapp.os, "remove") as remove_mock,
    ):
        resp = client.post("/webhook", json=payload_audio)
        print("status=", resp.status_code, "body=", resp.data.decode())
        print("requests_get_calls=", get_mock.call_count)
        print("convert_called=", convert_mock.called)
        print("transcribe_called=", transcribe_mock.called)
        print("translate_called=", translate_mock.called)
        print("pipeline_called=", pipeline_mock.called)
        print("remove_called=", remove_mock.called)
        print("send_message_called=", send_message_mock.called)

        args, _ = send_message_mock.call_args
        print("recipient=", args[0])
        print("message_preview=", args[1][:220].replace("\n", " | "))


if __name__ == "__main__":
    run()
