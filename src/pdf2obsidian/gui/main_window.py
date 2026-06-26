from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pdf2obsidian.core.ai.ollama_client import (
    DEFAULT_BASE_URL,
    DEFAULT_RECOMMENDED_MODEL,
    check_ollama_update_status,
    ensure_ollama_ready_and_model,
    is_ollama_installed,
    is_ollama_running,
    list_models,
    pull_model,
    select_best_available_model,
    start_ollama_server,
)
from pdf2obsidian.core.converter import ConversionOptions, convert_files
from pdf2obsidian.utils.paths import is_supported

APP_STYLE = """
QMainWindow,
QWidget {
    background: #0f141a;
    color: #f3f5f7;
    font-size: 12px;
}
QLabel#appTitle {
    font-size: 21px;
    font-weight: 700;
}
QLabel#appSubtitle,
QLabel#fieldHint,
QLabel#footerLabel {
    color: #a9b4c0;
}
QLabel#logoBadge {
    background: #1c2733;
    border: 1px solid #33465a;
    border-radius: 8px;
    color: #f3f5f7;
    font-size: 14px;
    font-weight: 700;
    padding: 8px 9px;
}
QFrame#inputCard,
QFrame#conversionCard,
QFrame#aiCard,
QFrame#runCard,
QFrame#logCard {
    background: #151a20;
    border: 1px solid #2b3642;
    border-radius: 8px;
}
QFrame#inputCard {
    border-color: #2563eb;
}
QFrame#conversionCard {
    border-color: #238636;
}
QFrame#aiCard {
    border-color: #b45309;
}
QFrame#runCard {
    border-color: #7c3aed;
}
QLabel#inputTitle {
    color: #58a6ff;
    font-size: 14px;
    font-weight: 700;
}
QLabel#conversionTitle {
    color: #57d16d;
    font-size: 14px;
    font-weight: 700;
}
QLabel#aiTitle {
    color: #fb923c;
    font-size: 14px;
    font-weight: 700;
}
QLabel#runTitle {
    color: #a78bfa;
    font-size: 14px;
    font-weight: 700;
}
QLabel#numberBadge {
    background: #2563eb;
    border-radius: 14px;
    color: white;
    font-weight: 700;
    min-height: 28px;
    min-width: 28px;
}
QLabel#fieldLabel {
    color: #f3f5f7;
    font-weight: 600;
}
QLabel#pathValue,
QLabel#statusValue,
QLabel#aiStatusHint,
QLabel#hintBox {
    background: #11161c;
    border: 1px solid #303a45;
    border-radius: 6px;
    padding: 6px;
}
QLabel#hintBox {
    color: #c9d1d9;
}
QLabel#aiStatusHint {
    color: #c9d1d9;
}
QListWidget,
QTextEdit,
QComboBox {
    background: #11161c;
    border: 1px solid #303a45;
    border-radius: 6px;
    color: #f3f5f7;
    padding: 4px 6px;
}
QListWidget::item {
    padding: 3px;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QPushButton {
    background: #1c232c;
    border: 1px solid #374151;
    border-radius: 6px;
    color: #f3f5f7;
    padding: 5px 7px;
}
QPushButton:hover {
    background: #263241;
}
QPushButton:disabled {
    color: #687381;
    background: #151a20;
    border-color: #28313a;
}
QPushButton#primaryButton {
    background: #6d28d9;
    border-color: #8b5cf6;
    font-size: 14px;
    font-weight: 700;
    min-height: 32px;
}
QPushButton#primaryButton:hover {
    background: #7c3aed;
}
QPushButton#accentButton {
    background: #123b6d;
    border-color: #2563eb;
}
QPushButton#warningButton {
    background: #3b250f;
    border-color: #b45309;
}
QCheckBox {
    spacing: 8px;
}
QProgressBar {
    background: #11161c;
    border: 1px solid #303a45;
    border-radius: 6px;
    color: #f3f5f7;
    text-align: center;
    min-height: 18px;
}
QProgressBar::chunk {
    background: #7c3aed;
    border-radius: 6px;
}
"""

