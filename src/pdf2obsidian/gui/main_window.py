from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pdf2obsidian.core.ai.ollama_client import is_ollama_running, list_models, pull_model
from pdf2obsidian.core.converter import ConversionOptions, convert_files
from pdf2obsidian.utils.paths import is_supported

TRANSLATIONS = {
    "en": {
        "window_title": "PDF2Obsidian",
        "language": "Language",
        "files": "Files",
        "select_files": "Select files",
        "remove_selected": "Remove selected",
        "clear": "Clear",
        "select_output_folder": "Select output folder",
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
        "ollama_status": "Ollama status",
        "ollama_not_checked": "Not checked",
        "ollama_running": "Running",
        "ollama_not_detected": "Not detected",
        "ollama_model": "Model",
        "check_ollama": "Check Ollama",
        "ollama_setup_guide": "Ollama Setup Guide",
        "open_ollama_download": "Open Ollama Download",
        "pull_model": "Pull Model",
        "ollama_pull_started": "Ollama model pull started: {model}",
        "ollama_pull_finished": "Ollama model pull finished: {message}",
        "ollama_guide_title": "Ollama setup guide",
        "ollama_guide_text": (
            "PDF2Obsidian works without Ollama.\n\n"
            "Use Ollama only when you choose Local AI (Ollama).\n\n"
            "Beginner steps:\n"
            "1. Click Open Ollama Download and install Ollama for Windows.\n"
            "2. Start Ollama from the Windows Start menu.\n"
            "3. Click Check Ollama. The status should become Running.\n"
            "4. Keep qwen2.5:3b selected and click Pull Model.\n"
            "5. Add a transcript file, choose Local AI (Ollama), "
            "choose Lecture Reconstruction MD, then start conversion.\n\n"
            "If Ollama is not detected, start Ollama and click Check Ollama again.\n"
            "Model files can be stored on another drive by setting OLLAMA_MODELS."
        ),
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
        "language": "언어",
        "files": "파일",
        "select_files": "파일 선택",
        "remove_selected": "선택 항목 제거",
        "clear": "전체 지우기",
        "select_output_folder": "출력 폴더 선택",
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
        "ollama_status": "Ollama 상태",
        "ollama_not_checked": "미확인",
        "ollama_running": "실행 중",
        "ollama_not_detected": "감지 안 됨",
        "ollama_model": "모델",
        "check_ollama": "Ollama 확인",
        "ollama_setup_guide": "Ollama 설정 가이드",
        "open_ollama_download": "Ollama 다운로드 열기",
        "pull_model": "모델 Pull",
        "ollama_pull_started": "Ollama 모델 pull 시작: {model}",
        "ollama_pull_finished": "Ollama 모델 pull 완료: {message}",
        "ollama_guide_title": "Ollama 설정 가이드",
        "ollama_guide_text": (
            "PDF2Obsidian은 Ollama 없이도 동작합니다.\n\n"
            "Ollama는 Local AI (Ollama)를 선택할 때만 필요합니다.\n\n"
            "초보자용 순서:\n"
            "1. Ollama 다운로드 열기를 눌러 Windows용 Ollama를 설치합니다.\n"
            "2. Windows 시작 메뉴에서 Ollama를 실행합니다.\n"
            "3. Ollama 확인을 누릅니다. 상태가 실행 중으로 바뀌어야 합니다.\n"
            "4. qwen2.5:3b 모델을 그대로 두고 모델 Pull을 누릅니다.\n"
            "5. 자막 파일을 추가하고 AI Mode를 Local AI (Ollama), "
            "Output Mode를 강의 재구성 MD로 둔 뒤 변환을 시작합니다.\n\n"
            "Ollama가 감지되지 않으면 Ollama를 실행한 뒤 다시 확인하세요.\n"
            "모델 파일은 OLLAMA_MODELS 환경 변수로 다른 드라이브에 저장할 수 있습니다."
        ),
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
    finished_message = Signal(str)

    def __init__(self, model: str) -> None:
        super().__init__()
        self.model = model

    def run(self) -> None:
        result = pull_model(self.model)
        if result.get("ok"):
            self.finished_message.emit("ok")
        else:
            self.finished_message.emit(str(result.get("error", "unknown error")))


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
        self.resize(820, 650)
        self.worker: ConversionWorker | None = None
        self.last_output_folder = Path.cwd() / "output"
        self.language = "en"

        self.file_list = DropListWidget()
        self.file_list.files_dropped.connect(self.add_files)

        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("한국어", "ko")
        self.language_combo.currentIndexChanged.connect(self.apply_language)

        self.output_label = QLabel(str(self.last_output_folder))
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
        self.ollama_model_combo = QComboBox()
        self.ollama_model_combo.setEditable(True)
        self.ollama_model_combo.addItems(["qwen2.5:3b", "llama3.2:3b", "qwen2.5:7b"])
        self.ollama_check_button = QPushButton()
        self.ollama_check_button.clicked.connect(self.check_ollama_status)
        self.ollama_guide_button = QPushButton()
        self.ollama_guide_button.clicked.connect(self.show_ollama_setup_guide)
        self.ollama_download_button = QPushButton()
        self.ollama_download_button.clicked.connect(self.open_ollama_download)
        self.ollama_pull_button = QPushButton()
        self.ollama_pull_button.clicked.connect(self.pull_selected_ollama_model)
        self.ollama_pull_worker: OllamaPullWorker | None = None

        self.keep_timestamps_checkbox = QCheckBox()
        self.keep_timestamps_checkbox.setChecked(True)
        self.review_questions_checkbox = QCheckBox()
        self.review_questions_checkbox.setChecked(True)
        self.checklist_checkbox = QCheckBox()
        self.checklist_checkbox.setChecked(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        self.open_output_button = QPushButton()
        self.open_output_button.setEnabled(False)
        self.open_output_button.clicked.connect(self.open_output_folder)
        self.author_footer_label = QLabel()

        self._build_layout()
        self.apply_language()

    def _build_layout(self) -> None:
        self.add_files_button = QPushButton()
        self.add_files_button.clicked.connect(self.select_files)
        self.remove_button = QPushButton()
        self.remove_button.clicked.connect(self.remove_selected_files)
        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(self.file_list.clear)

        file_buttons = QHBoxLayout()
        file_buttons.addWidget(self.add_files_button)
        file_buttons.addWidget(self.remove_button)
        file_buttons.addWidget(self.clear_button)

        self.output_button = QPushButton()
        self.output_button.clicked.connect(self.select_output_folder)
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_button)
        output_layout.addWidget(self.output_label, stretch=1)

        self.language_label = QLabel()
        language_row = QHBoxLayout()
        language_row.addWidget(self.language_label)
        language_row.addWidget(self.language_combo)
        language_row.addStretch(1)

        options_row = QHBoxLayout()
        self.mode_label = QLabel()
        self.quality_label = QLabel()
        self.pdf_output_label = QLabel()
        options_row.addWidget(self.mode_label)
        options_row.addWidget(self.mode_combo)
        options_row.addWidget(self.pdf_output_label)
        options_row.addWidget(self.pdf_output_combo)
        options_row.addWidget(self.quality_label)
        options_row.addWidget(self.quality_combo)
        options_row.addWidget(self.ocr_checkbox)
        options_row.addWidget(self.separator_checkbox)

        transcript_row = QHBoxLayout()
        self.transcript_preserve_label = QLabel()
        self.ai_mode_label = QLabel()
        self.output_mode_label = QLabel()
        self.output_language_label = QLabel()
        transcript_row.addWidget(self.transcript_preserve_label)
        transcript_row.addWidget(self.preserve_combo)
        transcript_row.addWidget(self.ai_mode_label)
        transcript_row.addWidget(self.ai_mode_combo)
        transcript_row.addWidget(self.output_mode_label)
        transcript_row.addWidget(self.output_mode_combo)
        transcript_row.addWidget(self.output_language_label)
        transcript_row.addWidget(self.output_language_combo)

        ollama_row = QHBoxLayout()
        self.ollama_status_label = QLabel()
        self.ollama_model_label = QLabel()
        ollama_row.addWidget(self.ollama_status_label)
        ollama_row.addWidget(self.ollama_status_value)
        ollama_row.addWidget(self.ollama_model_label)
        ollama_row.addWidget(self.ollama_model_combo)
        ollama_row.addWidget(self.ollama_check_button)
        ollama_row.addWidget(self.ollama_guide_button)
        ollama_row.addWidget(self.ollama_download_button)
        ollama_row.addWidget(self.ollama_pull_button)

        self.start_button = QPushButton()
        self.start_button.clicked.connect(self.start_conversion)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.start_button)
        bottom_row.addWidget(self.open_output_button)

        self.files_label = QLabel()
        self.log_label = QLabel()
        layout = QVBoxLayout()
        layout.addLayout(language_row)
        layout.addWidget(self.files_label)
        layout.addWidget(self.file_list)
        layout.addLayout(file_buttons)
        layout.addLayout(output_layout)
        layout.addLayout(options_row)
        layout.addLayout(transcript_row)
        layout.addLayout(ollama_row)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_label)
        layout.addWidget(self.log_area, stretch=1)
        layout.addLayout(bottom_row)
        layout.addWidget(self.author_footer_label)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

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
        ai_mode_value = self.ai_mode_combo.currentData() or "basic"
        output_mode_value = self.output_mode_combo.currentData() or "study_note"
        output_language_value = self.output_language_combo.currentData() or "auto"

        self.setWindowTitle(self.tr("window_title"))
        self.file_list.setToolTip(self.tr("drop_tooltip"))

        self.language_label.setText(self.tr("language"))
        self.files_label.setText(self.tr("files"))
        self.add_files_button.setText(self.tr("select_files"))
        self.remove_button.setText(self.tr("remove_selected"))
        self.clear_button.setText(self.tr("clear"))
        self.output_button.setText(self.tr("select_output_folder"))
        self.mode_label.setText(self.tr("mode"))
        self.pdf_output_label.setText(self.tr("pdf_output"))
        self.quality_label.setText(self.tr("quality"))
        self.ocr_checkbox.setText(self.tr("ocr"))
        self.separator_checkbox.setText(self.tr("separator"))
        self.transcript_preserve_label.setText(self.tr("transcript_preserve"))
        self.ai_mode_label.setText(self.tr("ai_mode"))
        self.output_mode_label.setText(self.tr("output_mode"))
        self.output_language_label.setText(self.tr("output_language"))
        self.ollama_status_label.setText(self.tr("ollama_status"))
        if not self.ollama_status_value.text():
            self.ollama_status_value.setText(self.tr("ollama_not_checked"))
        self.ollama_model_label.setText(self.tr("ollama_model"))
        self.ollama_check_button.setText(self.tr("check_ollama"))
        self.ollama_guide_button.setText(self.tr("ollama_setup_guide"))
        self.ollama_download_button.setText(self.tr("open_ollama_download"))
        self.ollama_pull_button.setText(self.tr("pull_model"))
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
        self.update_output_options()

    def update_output_options(self) -> None:
        is_ollama = self.ai_mode_combo.currentData() == "ollama"
        self.ollama_status_label.setEnabled(is_ollama)
        self.ollama_status_value.setEnabled(is_ollama)
        self.ollama_model_label.setEnabled(is_ollama)
        self.ollama_model_combo.setEnabled(is_ollama)
        self.ollama_check_button.setEnabled(is_ollama)
        self.ollama_guide_button.setEnabled(is_ollama)
        self.ollama_download_button.setEnabled(is_ollama)
        self.ollama_pull_button.setEnabled(is_ollama)

    def check_ollama_status(self) -> None:
        if is_ollama_running():
            self.ollama_status_value.setText(self.tr("ollama_running"))
            models = list_models()
            if models:
                current = self.ollama_model_combo.currentText()
                self.ollama_model_combo.clear()
                self.ollama_model_combo.addItems(models)
                if current:
                    self.ollama_model_combo.setCurrentText(current)
        else:
            self.ollama_status_value.setText(self.tr("ollama_not_detected"))

    def open_ollama_download(self) -> None:
        QDesktopServices.openUrl(QUrl("https://ollama.com/download"))

    def show_ollama_setup_guide(self) -> None:
        QMessageBox.information(
            self,
            self.tr("ollama_guide_title"),
            self.tr("ollama_guide_text"),
        )

    def pull_selected_ollama_model(self) -> None:
        model = self.ollama_model_combo.currentText().strip()
        if not model:
            return
        self.append_log(self.tr("ollama_pull_started", model=model))
        self.ollama_pull_button.setEnabled(False)
        self.ollama_pull_worker = OllamaPullWorker(model)
        self.ollama_pull_worker.finished_message.connect(self.ollama_pull_finished)
        self.ollama_pull_worker.start()

    def ollama_pull_finished(self, message: str) -> None:
        self.ollama_pull_button.setEnabled(True)
        self.append_log(self.tr("ollama_pull_finished", message=message))
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
            transcript_ai_mode=self.ai_mode_combo.currentData() or "basic",
            transcript_output_mode=self.output_mode_combo.currentData() or "study_note",
            transcript_output_language=self.output_language_combo.currentData() or "auto",
            ollama_model=self.ollama_model_combo.currentText().strip() or "qwen2.5:3b",
            transcript_keep_timestamps=self.keep_timestamps_checkbox.isChecked(),
            transcript_review_questions=self.review_questions_checkbox.isChecked(),
            transcript_checklist=self.checklist_checkbox.isChecked(),
        )

        self.progress_bar.setValue(0)
        self.open_output_button.setEnabled(False)
        self.append_log(self.tr("starting"))
        self.worker = ConversionWorker(files, options)
        self.worker.log_message.connect(self.append_log)
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.finished_success.connect(self.conversion_finished)
        self.worker.failed.connect(self.conversion_failed)
        self.worker.start()

    def append_log(self, message: str) -> None:
        self.log_area.append(message)

    def conversion_finished(self, output_folder: str) -> None:
        self.last_output_folder = Path(output_folder)
        self.open_output_button.setEnabled(True)
        self.append_log(self.tr("finished"))

    def conversion_failed(self, message: str) -> None:
        self.append_log(self.tr("error", message=message))
        QMessageBox.critical(self, self.tr("failed_title"), message)

    def open_output_folder(self) -> None:
        self.last_output_folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_output_folder)))
