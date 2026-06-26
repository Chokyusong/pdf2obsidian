from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
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
OLLAMA_WINGET_ID = "Ollama.Ollama"


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


def _request_json_stream(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 10,
) -> Iterator[dict[str, Any]]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if line:
                yield json.loads(line)


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
            result = _run_cli([executable, "--version"], timeout_sec=10)
        except (OSError, subprocess.SubprocessError):
            return True
        return result.returncode == 0 or bool(result.stdout.strip() or result.stderr.strip())
    return is_ollama_running(base_url)


def get_ollama_version() -> str | None:
    executable = get_ollama_executable_path()
    if not executable:
        return None
    try:
        result = _run_cli([executable, "--version"], timeout_sec=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return _extract_version(f"{result.stdout}\n{result.stderr}")


def get_latest_ollama_version_from_winget(timeout_sec: int = 60) -> str | None:
    winget = shutil.which("winget")
    if not winget:
        return None
    try:
        result = _run_cli(
            [
                winget,
                "show",
                "--id",
                OLLAMA_WINGET_ID,
                "-e",
                "--accept-source-agreements",
            ],
            timeout_sec=timeout_sec,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return _extract_winget_version(f"{result.stdout}\n{result.stderr}")


def check_ollama_update_status() -> dict[str, Any]:
    installed_version = get_ollama_version()
    latest_version = get_latest_ollama_version_from_winget()
    update_available = False
    if installed_version and latest_version:
        update_available = _compare_versions(installed_version, latest_version) < 0
    return {
        "installed": is_ollama_installed(),
        "installed_version": installed_version,
        "latest_version": latest_version,
        "update_available": update_available,
    }


def _extract_version(text: str) -> str | None:
    match = re.search(r"\d+(?:\.\d+){1,3}", text)
    return match.group(0) if match else None


def _extract_winget_version(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("version:") or stripped.startswith("버전:"):
            return _extract_version(stripped)
    return _extract_version(text)


def _compare_versions(current: str, latest: str) -> int:
    current_parts = _version_parts(current)
    latest_parts = _version_parts(latest)
    max_len = max(len(current_parts), len(latest_parts))
    current_parts.extend([0] * (max_len - len(current_parts)))
    latest_parts.extend([0] * (max_len - len(latest_parts)))
    if current_parts < latest_parts:
        return -1
    if current_parts > latest_parts:
        return 1
    return 0


def _version_parts(version: str) -> list[int]:
    return [int(part) for part in re.findall(r"\d+", version)]


def _run_cli(command: list[str], timeout_sec: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_sec,
        check=False,
    )


def _format_bytes(size: int) -> str:
    value = float(max(size, 0))
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def _pull_progress_percent(event: dict[str, Any]) -> int | None:
    completed = event.get("completed")
    total = event.get("total")
    if (
        not isinstance(completed, (int, float))
        or not isinstance(total, (int, float))
        or total <= 0
    ):
        return None
    percent = int((completed / total) * 100)
    return max(0, min(100, percent))


def _format_pull_progress(event: dict[str, Any], model_name: str) -> str | None:
    status = str(event.get("status") or "").strip()
    percent = _pull_progress_percent(event)
    completed = event.get("completed")
    total = event.get("total")
    if (
        percent is not None
        and isinstance(completed, (int, float))
        and isinstance(total, (int, float))
    ):
        status_prefix = f"{status} " if status else ""
        return (
            f"{model_name}: {status_prefix}{percent}% "
            f"({_format_bytes(int(completed))} / {_format_bytes(int(total))})"
        )
    if status:
        return f"{model_name}: {status}"
    return None


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
        result = _run_cli([executable, "list"], timeout_sec=20)
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


def pull_model(
    model_name: str,
    base_url: str = DEFAULT_BASE_URL,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if not model_name.strip():
        return {"ok": False, "error": "Choose an Ollama model name first."}

    try:
        last_event: dict[str, Any] = {}
        last_status: str | None = None
        last_bucket: int | None = None
        last_message: str | None = None
        for event in _request_json_stream(
            _url(base_url, "/api/pull"),
            method="POST",
            payload={"name": model_name, "stream": True},
            timeout=600,
        ):
            last_event = event
            if event.get("error"):
                return {"ok": False, "error": str(event["error"])}
            message = _format_pull_progress(event, model_name)
            if progress and message:
                status = str(event.get("status") or "")
                percent = _pull_progress_percent(event)
                bucket = percent // 5 if percent is not None else None
                should_emit = (
                    status != last_status
                    or bucket != last_bucket
                    or message != last_message
                )
                if should_emit:
                    progress(message)
                    last_status = status
                    last_bucket = bucket
                    last_message = message
        return {"ok": True, "response": last_event}
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
        result = _run_cli(
            [
                winget,
                "install",
                "--id",
                OLLAMA_WINGET_ID,
                "-e",
                "--accept-source-agreements",
                "--accept-package-agreements",
            ],
            timeout_sec=timeout_sec,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def upgrade_ollama_with_winget(timeout_sec: int = 900) -> bool:
    winget = shutil.which("winget")
    if not winget:
        return False
    try:
        result = _run_cli(
            [
                winget,
                "upgrade",
                "--id",
                OLLAMA_WINGET_ID,
                "-e",
                "--accept-source-agreements",
                "--accept-package-agreements",
            ],
            timeout_sec=timeout_sec,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    if result.returncode == 0:
        return True
    return "no available upgrade" in combined_output


def download_ollama_installer(
    download_url: str = OLLAMA_DOWNLOAD_URL,
    progress: Callable[[str], None] | None = None,
) -> str | None:
    installer_path = Path(tempfile.gettempdir()) / "OllamaSetup.exe"
    try:
        with urllib.request.urlopen(download_url, timeout=60) as response:
            total_text = response.headers.get("Content-Length", "")
            total = int(total_text) if total_text.isdigit() else 0
            completed = 0
            last_bucket = -1
            with installer_path.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    completed += len(chunk)
                    if progress and total > 0:
                        percent = max(0, min(100, int((completed / total) * 100)))
                        bucket = percent // 5
                        if bucket != last_bucket:
                            progress(
                                "Ollama installer download "
                                f"{percent}% ({_format_bytes(completed)} / "
                                f"{_format_bytes(total)})"
                            )
                            last_bucket = bucket
                    elif progress and completed // (10 * 1024 * 1024) > last_bucket:
                        progress(
                            "Ollama installer download "
                            f"({_format_bytes(completed)} received)"
                        )
                        last_bucket = completed // (10 * 1024 * 1024)
            if progress:
                if total > 0:
                    progress(
                        "Ollama installer download 100% "
                        f"({_format_bytes(completed)} / {_format_bytes(total)})"
                    )
                else:
                    progress(
                        "Ollama installer download finished "
                        f"({_format_bytes(completed)} received)"
                    )
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
            installer_path = download_ollama_installer(progress=emit)
            if not installer_path:
                return {"ok": False, "error": "Ollama installer download failed."}
            emit("Starting Ollama installer. Approve Windows permission prompts if shown.")
            if not run_ollama_installer(installer_path):
                return {"ok": False, "error": "Ollama installer could not be started."}
        emit("Waiting for Ollama installation to become ready.")
        if not wait_for_ollama_ready(timeout_sec=300, base_url=base_url):
            return {"ok": False, "error": "Ollama was not ready after installation."}
    else:
        installed_version = get_ollama_version()
        latest_version = get_latest_ollama_version_from_winget()
        if installed_version:
            emit(f"Installed Ollama version: {installed_version}")
        if latest_version:
            emit(f"Latest Ollama version from winget: {latest_version}")
        if (
            installed_version
            and latest_version
            and _compare_versions(installed_version, latest_version) < 0
        ):
            emit("Updating Ollama to the latest available version.")
            if not upgrade_ollama_with_winget():
                emit("Ollama update could not be completed with winget.")
        elif latest_version:
            emit("Ollama is already up to date.")

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
        pull_result = pull_model(selected_model, base_url=base_url, progress=emit)
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