TRANSLATIONS = {
    "en": {
        "window_title": "PDF2Obsidian",
        "app_subtitle": "Local-first converter for Obsidian Markdown",
        "language": "Language",
        "input_files_title": "1. Input Files",
        "conversion_settings_title": "2. Conversion Settings",
        "ai_settings_title": "3. AI Settings",
        "run_status_title": "4. Run / Status",
        "files": "Files",
        "select_files": "Select files",
        "remove_selected": "Remove",
        "clear": "Clear",
        "output_folder": "Output folder",
        "output_folder_hint": "Choose where converted files will be saved.",
        "select_output_folder": "Select output folder",
        "browse": "Browse",
        "mode": "Mode",
        "mode_pdf_image": "PDF/Image conversion",
        "mode_lecture": "Lecture reconstruction",
        "mode_auto": "Auto detect",
        "quality": "Quality",
        "pdf_output_markdown_image": "Markdown + Image",
        "pdf_output_webp_compression": "WebP Compression",
        "pdf_output": "PDF Output",
        "ai_mode": "AI Mode",
        "ai_basic": "Basic (No AI)",
        "ai_ollama": "Local AI (Ollama)",
        "ai_cloud_future": "Cloud AI (OpenAI Compatible) - Future",
        "output_mode": "Output Mode",
        "output_simple_note": "Simple Note - Future",
        "output_study_note": "Lecture Reconstruction MD",
        "output_ebook": "Ebook - Future",
        "output_executive_summary": "Executive Brief - Future",
        "output_language": "Output Language",
        "language_auto": "Same as source",
        "language_ko": "Korean",
        "language_en": "English",
        "keep_timestamps": "Keep timestamps",
        "generate_review_questions": "Generate review questions",
        "generate_checklist": "Generate checklist",
        "output_mode_hint": (
            "Output Mode works separately from AI Mode. Default is Lecture Reconstruction MD."
        ),
        "ollama_status": "Ollama status",
        "ollama_not_checked": "Not checked",
        "ollama_running": "Running",
        "ollama_not_detected": "Not detected",
        "ollama_installing": "Installing...",
        "ollama_model": "Model",
        "ollama_endpoint": "Endpoint",
        "installed_models": "Installed",
        "no_installed_models_choice": "No installed models detected",
        "check_ollama": "Check Ollama",
        "check_ollama_latest": "Check Latest Version",
        "ollama_auto_install": "Auto Install Ollama",
        "refresh_ollama_models": "Refresh Models",
        "ollama_setup_guide": "Ollama Setup Guide",
        "open_ollama_download": "Open Download Page",
        "pull_model": "Pull Model",
        "ollama_pull_started": "Ollama model pull started: {model}",
        "ollama_pull_finished": "Ollama model pull finished: {message}",
        "ollama_models_refreshed": "Ollama models refreshed: {models}",
        "ollama_no_models": "No installed Ollama models were detected.",
        "ollama_setup_confirm_title": "Install Ollama automatically?",
        "ollama_setup_confirm_message": (
            "PDF2Obsidian will install Ollama using winget first. If winget fails, "
            "it will download and run the official Ollama installer.\n\n"
            "Windows may show a permission prompt. After installation, the selected "
            "model will be downloaded if it is missing.\n\n"
            "Continue?"
        ),
        "ollama_setup_started": "Ollama automatic setup started.",
        "ollama_setup_finished": "Ollama automatic setup finished: {message}",
        "ollama_version_check_started": "Checking Ollama latest version.",
        "ollama_version_check_result": (
            "Ollama version: installed={installed}, latest={latest}, update={update}"
        ),
        "ollama_model_required_title": "No installed Ollama model",
        "ollama_model_required_message": (
            "Refresh installed models or pull the recommended model before conversion."
        ),
        "ollama_guide_title": "Ollama setup guide",
        "ollama_guide_text": (
            "PDF2Obsidian works without Ollama.\n\n"
            "Use Ollama only when you choose Local AI (Ollama).\n\n"
            "Recommended beginner steps:\n"
            "1. Click Auto Install Ollama.\n"
            "2. Wait while Ollama and the selected model are installed.\n"
            "3. If automatic setup fails, click Open Download Page.\n"
            "4. Add a transcript file, choose Local AI (Ollama), "
            "choose Lecture Reconstruction MD, then start conversion.\n\n"
            "If Ollama is not detected, start Ollama and click Check Ollama again.\n"
            "Model files can be stored on another drive by setting OLLAMA_MODELS."
        ),
        "ai_basic_status": "Basic local rule-based mode. No AI, model, or internet is required.",
        "ai_ollama_status": "Local AI mode uses your local Ollama server only after you choose it.",
        "ai_cloud_status": "Reserved for a future optional cloud AI mode. Not implemented.",
        "ollama_hint": (
            "Auto Install runs only after you click the button and confirm the setup prompt."
        ),
        "progress": "Progress",
        "status": "Status",
        "status_ready": "Ready.",
        "status_running": "Conversion is running.",
        "status_conversion_progress": "Conversion progress: {percent}%",
        "status_finished": "Conversion finished. Output folder is ready.",
        "status_failed": "Conversion failed. Open the log for details.",
        "status_ollama_setup": "Ollama setup is running.",
        "status_ollama_pull": "Ollama model pull is running.",
        "show_log": "Show Log",
        "hide_log": "Hide Log",
        "ocr": "Use OCR when available",
        "separator": "Insert page separators",
        "transcript_preserve": "Transcript detail",
        "preserve_low": "Low",
        "preserve_medium": "Medium",
        "preserve_high": "High",
        "output": "Output",
        "format_detailed": "Detailed lecture note",
        "format_clean": "Clean transcript",
        "format_study_note": "Study note",
        "format_ebook_draft": "Ebook draft",
        "format_obsidian_moc": "Obsidian MOC",
        "log": "Log",
        "start": "Start conversion",
        "open_output": "Open output folder",
        "author_footer": "Created by Cho Kyusong | MIT License",
        "drop_tooltip": "Drop PDF, image, or transcript files here.",
        "file_dialog_title": "Select files",
        "file_dialog_filter": (
            "Supported files (*.pdf *.png *.jpg *.jpeg *.webp *.srt *.vtt *.txt *.md)"
        ),
        "output_dialog_title": "Select output folder",
        "no_files_title": "No files",
        "no_files_message": "Add at least one file first.",
        "skipped": "Skipped unsupported file: {name}",
        "starting": "Starting conversion.",
        "finished": "Conversion finished.",
        "failed_title": "Conversion failed",
        "error": "Error: {message}",
    },
    "ko": {
        "window_title": "PDF2Obsidian",
        "app_subtitle": "Obsidian Markdown용 로컬 우선 변환기",
        "language": "언어",
        "input_files_title": "1. Input Files",
        "conversion_settings_title": "2. Conversion Settings",
        "ai_settings_title": "3. AI Settings",
        "run_status_title": "4. Run / Status",
        "files": "파일",
        "select_files": "파일 선택",
        "remove_selected": "선택 제거",
        "clear": "전체 지우기",
        "output_folder": "출력 폴더",
        "output_folder_hint": "변환된 파일이 저장될 폴더를 선택하세요.",
        "select_output_folder": "출력 폴더 선택",
        "browse": "찾아보기",
        "mode": "변환 모드",
        "mode_pdf_image": "PDF/이미지 변환",
        "mode_lecture": "강의 자막 상세 정리",
        "mode_auto": "자동 판별",
        "quality": "이미지 품질",
        "pdf_output_markdown_image": "Markdown + Image",
        "pdf_output_webp_compression": "WebP 압축",
        "pdf_output": "PDF 출력",
        "ai_mode": "AI Mode",
        "ai_basic": "Basic (No AI)",
        "ai_ollama": "Local AI (Ollama)",
        "ai_cloud_future": "Cloud AI (OpenAI Compatible) - Future",
        "output_mode": "Output Mode",
        "output_simple_note": "Simple Note - 향후",
        "output_study_note": "강의 재구성 MD",
        "output_ebook": "Ebook - 향후",
        "output_executive_summary": "검토 브리프 - 향후",
        "output_language": "출력 언어",
        "language_auto": "원문 언어 유지",
        "language_ko": "한국어",
        "language_en": "영어",
        "keep_timestamps": "타임스탬프 유지",
        "generate_review_questions": "복습 질문 생성",
        "generate_checklist": "체크리스트 생성",
        "output_mode_hint": (
            "Output Mode는 AI Mode와 별도로 동작합니다. 기본값은 강의 재구성 MD입니다."
        ),
        "ollama_status": "Ollama 상태",
        "ollama_not_checked": "미확인",
        "ollama_running": "실행 중",
        "ollama_not_detected": "감지 안 됨",
        "ollama_installing": "설치 중...",
        "ollama_model": "모델",
        "ollama_endpoint": "Endpoint",
        "installed_models": "설치된 모델",
        "no_installed_models_choice": "설치된 모델 없음",
        "check_ollama": "Ollama 확인",
        "check_ollama_latest": "최신 버전 확인",
        "ollama_auto_install": "Ollama 자동 설치",
        "refresh_ollama_models": "모델 새로고침",
        "ollama_setup_guide": "Ollama 설정 가이드",
        "open_ollama_download": "다운로드 페이지 열기",
        "pull_model": "모델 Pull",
        "ollama_pull_started": "Ollama 모델 pull 시작: {model}",
        "ollama_pull_finished": "Ollama 모델 pull 완료: {message}",
        "ollama_models_refreshed": "Ollama 모델 목록 새로고침 완료: {models}",
        "ollama_no_models": "설치된 Ollama 모델이 없습니다.",
        "ollama_setup_confirm_title": "Ollama를 자동 설치할까요?",
        "ollama_setup_confirm_message": (
            "PDF2Obsidian이 먼저 winget으로 Ollama 설치를 시도합니다. winget이 실패하면 "
            "공식 Ollama 설치 파일을 다운로드해 실행합니다.\n\n"
            "Windows 권한 확인 창이 표시될 수 있습니다. 설치 후 선택한 모델이 없으면 "
            "자동으로 다운로드합니다.\n\n"
            "계속하시겠습니까?"
        ),
        "ollama_setup_started": "Ollama 자동 설치를 시작합니다.",
        "ollama_setup_finished": "Ollama 자동 설치 완료: {message}",
        "ollama_version_check_started": "Ollama 최신 버전을 확인합니다.",
        "ollama_version_check_result": (
            "Ollama 버전: 설치됨={installed}, 최신={latest}, 업데이트={update}"
        ),
        "ollama_model_required_title": "설치된 Ollama 모델 없음",
        "ollama_model_required_message": (
            "변환 전에 설치 모델을 새로고침하거나 추천 모델을 Pull 하세요."
        ),
        "ollama_guide_title": "Ollama 설정 가이드",
        "ollama_guide_text": (
            "PDF2Obsidian은 Ollama 없이도 동작합니다.\n\n"
            "Ollama는 Local AI (Ollama)를 선택할 때만 필요합니다.\n\n"
            "초보자용 순서:\n"
            "1. Ollama 자동 설치를 누릅니다.\n"
            "2. Ollama와 선택 모델 설치가 끝날 때까지 기다립니다.\n"
            "3. 자동 설치가 실패하면 다운로드 페이지 열기를 누릅니다.\n"
            "4. 자막 파일을 추가하고 AI Mode를 Local AI (Ollama), "
            "Output Mode를 강의 재구성 MD로 둔 뒤 변환을 시작합니다.\n\n"
            "Ollama가 감지되지 않으면 Ollama를 실행한 뒤 다시 확인하세요.\n"
            "모델 파일은 OLLAMA_MODELS 환경 변수로 다른 드라이브에 저장할 수 있습니다."
        ),
        "ai_basic_status": "로컬 규칙 기반 모드입니다. AI, 모델, 인터넷이 필요 없습니다.",
        "ai_ollama_status": "Local AI는 사용자가 선택했을 때만 로컬 Ollama 서버를 사용합니다.",
        "ai_cloud_status": "향후 선택형 Cloud AI를 위한 예약 옵션입니다. 아직 구현되지 않았습니다.",
        "ollama_hint": "자동 설치는 사용자가 버튼을 누르고 확인했을 때만 실행됩니다.",
        "progress": "진행률",
        "status": "상태",
        "status_ready": "대기 중입니다.",
        "status_running": "변환 중입니다.",
        "status_conversion_progress": "변환 진행률: {percent}%",
        "status_finished": "변환이 완료되었습니다. 출력 폴더를 열 수 있습니다.",
        "status_failed": "변환에 실패했습니다. 로그를 확인하세요.",
        "status_ollama_setup": "Ollama 설정을 진행 중입니다.",
        "status_ollama_pull": "Ollama 모델을 다운로드 중입니다.",
        "show_log": "로그 보기",
        "hide_log": "로그 숨기기",
        "ocr": "가능하면 OCR 사용",
        "separator": "페이지 구분선 삽입",
        "transcript_preserve": "자막 상세도",
        "preserve_low": "낮음",
        "preserve_medium": "중간",
        "preserve_high": "높음",
        "output": "출력 형식",
        "format_detailed": "상세 강의 노트",
        "format_clean": "정리된 자막",
        "format_study_note": "학습 노트",
        "format_ebook_draft": "전자책 원고",
        "format_obsidian_moc": "Obsidian MOC",
        "log": "로그",
        "start": "변환 시작",
        "open_output": "출력 폴더 열기",
        "author_footer": "Created by Cho Kyusong | MIT License",
        "drop_tooltip": "PDF, 이미지, 자막 파일을 여기에 드래그하세요.",
        "file_dialog_title": "파일 선택",
        "file_dialog_filter": "지원 파일 (*.pdf *.png *.jpg *.jpeg *.webp *.srt *.vtt *.txt *.md)",
        "output_dialog_title": "출력 폴더 선택",
        "no_files_title": "파일 없음",
        "no_files_message": "파일을 하나 이상 추가하세요.",
        "skipped": "지원하지 않는 파일 건너뜀: {name}",
        "starting": "변환을 시작합니다.",
        "finished": "변환이 완료되었습니다.",
        "failed_title": "변환 실패",
        "error": "오류: {message}",
    },
}


