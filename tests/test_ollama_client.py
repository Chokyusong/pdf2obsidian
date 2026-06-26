from __future__ import annotations

from pdf2obsidian.core.ai import ollama_client


def test_ollama_not_running_does_not_crash(monkeypatch):
    def fail_request(*args, **kwargs):  # noqa: ANN002, ANN003
        raise OSError("connection refused")

    monkeypatch.setattr(ollama_client, "_request_json", fail_request)

    assert ollama_client.is_ollama_running() is False
    assert ollama_client.list_models() == []


def test_mock_model_list_response(monkeypatch):
    def fake_request(*args, **kwargs):  # noqa: ANN002, ANN003
        return {"models": [{"name": "qwen2.5:3b"}, {"name": "llama3.2:3b"}]}

    monkeypatch.setattr(ollama_client, "_request_json", fake_request)

    assert ollama_client.is_ollama_running() is True
    assert ollama_client.list_models() == ["qwen2.5:3b", "llama3.2:3b"]


def test_mock_generate_response(monkeypatch):
    captured = {}

    def fake_request(*args, **kwargs):  # noqa: ANN002, ANN003
        captured["payload"] = kwargs.get("payload")
        return {"response": "# Sample\n\n## Lecture Reconstruction"}

    monkeypatch.setattr(ollama_client, "_request_json", fake_request)

    result = ollama_client.reconstruct_with_ollama(
        "source transcript",
        model="qwen2.5:3b",
        template="write markdown",
    )

    assert result == "# Sample\n\n## Lecture Reconstruction"
    assert captured["payload"]["options"]["num_predict"] == 8192
    assert captured["payload"]["options"]["num_ctx"] == 32768


def test_timeout_is_returned_as_user_friendly_message(monkeypatch):
    def timeout_request(*args, **kwargs):  # noqa: ANN002, ANN003
        raise TimeoutError

    monkeypatch.setattr(ollama_client, "_request_json", timeout_request)

    result = ollama_client.reconstruct_with_ollama(
        "source transcript",
        model="qwen2.5:3b",
        template="write markdown",
    )

    assert "timed out" in result


def test_pull_model_uses_no_external_api_key(monkeypatch):
    captured = {}

    def fake_request(url, method="GET", payload=None, timeout=10):  # noqa: ANN001
        captured["url"] = url
        captured["payload"] = payload
        captured["timeout"] = timeout
        return {"status": "success"}

    monkeypatch.setattr(ollama_client, "_request_json", fake_request)

    result = ollama_client.pull_model("qwen2.5:3b")

    assert result["ok"] is True
    assert captured["payload"] == {"name": "qwen2.5:3b", "stream": False}
    assert "api_key" not in captured["payload"]
