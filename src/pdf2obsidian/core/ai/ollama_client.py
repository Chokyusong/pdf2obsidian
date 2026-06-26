from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_RECOMMENDED_MODEL = "qwen2.5:7b"
FALLBACK_MODELS = [
    "qwen2.5:7b",
    "qwen2.5:3b",
    "llama3.2:3b",
    "gemma3:4b",
]
OLLAMA_DOWNLOAD_URL = "https://ollama.com/download/OllamaSetup.exe"


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


def get_ollama_executable_path() -> str | None:
    executable = shutil.which("ollama")
    if executable:
        return executable

    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Ollama" / "ollama.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def is_ollama_installed(base_url: str = DEFAULT_BASE_URL) -> bool:
    executable = get_ollama_executable_path()
    if executable:
        try:
            result = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return True
        return result.returncode == 0 or bool(result.stdout.strip() or result.stderr.strip())
    return is_ollama_running(base_url)


def list_models_from_api(base_url: str = DEFAULT_BASE_URL) -> list[str]:
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


def list_models_from_cli() -> list[str]:
    executable = get_ollama_executable_path()
    if not executable:
        return []
    try:
        result = subprocess.run(
            [executable, "list"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []

    names: list[str] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("name"):
            continue
        first_column = stripped.split()[0]
        if ":" in first_column:
            names.append(first_column)
    return names


def list_models(base_url: str = DEFAULT_BASE_URL) -> list[str]:
    models = list_models_from_api(base_url)
    if models:
        return models
    return list_models_from_cli()


def select_best_available_model(
    models: list[str],
    preferred_model: str | None = None,
) -> str:
    normalized_preferred = (preferred_model or "").strip()
    if normalized_preferred and normalized_preferred in models:
        return normalized_preferred
    if not models:
        return normalized_preferred or DEFAULT_RECOMMENDED_MODEL
    return sorted(models, key=_model_quality_score, reverse=True)[0]


def _model_quality_score(model_name: str) -> tuple[float, int, str]:
    normalized = model_name.lower()
    size = 0.0
    for marker in normalized.replace("-", ":").split(":"):
        if marker.endswith("b"):
            with contextlib.suppress(ValueError):
                size = float(marker[:-1])
    family_score = 0
    if "qwen" in normalized:
        family_score = 4
    elif "gemma" in normalized:
        family_score = 3
    elif "llama" in normalized:
        family_score = 2
    return (size, family_score, normalized)


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


def start_ollama_server(base_url: str = DEFAULT_BASE_URL) -> bool:
    if is_ollama_running(base_url):
        return True
    executable = get_ollama_executable_path()
    if not executable:
        return False

    popen_kwargs: dict[str, Any] = {}
    if os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.Popen(
            [executable, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **popen_kwargs,
        )
    except OSError:
        return False
    return True


def wait_for_ollama_ready(
    timeout_sec: int = 300,
    interval_sec: int = 5,
    base_url: str = DEFAULT_BASE_URL,
) -> bool:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if is_ollama_running(base_url):
            return True
        if is_ollama_installed(base_url):
            start_ollama_server(base_url)
        time.sleep(interval_sec)
    return is_ollama_running(base_url)


def install_ollama_with_winget(timeout_sec: int = 900) -> bool:
    winget = shutil.which("winget")
    if not winget:
        return False
    try:
        result = subprocess.run(
            [
                winget,
                "install",
                "--id",
                "Ollama.Ollama",
                "-e",
                "--accept-source-agreements",
                "--accept-package-agreements",
            ],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def download_ollama_installer(download_url: str = OLLAMA_DOWNLOAD_URL) -> str | None:
    installer_path = Path(tempfile.gettempdir()) / "OllamaSetup.exe"
    try:
        with urllib.request.urlopen(download_url, timeout=60) as response:
            with installer_path.open("wb") as output:
                shutil.copyfileobj(response, output)
    except (OSError, urllib.error.URLError, TimeoutError):
        return None
    return str(installer_path) if installer_path.is_file() else None


def run_ollama_installer(installer_path: str) -> bool:
    path = Path(installer_path)
    if not path.is_file():
        return False
    try:
        subprocess.Popen([str(path)])
    except OSError:
        return False
    return True


def ensure_ollama_ready_and_model(
    model_name: str = DEFAULT_RECOMMENDED_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    log: Any | None = None,
) -> dict[str, Any]:
    selected_model = model_name.strip() or DEFAULT_RECOMMENDED_MODEL

    def emit(message: str) -> None:
        if log:
            log(message)

    emit("Ollama installation check started.")
    if not is_ollama_installed(base_url):
        emit("Ollama is not installed. Trying winget installation.")
        installed = install_ollama_with_winget()
        if not installed:
            emit("winget installation failed. Downloading official Ollama installer.")
            installer_path = download_ollama_installer()
            if not installer_path:
                return {"ok": False, "error": "Ollama installer download failed."}
            emit("Starting Ollama installer. Approve Windows permission prompts if shown.")
            if not run_ollama_installer(installer_path):
                return {"ok": False, "error": "Ollama installer could not be started."}
        emit("Waiting for Ollama installation to become ready.")
        if not wait_for_ollama_ready(timeout_sec=300, base_url=base_url):
            return {"ok": False, "error": "Ollama was not ready after installation."}

    if not is_ollama_running(base_url):
        emit("Starting Ollama server.")
        start_ollama_server(base_url)
        if not wait_for_ollama_ready(timeout_sec=60, base_url=base_url):
            return {"ok": False, "error": "Ollama server did not start."}

    models = list_models(base_url)
    if models:
        selected_model = select_best_available_model(models, selected_model)
        emit(f"Installed Ollama models detected: {', '.join(models)}")
    else:
        emit("No installed Ollama models were detected.")

    if selected_model not in models:
        emit(f"Downloading Ollama model: {selected_model}")
        pull_result = pull_model(selected_model, base_url=base_url)
        if not pull_result.get("ok"):
            return {
                "ok": False,
                "error": str(pull_result.get("error", "Ollama model download failed.")),
            }

    emit("Ollama setup finished.")
    return {"ok": True, "model": selected_model, "models": list_models(base_url)}


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