class OllamaPullWorker(QThread):
    progress_message = Signal(str)
    finished_message = Signal(str)

    def __init__(self, model: str) -> None:
        super().__init__()
        self.model = model

    def run(self) -> None:
        result = pull_model(self.model, progress=self.progress_message.emit)
        if result.get("ok"):
            self.finished_message.emit("ok")
        else:
            self.finished_message.emit(str(result.get("error", "unknown error")))


class OllamaSetupWorker(QThread):
    log_message = Signal(str)
    finished_setup = Signal(bool, str, str)

    def __init__(self, model: str) -> None:
        super().__init__()
        self.model = model

    def run(self) -> None:
        result = ensure_ollama_ready_and_model(self.model, log=self.log_message.emit)
        if result.get("ok"):
            model = str(result.get("model", self.model))
            self.finished_setup.emit(True, model, "ok")
        else:
            self.finished_setup.emit(False, self.model, str(result.get("error", "unknown error")))


class OllamaVersionCheckWorker(QThread):
    finished_check = Signal(dict)

    def run(self) -> None:
        self.finished_check.emit(check_ollama_update_status())


class DropListWidget(QListWidget):
    files_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(130)
        self.setToolTip("Drop PDF, image, or transcript files here.")

    def dragEnterEvent(self, event) -> None:  # noqa: ANN001
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: ANN001
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # noqa: ANN001
        paths = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(url.toLocalFile())
        if paths:
            self.files_dropped.emit(paths)


