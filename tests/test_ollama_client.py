from __future__ import annotations

from types import SimpleNamespace

from pdf2obsidian.core.ai import ollama_client


def test_ollama_not_running_does_not_crash(monkeypatch):
    def fail_request(*args, **kwargs):  # noqa: ANN002, ANN003
        raise OSError("connection refused")

    monkeypatch.setattr(ollama_client, "_request_json", fail_request)
    monkeypatch.setattr(ollama_client, "list_models_from_cli", lambda: [])

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
    assert captured["payload"]["think"] is False
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

    def fake_request_stream(url, method="GET", payload=None, timeout=10):  # noqa: ANN001
        captured["url"] = url
        captured["payload"] = payload
        captured["timeout"] = timeout
        yield {"status": "pulling manifest"}
        yield {"status": "pulling blob", "completed": 50, "total": 100}
        yield {"status": "success"}

    monkeypatch.setattr(ollama_client, "_request_json_stream", fake_request_stream)

    messages = []
    result = ollama_client.pull_model("qwen2.5:3b", progress=messages.append)

    assert result["ok"] is True
    assert captured["payload"] == {"name": "qwen2.5:3b", "stream": True}
    assert "api_key" not in captured["payload"]
    assert any("50%" in message for message in messages)


def test_pull_model_returns_streamed_error(monkeypatch):
    def fake_request_stream(*args, **kwargs):  # noqa: ANN002, ANN003
        yield {"error": "not enough disk space"}

    monkeypatch.setattr(ollama_client, "_request_json_stream", fake_request_stream)

    result = ollama_client.pull_model("qwen2.5:3b")

    assert result == {"ok": False, "error": "not enough disk space"}


def test_model_list_uses_cli_fallback(monkeypatch):
    def fail_request(*args, **kwargs):  # noqa: ANN002, ANN003
        raise OSError("connection refused")

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        return SimpleNamespace(
            returncode=0,
            stdout=(
                "NAME              ID              SIZE      MODIFIED\n"
                "qwen2.5:7b        abc123          4.7GB     2 days ago\n"
                "gemma3:12b        def456          8.1GB     1 hour ago\n"
            ),
        )

    monkeypatch.setattr(ollama_client, "_request_json", fail_request)
    monkeypatch.setattr(ollama_client, "get_ollama_executable_path", lambda: "ollama")
    monkeypatch.setattr(ollama_client.subprocess, "run", fake_run)

    assert ollama_client.list_models() == ["qwen2.5:7b", "gemma3:12b"]


def test_select_best_available_model_prefers_user_model_when_installed():
    models = ["qwen2.5:7b", "qwen3:14b", "qwen2.5:3b"]

    assert (
        ollama_client.select_best_available_model(models, preferred_model="qwen2.5:7b")
        == "qwen2.5:7b"
    )


def test_select_best_available_model_prefers_recommended_model_without_preference():
    models = ["qwen2.5:7b", "qwen3:14b", "qwen2.5:3b"]

    assert ollama_client.select_best_available_model(models) == "qwen2.5:7b"


def test_select_best_available_model_uses_stable_fallback_before_large_model():
    models = ["qwen2.5:3b", "qwen3:14b"]

    assert ollama_client.select_best_available_model(models) == "qwen2.5:3b"


def test_version_extraction_from_ollama_output():
    assert ollama_client._extract_version("ollama version is 0.9.6") == "0.9.6"


def test_winget_version_extraction_prefers_version_line():
    text = "Name: Ollama\nVersion: 0.9.7\nPublisher: Ollama"

    assert ollama_client._extract_winget_version(text) == "0.9.7"


def test_version_compare_detects_update():
    assert ollama_client._compare_versions("0.9.6", "0.10.0") < 0
    assert ollama_client._compare_versions("0.10.0", "0.9.6") > 0
    assert ollama_client._compare_versions("0.10.0", "0.10.0") == 0


def test_cli_runner_forces_utf8_decoding(monkeypatch):
    captured = {}

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="버전: 0.10.0", stderr="")

    monkeypatch.setattr(ollama_client.subprocess, "run", fake_run)

    result = ollama_client._run_cli(["winget", "show"], timeout_sec=5)

    assert result.stdout == "버전: 0.10.0"
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"
