from __future__ import annotations

import contextlib
import json
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "http://localhost:11434"


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _request_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 10,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw.strip() else {}


def is_ollama_running(base_url: str = DEFAULT_BASE_URL) -> bool:
    try:
        _request_json(_url(base_url, "/api/tags"), timeout=3)
        return True
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return False


def list_models(base_url: str = DEFAULT_BASE_URL) -> list[str]:
    try:
        response = _request_json(_url(base_url, "/api/tags"), timeout=5)
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []

    models = response.get("models", [])
    names = []
    for model in models:
        if isinstance(model, dict) and isinstance(model.get("name"), str):
            names.append(model["name"])
    return names


def pull_model(model_name: str, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    if not model_name.strip():
        return {"ok": False, "error": "Choose an Ollama model name first."}

    try:
        response = _request_json(
            _url(base_url, "/api/pull"),
            method="POST",
            payload={"name": model_name, "stream": False},
            timeout=600,
        )
        return {"ok": True, "response": response}
    except TimeoutError:
        return {"ok": False, "error": "Ollama model download timed out."}
    except (OSError, urllib.error.URLError) as exc:
        return {"ok": False, "error": f"Ollama is not reachable: {exc}"}
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"Ollama returned invalid JSON: {exc}"}


def reconstruct_with_ollama(
    text: str,
    model: str,
    template: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 600,
    num_predict: int = 8192,
    num_ctx: int = 32768,
) -> str:
    if not text.strip():
        return "Ollama reconstruction was skipped because the input text is empty."
    if not model.strip():
        return "Ollama reconstruction failed: choose a model first."

    prompt = f"{template.strip()}\n\nSOURCE TEXT:\n{text.strip()}"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": num_predict,
            "num_ctx": num_ctx,
        },
    }

    try:
        response = _request_json(
            _url(base_url, "/api/generate"),
            method="POST",
            payload=payload,
            timeout=timeout,
        )
    except TimeoutError:
        return "Ollama reconstruction failed: request timed out."
    except urllib.error.HTTPError as exc:
        detail = ""
        with contextlib.suppress(Exception):
            detail = exc.read().decode("utf-8", errors="replace").strip()
        message = detail or str(exc)
        return f"Ollama reconstruction failed: {message}"
    except (OSError, urllib.error.URLError) as exc:
        return f"Ollama reconstruction failed: Ollama is not reachable. {exc}"
    except json.JSONDecodeError as exc:
        return f"Ollama reconstruction failed: invalid JSON response. {exc}"

    result = response.get("response")
    if isinstance(result, str) and result.strip():
        return result.strip()
    return "Ollama reconstruction failed: no Markdown text was returned."