class ConversionWorker(QThread):
    log_message = Signal(str)
    progress_changed = Signal(int)
    finished_success = Signal(str)
    failed = Signal(str)

    def __init__(self, files: list[str], options: ConversionOptions) -> None:
        super().__init__()
        self.files = files
        self.options = options

    def run(self) -> None:
        try:
            total = len(self.files)

            def progress(done: int, count: int) -> None:
                percent = int((done / count) * 100) if count else 0
                self.progress_changed.emit(percent)

            convert_files(
                self.files,
                self.options,
                log=self.log_message.emit,
                progress=progress,
            )
            self.progress_changed.emit(100)
            self.finished_success.emit(str(self.options.output_root))
            self.log_message.emit(f"Completed {total} file(s).")
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF2Obsidian")
        self.resize(1200, 720)
        self.setMinimumSize(1100, 650)
        self.setStyleSheet(APP_STYLE)
        self.settings = QSettings("PDF2Obsidian", "PDF2Obsidian")
        self.worker: ConversionWorker | None = None
        self.ollama_setup_worker: OllamaSetupWorker | None = None
        self.ollama_version_check_worker: OllamaVersionCheckWorker | None = None
        self.last_output_folder = Path.cwd() / "output"
        self.language = "en"
        self.log_expanded = True

        self.file_list = DropListWidget()
        self.file_list.files_dropped.connect(self.add_files)
        self.file_list.setMinimumHeight(92)

        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("한국어", "ko")
        self.language_combo.currentIndexChanged.connect(self.apply_language)

        self.output_label = QLabel(str(self.last_output_folder))
        self.output_label.setObjectName("pathValue")
        self.output_label.setMinimumWidth(0)
        self.output_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["60", "75", "90"])
        self.quality_combo.setCurrentText("75")

        self.mode_combo = QComboBox()
        self.mode_combo.currentIndexChanged.connect(self.update_output_options)

        self.pdf_output_combo = QComboBox()
        self.ocr_checkbox = QCheckBox()
        self.separator_checkbox = QCheckBox()
        self.separator_checkbox.setChecked(True)

        self.preserve_combo = QComboBox()
        self.ai_mode_combo = QComboBox()
        self.ai_mode_combo.currentIndexChanged.connect(self.update_output_options)
        self.output_mode_combo = QComboBox()
        self.output_language_combo = QComboBox()

        self.ollama_status_value = QLabel()
        self.ollama_status_value.setObjectName("statusValue")
        self.ollama_endpoint_value = QLabel(DEFAULT_BASE_URL)
        self.ollama_endpoint_value.setObjectName("statusValue")
        self.ollama_installed_models_value = QLabel("-")
        self.ollama_installed_models_value.setObjectName("statusValue")
        self.ollama_installed_models_value.setMinimumWidth(0)
        self.ollama_installed_models_value.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Fixed,
        )
        self.ollama_installed_models_value.setWordWrap(True)
        self.ollama_model_combo = QComboBox()
        self.ollama_model_combo.setEditable(False)
        self.ollama_check_button = QPushButton()
        self.ollama_check_button.clicked.connect(self.check_ollama_status)
        self.ollama_latest_check_button = QPushButton()
        self.ollama_latest_check_button.clicked.connect(self.check_ollama_latest_version)
        self.ollama_auto_install_button = QPushButton()
        self.ollama_auto_install_button.clicked.connect(self.start_ollama_auto_install)
        self.ollama_refresh_models_button = QPushButton()
        self.ollama_refresh_models_button.clicked.connect(self.refresh_ollama_model_selector)
        self.ollama_guide_button = QPushButton()
        self.ollama_guide_button.clicked.connect(self.show_ollama_setup_guide)
        self.ollama_download_button = QPushButton()
        self.ollama_download_button.clicked.connect(self.open_ollama_download)
        self.ollama_pull_button = QPushButton()
        self.ollama_pull_button.clicked.connect(self.pull_selected_ollama_model)
        self.ollama_pull_worker: OllamaPullWorker | None = None

        self.keep_timestamps_checkbox = QCheckBox()
        self.keep_timestamps_checkbox.setChecked(False)
        self.review_questions_checkbox = QCheckBox()
        self.review_questions_checkbox.setChecked(False)
        self.checklist_checkbox = QCheckBox()
        self.checklist_checkbox.setChecked(False)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFormat("%p%")

        self.status_value_label = QLabel()
        self.status_value_label.setObjectName("statusValue")
        self.status_value_label.setWordWrap(True)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(84)
        self.log_area.setMaximumHeight(150)

        self.open_output_button = QPushButton()
        self.open_output_button.setEnabled(False)
        self.open_output_button.clicked.connect(self.open_output_folder)
        self.log_toggle_button = QPushButton()
        self.log_toggle_button.clicked.connect(self.toggle_log_visibility)
        self.author_footer_label = QLabel()
        self.author_footer_label.setObjectName("footerLabel")

        self._build_layout()
        self.apply_language()

    def _build_layout(self) -> None:
        self._configure_compact_widgets()

        self.add_files_button = QPushButton()
        self.add_files_button.clicked.connect(self.select_files)
        self.add_files_button.setObjectName("accentButton")
        self.remove_button = QPushButton()
        self.remove_button.clicked.connect(self.remove_selected_files)
        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(self.file_list.clear)
        for button in (self.add_files_button, self.remove_button, self.clear_button):
            button.setMinimumWidth(0)
            button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

        file_buttons = QGridLayout()
        file_buttons.setHorizontalSpacing(8)
        file_buttons.setVerticalSpacing(6)
        file_buttons.addWidget(self.add_files_button, 0, 0)
        file_buttons.addWidget(self.remove_button, 0, 1)
        file_buttons.addWidget(self.clear_button, 0, 2)

        self.output_button = QPushButton()
        self.output_button.clicked.connect(self.select_output_folder)
        self.output_button.setObjectName("accentButton")
        self.output_button.setMinimumWidth(0)

        self.app_title_label = QLabel()
        self.app_title_label.setObjectName("appTitle")
        self.app_subtitle_label = QLabel()
        self.app_subtitle_label.setObjectName("appSubtitle")
        self.logo_label = QLabel("P2O")
        self.logo_label.setObjectName("logoBadge")
        self.logo_label.setAlignment(Qt.AlignCenter)

        self.language_label = QLabel()
        self.mode_label = QLabel()
        self.quality_label = QLabel()
        self.pdf_output_label = QLabel()
        self.transcript_preserve_label = QLabel()
        self.ai_mode_label = QLabel()
        self.output_mode_label = QLabel()
        self.output_language_label = QLabel()
        self.ollama_status_label = QLabel()
        self.ollama_model_label = QLabel()
        self.ollama_endpoint_label = QLabel()
        self.ollama_installed_models_label = QLabel()
        self.output_folder_label = QLabel()
        self.output_folder_hint_label = QLabel()
        self.output_folder_hint_label.setObjectName("fieldHint")
        self.output_mode_hint_label = QLabel()
        self.output_mode_hint_label.setObjectName("hintBox")
        self.output_mode_hint_label.setWordWrap(True)
        self.output_mode_hint_label.setMaximumHeight(72)
        self.ai_status_hint_label = QLabel()
        self.ai_status_hint_label.setObjectName("aiStatusHint")
        self.ai_status_hint_label.setWordWrap(True)
        self.ai_status_hint_label.setMaximumHeight(54)
        self.ollama_hint_label = QLabel()
        self.ollama_hint_label.setObjectName("hintBox")
        self.ollama_hint_label.setWordWrap(True)
        self.ollama_hint_label.setMaximumHeight(46)
        self.progress_label = QLabel()
        self.status_label = QLabel()

        self.start_button = QPushButton()
        self.start_button.clicked.connect(self.start_conversion)
        self.start_button.setObjectName("primaryButton")
        self.start_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ollama_auto_install_button.setObjectName("warningButton")

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(1)
        title_layout.addWidget(self.app_title_label)
        title_layout.addWidget(self.app_subtitle_label)
        header_layout.addWidget(self.logo_label)
        header_layout.addLayout(title_layout, stretch=1)
        header_layout.addWidget(self.language_label)
        header_layout.addWidget(self.language_combo)

        self.files_label = QLabel()
        self.log_label = QLabel()
        input_card = self._create_card("inputCard", self.files_label, "inputTitle")
        input_layout = input_card.layout()
        input_layout.addWidget(self.file_list)
        input_layout.addLayout(file_buttons)
        self.output_folder_label.setObjectName("fieldLabel")
        input_layout.addWidget(self.output_folder_label)
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_label, stretch=1)
        output_layout.addWidget(self.output_button)
        input_layout.addLayout(output_layout)
        input_layout.addWidget(self.output_folder_hint_label)

        self.conversion_title_label = QLabel()
        conversion_card = self._create_card(
            "conversionCard",
            self.conversion_title_label,
            "conversionTitle",
        )
        conversion_layout = conversion_card.layout()
        settings_grid = QGridLayout()
        settings_grid.setHorizontalSpacing(10)
        settings_grid.setVerticalSpacing(7)
        self._add_setting_row(settings_grid, 0, self.mode_label, self.mode_combo)
        self._add_setting_row(settings_grid, 1, self.pdf_output_label, self.pdf_output_combo)
        self._add_setting_row(settings_grid, 2, self.quality_label, self.quality_combo)
        self._add_setting_row(settings_grid, 3, self.transcript_preserve_label, self.preserve_combo)
        self._add_setting_row(settings_grid, 4, self.output_mode_label, self.output_mode_combo)
        self._add_setting_row(
            settings_grid,
            5,
            self.output_language_label,
            self.output_language_combo,
        )
        checkbox_layout = QGridLayout()
        checkbox_layout.setHorizontalSpacing(12)
        checkbox_layout.setVerticalSpacing(6)
        checkbox_layout.addWidget(self.separator_checkbox, 0, 0)
        checkbox_layout.addWidget(self.ocr_checkbox, 0, 1)
        settings_grid.addLayout(checkbox_layout, 6, 0, 1, 2)
        settings_grid.setColumnStretch(1, 1)
        conversion_layout.addLayout(settings_grid)
        conversion_layout.addWidget(self.output_mode_hint_label)

        self.ai_title_label = QLabel()
        ai_card = self._create_card("aiCard", self.ai_title_label, "aiTitle")
        ai_layout = ai_card.layout()
        ai_grid = QGridLayout()
        ai_grid.setHorizontalSpacing(10)
        ai_grid.setVerticalSpacing(7)
        self._add_setting_row(ai_grid, 0, self.ai_mode_label, self.ai_mode_combo)
        ai_grid.addWidget(self.ai_status_hint_label, 1, 0, 1, 2)
        ai_grid.setColumnStretch(1, 1)
        ai_layout.addLayout(ai_grid)
        self.ollama_details_widget = QWidget()
        ollama_details_layout = QGridLayout(self.ollama_details_widget)
        ollama_details_layout.setContentsMargins(0, 0, 0, 0)
        ollama_details_layout.setHorizontalSpacing(10)
        ollama_details_layout.setVerticalSpacing(7)
        self._add_setting_row(
            ollama_details_layout,
            0,
            self.ollama_status_label,
            self.ollama_status_value,
        )
        self._add_setting_row(
            ollama_details_layout,
            1,
            self.ollama_endpoint_label,
            self.ollama_endpoint_value,
        )
        self._add_setting_row(
            ollama_details_layout,
            2,
            self.ollama_installed_models_label,
            self.ollama_installed_models_value,
        )
        self._add_setting_row(
            ollama_details_layout,
            3,
            self.ollama_model_label,
            self.ollama_model_combo,
        )
        self.ollama_action_widget = QWidget()
        ollama_action_layout = QGridLayout(self.ollama_action_widget)
        ollama_action_layout.setContentsMargins(0, 0, 0, 0)
        ollama_action_layout.setHorizontalSpacing(8)
        ollama_action_layout.setVerticalSpacing(6)
        ollama_action_layout.addWidget(self.ollama_check_button, 0, 0)
        ollama_action_layout.addWidget(self.ollama_refresh_models_button, 0, 1)
        ollama_action_layout.addWidget(self.ollama_latest_check_button, 1, 0)
        ollama_action_layout.addWidget(self.ollama_pull_button, 1, 1)
        ollama_action_layout.addWidget(self.ollama_auto_install_button, 2, 0)
        ollama_action_layout.addWidget(self.ollama_guide_button, 2, 1)
        ollama_action_layout.addWidget(self.ollama_download_button, 3, 0, 1, 2)
        ollama_details_layout.addWidget(self.ollama_action_widget, 0, 2, 4, 1)
        ollama_details_layout.addWidget(self.ollama_hint_label, 4, 0, 1, 3)
        ollama_details_layout.setColumnStretch(1, 1)
        ollama_details_layout.setColumnStretch(2, 1)
        ai_layout.addWidget(self.ollama_details_widget)

        self.run_title_label = QLabel()
        run_card = self._create_card("runCard", self.run_title_label, "runTitle")
        run_card.setMaximumHeight(220)
        run_layout = run_card.layout()
        run_layout.addWidget(self.start_button)
        self.progress_label.setObjectName("fieldLabel")
        self.status_label.setObjectName("fieldLabel")
        run_layout.addWidget(self.progress_label)
        run_layout.addWidget(self.progress_bar)
        run_layout.addWidget(self.status_label)
        run_layout.addWidget(self.status_value_label)
        run_actions = QHBoxLayout()
        run_actions.addStretch(1)
        run_actions.addWidget(self.open_output_button)
        run_layout.addLayout(run_actions)

        self.log_card = self._create_card("logCard", self.log_label, "fieldLabel")
        self.log_card.setMaximumHeight(220)
        log_layout = self.log_card.layout()
        log_layout.addWidget(self.log_area)
        self.log_card.setVisible(True)

        workflow_layout = QGridLayout()
        workflow_layout.setHorizontalSpacing(12)
        workflow_layout.setVerticalSpacing(10)
        workflow_layout.addWidget(input_card, 0, 0)
        workflow_layout.addWidget(conversion_card, 0, 1)
        workflow_layout.addWidget(ai_card, 0, 2)
        workflow_layout.addWidget(run_card, 1, 0)
        workflow_layout.addWidget(self.log_card, 1, 1, 1, 2)
        workflow_layout.setColumnStretch(0, 2)
        workflow_layout.setColumnStretch(1, 2)
        workflow_layout.setColumnStretch(2, 3)
        workflow_layout.setRowMinimumHeight(0, 305)
        workflow_layout.setRowMinimumHeight(1, 205)
        workflow_layout.setRowStretch(0, 4)
        workflow_layout.setRowStretch(1, 1)

        footer_layout = QHBoxLayout()
        footer_layout.addWidget(self.author_footer_label)
        footer_layout.addStretch(1)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 8)
        layout.setSpacing(8)
        layout.addLayout(header_layout)
        layout.addLayout(workflow_layout)
        layout.addLayout(footer_layout)

        content = QWidget()
        content.setMinimumWidth(0)
        content.setLayout(layout)
        self.setCentralWidget(content)

    def _create_card(self, object_name: str, title_label: QLabel, title_object: str) -> QFrame:
        card = QFrame()
        card.setObjectName(object_name)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)
        title_label.setObjectName(title_object)
        title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        title_row_widget = QWidget()
        title_row_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        title_row = QHBoxLayout(title_row_widget)
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(0)
        title_row.addWidget(title_label)
        title_row.addStretch(1)
        layout.addWidget(title_row_widget)
        return card

    def _add_setting_row(
        self,
        grid: QGridLayout,
        row: int,
        label: QLabel,
        widget: QWidget,
    ) -> None:
        label.setObjectName("fieldLabel")
        grid.addWidget(label, row, 0)
        grid.addWidget(widget, row, 1)

    def _configure_compact_widgets(self) -> None:
        combos = [
            self.language_combo,
            self.quality_combo,
            self.mode_combo,
            self.pdf_output_combo,
            self.preserve_combo,
            self.ai_mode_combo,
            self.output_mode_combo,
            self.output_language_combo,
            self.ollama_model_combo,
        ]
        for combo in combos:
            combo.setMinimumContentsLength(10)
            combo.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.ai_mode_combo.setMinimumContentsLength(14)
        self.output_mode_combo.setMinimumContentsLength(14)

    def tr(self, key: str, **kwargs: str) -> str:
        text = TRANSLATIONS[self.language][key]
        return text.format(**kwargs) if kwargs else text

    def _reset_combo_items(
        self,
        combo: QComboBox,
        items: list[tuple[str, str]],
        selected_data: str | None = None,
    ) -> None:
        combo.blockSignals(True)
        combo.clear()
        for label, data in items:
            combo.addItem(label, data)
        if selected_data is not None:
            for index in range(combo.count()):
                if combo.itemData(index) == selected_data:
                    combo.setCurrentIndex(index)
                    break
        combo.blockSignals(False)

    def apply_language(self) -> None:
        selected_language = self.language_combo.currentData()
        self.language = selected_language or "en"

        mode_value = self.mode_combo.currentData() or "auto"
        preserve_value = self.preserve_combo.currentData() or "high"
        pdf_output_value = self.pdf_output_combo.currentData() or "markdown_image"
        ai_mode_value = self.ai_mode_combo.currentData() or str(
            self.settings.value("ai_mode", "basic")
        )
        output_mode_value = self.output_mode_combo.currentData() or "study_note"
        output_language_value = self.output_language_combo.currentData() or "auto"

        self.setWindowTitle(self.tr("window_title"))
        self.file_list.setToolTip(self.tr("drop_tooltip"))
        self.app_title_label.setText(self.tr("window_title"))
        self.app_subtitle_label.setText(self.tr("app_subtitle"))

        self.language_label.setText(self.tr("language"))
        self.files_label.setText(self.tr("input_files_title"))
        self.conversion_title_label.setText(self.tr("conversion_settings_title"))
        self.ai_title_label.setText(self.tr("ai_settings_title"))
        self.run_title_label.setText(self.tr("run_status_title"))
        self.add_files_button.setText(self.tr("select_files"))
        self.remove_button.setText(self.tr("remove_selected"))
        self.clear_button.setText(self.tr("clear"))
        self.output_folder_label.setText(self.tr("output_folder"))
        self.output_folder_hint_label.setText(self.tr("output_folder_hint"))
        self.output_button.setText(self.tr("browse"))
        self.mode_label.setText(self.tr("mode"))
        self.pdf_output_label.setText(self.tr("pdf_output"))
        self.quality_label.setText(self.tr("quality"))
        self.ocr_checkbox.setText(self.tr("ocr"))
        self.separator_checkbox.setText(self.tr("separator"))
        self.keep_timestamps_checkbox.setText(self.tr("keep_timestamps"))
        self.review_questions_checkbox.setText(self.tr("generate_review_questions"))
        self.checklist_checkbox.setText(self.tr("generate_checklist"))
        self.transcript_preserve_label.setText(self.tr("transcript_preserve"))
        self.ai_mode_label.setText(self.tr("ai_mode"))
        self.output_mode_label.setText(self.tr("output_mode"))
        self.output_language_label.setText(self.tr("output_language"))
        self.output_mode_hint_label.setText(self.tr("output_mode_hint"))
        self.ollama_status_label.setText(self.tr("ollama_status"))
        if not self.ollama_status_value.text():
            self.ollama_status_value.setText(self.tr("ollama_not_checked"))
        self.ollama_model_label.setText(self.tr("ollama_model"))
        self.ollama_endpoint_label.setText(self.tr("ollama_endpoint"))
        self.ollama_endpoint_value.setText(DEFAULT_BASE_URL)
        self.ollama_installed_models_label.setText(self.tr("installed_models"))
        self.ollama_check_button.setText(self.tr("check_ollama"))
        self.ollama_latest_check_button.setText(self.tr("check_ollama_latest"))
        self.ollama_auto_install_button.setText(self.tr("ollama_auto_install"))
        self.ollama_refresh_models_button.setText(self.tr("refresh_ollama_models"))
        self.ollama_guide_button.setText(self.tr("ollama_setup_guide"))
        self.ollama_download_button.setText(self.tr("open_ollama_download"))
        self.ollama_pull_button.setText(self.tr("pull_model"))
        self.ollama_hint_label.setText(self.tr("ollama_hint"))
        self.progress_label.setText(self.tr("progress"))
        self.status_label.setText(self.tr("status"))
        if not self.status_value_label.text():
            self.status_value_label.setText(self.tr("status_ready"))
        self.log_toggle_button.setText(
            self.tr("hide_log") if self.log_expanded else self.tr("show_log")
        )
        self.log_label.setText(self.tr("log"))
        self.start_button.setText(self.tr("start"))
        self.open_output_button.setText(self.tr("open_output"))
        self.author_footer_label.setText(self.tr("author_footer"))

        self._reset_combo_items(
            self.mode_combo,
            [
                (self.tr("mode_pdf_image"), "pdf_image"),
                (self.tr("mode_lecture"), "lecture"),
                (self.tr("mode_auto"), "auto"),
            ],
            mode_value,
        )
        self._reset_combo_items(
            self.preserve_combo,
            [
                (self.tr("preserve_low"), "low"),
                (self.tr("preserve_medium"), "medium"),
                (self.tr("preserve_high"), "high"),
            ],
            preserve_value,
        )
        self._reset_combo_items(
            self.pdf_output_combo,
            [
                (self.tr("pdf_output_markdown_image"), "markdown_image"),
                (self.tr("pdf_output_webp_compression"), "webp_compression"),
            ],
            pdf_output_value,
        )
        self._reset_combo_items(
            self.ai_mode_combo,
            [
                (self.tr("ai_basic"), "basic"),
                (self.tr("ai_ollama"), "ollama"),
                (self.tr("ai_cloud_future"), "cloud_future"),
            ],
            ai_mode_value,
        )
        self._reset_combo_items(
            self.output_mode_combo,
            [
                (self.tr("output_simple_note"), "simple_note"),
                (self.tr("output_study_note"), "study_note"),
                (self.tr("output_ebook"), "ebook"),
                (self.tr("output_executive_summary"), "executive_summary"),
            ],
            output_mode_value,
        )
        self._reset_combo_items(
            self.output_language_combo,
            [
                (self.tr("language_auto"), "auto"),
                (self.tr("language_ko"), "ko"),
                (self.tr("language_en"), "en"),
            ],
            output_language_value,
        )
        if self.ollama_model_combo.count() == 0 or self.ollama_model_combo.currentData() == "":
            self._show_no_installed_model_choice()
        self.update_output_options()

    def update_output_options(self) -> None:
        ai_mode = self.ai_mode_combo.currentData()
        is_ollama = ai_mode == "ollama"
        if ai_mode == "cloud_future":
            self.ai_status_hint_label.setText(self.tr("ai_cloud_status"))
        elif is_ollama:
            self.ai_status_hint_label.setText(self.tr("ai_ollama_status"))
        else:
            self.ai_status_hint_label.setText(self.tr("ai_basic_status"))

        self.ollama_details_widget.setVisible(is_ollama)
        self.ollama_status_label.setEnabled(is_ollama)
        self.ollama_status_value.setEnabled(is_ollama)
        self.ollama_model_label.setEnabled(is_ollama)
        self.ollama_model_combo.setEnabled(is_ollama)
        self.ollama_check_button.setEnabled(is_ollama)
        self.ollama_latest_check_button.setEnabled(is_ollama)
        self.ollama_auto_install_button.setEnabled(is_ollama)
        self.ollama_refresh_models_button.setEnabled(is_ollama)
        self.ollama_guide_button.setEnabled(is_ollama)
        self.ollama_download_button.setEnabled(is_ollama)
        self.ollama_pull_button.setEnabled(is_ollama)

    def check_ollama_status(self) -> None:
        if not is_ollama_running() and is_ollama_installed():
            start_ollama_server()

        if is_ollama_running():
            self.ollama_status_value.setText(self.tr("ollama_running"))
            self.status_value_label.setText(self.tr("ollama_running"))
            self.refresh_ollama_model_selector()
        else:
            self.ollama_status_value.setText(self.tr("ollama_not_detected"))
            self.ollama_installed_models_value.setText("-")
            self.status_value_label.setText(self.tr("ollama_not_detected"))

    def refresh_ollama_model_selector(self) -> None:
        current = self._selected_ollama_model()
        models = list_models()
        if not models:
            self._show_no_installed_model_choice()
            self.ollama_installed_models_value.setText("-")
            self.append_log(self.tr("ollama_no_models"))
            return

        selected = select_best_available_model(
            models,
            preferred_model=current,
        )
        self.ollama_model_combo.clear()
        for model in models:
            self.ollama_model_combo.addItem(model, model)
        self.ollama_model_combo.setCurrentText(selected)
        self.ollama_installed_models_value.setText(", ".join(models))
        self.settings.setValue("ollama_model", selected)
        self.append_log(self.tr("ollama_models_refreshed", models=", ".join(models)))

    def _show_no_installed_model_choice(self) -> None:
        self.ollama_model_combo.clear()
        self.ollama_model_combo.addItem(self.tr("no_installed_models_choice"), "")

    def _selected_ollama_model(self) -> str:
        model_data = self.ollama_model_combo.currentData()
        if isinstance(model_data, str) and model_data.strip():
            return model_data.strip()
        return ""

    def open_ollama_download(self) -> None:
        QDesktopServices.openUrl(QUrl("https://ollama.com/download"))

    def show_ollama_setup_guide(self) -> None:
        message = QMessageBox(self)
        message.setWindowTitle(self.tr("ollama_guide_title"))
        message.setText(self.tr("ollama_guide_text"))
        auto_button = message.addButton(self.tr("ollama_auto_install"), QMessageBox.ActionRole)
        manual_button = message.addButton(self.tr("open_ollama_download"), QMessageBox.ActionRole)
        check_button = message.addButton(self.tr("check_ollama"), QMessageBox.ActionRole)
        message.addButton(QMessageBox.Close)
        message.exec()

        clicked = message.clickedButton()
        if clicked == auto_button:
            self.start_ollama_auto_install()
        elif clicked == manual_button:
            self.open_ollama_download()
        elif clicked == check_button:
            self.check_ollama_status()

    def check_ollama_latest_version(self) -> None:
        self.append_log(self.tr("ollama_version_check_started"))
        self.status_value_label.setText(self.tr("ollama_version_check_started"))
        self.ollama_latest_check_button.setEnabled(False)
        self.ollama_version_check_worker = OllamaVersionCheckWorker()
        self.ollama_version_check_worker.finished_check.connect(
            self.ollama_latest_version_checked
        )
        self.ollama_version_check_worker.start()

    def ollama_latest_version_checked(self, result: dict) -> None:
        self.ollama_latest_check_button.setEnabled(
            self.ai_mode_combo.currentData() == "ollama"
        )
        installed = str(result.get("installed_version") or "unknown")
        latest = str(result.get("latest_version") or "unknown")
        update = "yes" if result.get("update_available") else "no"
        message = self.tr(
            "ollama_version_check_result",
            installed=installed,
            latest=latest,
            update=update,
        )
        self.status_value_label.setText(message)
        self.append_log(message)

    def start_ollama_auto_install(self) -> None:
        model = self._selected_ollama_model() or DEFAULT_RECOMMENDED_MODEL
        answer = QMessageBox.question(
            self,
            self.tr("ollama_setup_confirm_title"),
            self.tr("ollama_setup_confirm_message"),
        )
        if answer != QMessageBox.Yes:
            return

        self.append_log(self.tr("ollama_setup_started"))
        self.ollama_status_value.setText(self.tr("ollama_installing"))
        self.status_value_label.setText(self.tr("status_ollama_setup"))
        self.progress_bar.setValue(0)
        self._set_ollama_setup_controls_enabled(False)
        self.ollama_setup_worker = OllamaSetupWorker(model)
        self.ollama_setup_worker.log_message.connect(self.ollama_setup_progress_changed)
        self.ollama_setup_worker.finished_setup.connect(self.ollama_auto_install_finished)
        self.ollama_setup_worker.start()

    def ollama_setup_progress_changed(self, message: str) -> None:
        self.append_log(message)
        self.status_value_label.setText(message)
        self._set_progress_from_message(message)

    def _set_progress_from_message(self, message: str) -> None:
        percent_marker = message.find("%")
        if percent_marker < 1:
            return
        start = percent_marker
        while start > 0 and message[start - 1].isdigit():
            start -= 1
        if start == percent_marker:
            return
        self.progress_bar.setValue(int(message[start:percent_marker]))

    def _set_ollama_setup_controls_enabled(self, enabled: bool) -> None:
        is_ollama = self.ai_mode_combo.currentData() == "ollama"
        final_enabled = enabled and is_ollama
        self.ollama_check_button.setEnabled(final_enabled)
        self.ollama_latest_check_button.setEnabled(final_enabled)
        self.ollama_auto_install_button.setEnabled(final_enabled)
        self.ollama_refresh_models_button.setEnabled(final_enabled)
        self.ollama_guide_button.setEnabled(final_enabled)
        self.ollama_download_button.setEnabled(final_enabled)
        self.ollama_pull_button.setEnabled(final_enabled)
        self.ollama_model_combo.setEnabled(final_enabled)

    def ollama_auto_install_finished(self, ok: bool, model: str, message: str) -> None:
        self._set_ollama_setup_controls_enabled(True)
        self.append_log(self.tr("ollama_setup_finished", message=message))
        if ok:
            self.progress_bar.setValue(100)
            self.ollama_status_value.setText(self.tr("ollama_running"))
            self.status_value_label.setText(self.tr("ollama_setup_finished", message=message))
            self.ollama_model_combo.setCurrentText(model)
            self.settings.setValue("ollama_model", model)
            self.settings.setValue("ai_mode", "ollama")
            for index in range(self.ai_mode_combo.count()):
                if self.ai_mode_combo.itemData(index) == "ollama":
                    self.ai_mode_combo.setCurrentIndex(index)
                    break
            self.refresh_ollama_model_selector()
        else:
            self.ollama_status_value.setText(self.tr("ollama_not_detected"))
            self.status_value_label.setText(self.tr("status_failed"))
            self.set_log_visible(True)
            QMessageBox.warning(self, self.tr("ollama_guide_title"), message)

    def pull_selected_ollama_model(self) -> None:
        model = self._selected_ollama_model() or DEFAULT_RECOMMENDED_MODEL
        if not model:
            return
        self.settings.setValue("ollama_model", model)
        self.append_log(self.tr("ollama_pull_started", model=model))
        self.status_value_label.setText(self.tr("status_ollama_pull"))
        self.progress_bar.setValue(0)
        self.ollama_pull_button.setEnabled(False)
        self.ollama_pull_worker = OllamaPullWorker(model)
        self.ollama_pull_worker.progress_message.connect(self.ollama_pull_progress_changed)
        self.ollama_pull_worker.finished_message.connect(self.ollama_pull_finished)
        self.ollama_pull_worker.start()

    def ollama_pull_progress_changed(self, message: str) -> None:
        self.append_log(message)
        self.status_value_label.setText(message)
        self._set_progress_from_message(message)

    def ollama_pull_finished(self, message: str) -> None:
        self.ollama_pull_button.setEnabled(True)
        if message == "ok":
            self.progress_bar.setValue(100)
        self.append_log(self.tr("ollama_pull_finished", message=message))
        self.status_value_label.setText(self.tr("ollama_pull_finished", message=message))
        self.check_ollama_status()

    def select_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("file_dialog_title"),
            str(Path.cwd()),
            self.tr("file_dialog_filter"),
        )
        self.add_files(files)

    def add_files(self, files: list[str]) -> None:
        existing = {self.file_list.item(index).text() for index in range(self.file_list.count())}
        for file_path in files:
            path = Path(file_path)
            if path.is_file() and is_supported(path) and str(path) not in existing:
                self.file_list.addItem(str(path))
                existing.add(str(path))
            elif path.is_file():
                self.append_log(self.tr("skipped", name=path.name))

    def remove_selected_files(self) -> None:
        for item in self.file_list.selectedItems():
            row = self.file_list.row(item)
            self.file_list.takeItem(row)

    def select_output_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            self.tr("output_dialog_title"),
            str(self.last_output_folder),
        )
        if folder:
            self.last_output_folder = Path(folder)
            self.output_label.setText(str(self.last_output_folder))

    def _collect_files(self) -> list[str]:
        return [self.file_list.item(index).text() for index in range(self.file_list.count())]

    def start_conversion(self) -> None:
        files = self._collect_files()
        if not files:
            QMessageBox.warning(self, self.tr("no_files_title"), self.tr("no_files_message"))
            return

        selected_ai_mode = self.ai_mode_combo.currentData() or "basic"
        selected_ollama_model = self._selected_ollama_model()
        if selected_ai_mode == "ollama" and not selected_ollama_model:
            QMessageBox.warning(
                self,
                self.tr("ollama_model_required_title"),
                self.tr("ollama_model_required_message"),
            )
            return
        selected_ollama_model = selected_ollama_model or DEFAULT_RECOMMENDED_MODEL
        self.settings.setValue("ai_mode", selected_ai_mode)
        self.settings.setValue("ollama_model", selected_ollama_model)

        self.last_output_folder.mkdir(parents=True, exist_ok=True)
        options = ConversionOptions(
            output_root=self.last_output_folder,
            image_quality=int(self.quality_combo.currentText()),
            ocr_enabled=self.ocr_checkbox.isChecked(),
            include_page_separator=self.separator_checkbox.isChecked(),
            mode=self.mode_combo.currentData(),
            pdf_output_format=self.pdf_output_combo.currentData() or "markdown_image",
            transcript_preserve_level=self.preserve_combo.currentData(),
            transcript_output_format=self.output_mode_combo.currentData(),
            transcript_ai_mode=selected_ai_mode,
            transcript_output_mode=self.output_mode_combo.currentData() or "study_note",
            transcript_output_language=self.output_language_combo.currentData() or "auto",
            ollama_model=selected_ollama_model,
            transcript_keep_timestamps=False,
            transcript_review_questions=False,
            transcript_checklist=False,
        )

        self.progress_bar.setValue(0)
        self.open_output_button.setEnabled(False)
        self.status_value_label.setText(self.tr("status_running"))
        self.append_log(self.tr("starting"))
        self.worker = ConversionWorker(files, options)
        self.worker.log_message.connect(self.append_log)
        self.worker.progress_changed.connect(self.conversion_progress_changed)
        self.worker.finished_success.connect(self.conversion_finished)
        self.worker.failed.connect(self.conversion_failed)
        self.worker.start()

    def conversion_progress_changed(self, percent: int) -> None:
        self.progress_bar.setValue(percent)
        self.status_value_label.setText(self.tr("status_conversion_progress", percent=percent))

    def append_log(self, message: str) -> None:
        self.log_area.append(message)

    def toggle_log_visibility(self) -> None:
        self.set_log_visible(not self.log_expanded)

    def set_log_visible(self, visible: bool) -> None:
        self.log_expanded = visible
        self.log_card.setVisible(visible)
        self.log_toggle_button.setText(
            self.tr("hide_log") if self.log_expanded else self.tr("show_log")
        )

    def conversion_finished(self, output_folder: str) -> None:
        self.last_output_folder = Path(output_folder)
        self.open_output_button.setEnabled(True)
        self.status_value_label.setText(self.tr("status_finished"))
        self.append_log(self.tr("finished"))

    def conversion_failed(self, message: str) -> None:
        self.status_value_label.setText(self.tr("status_failed"))
        self.append_log(self.tr("error", message=message))
        self.set_log_visible(True)
        QMessageBox.critical(self, self.tr("failed_title"), message)

    def open_output_folder(self) -> None:
        self.last_output_folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_output_folder)))
