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
        "mode_lecture": "Lecture subtitle summary",
        "mode_auto": "Auto detect",
        "quality": "Quality",
        "pdf_output_markdown_image": "Markdown + Image",
        "pdf_output_webp_compression": "WebP Compression",
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
        "keep_timestamps": "Keep timestamps",
        "review_questions": "Generate review questions",
        "checklist": "Generate checklist",
        "log": "Log",
        "start": "Start conversion",
        "open_output": "Open output folder",
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
        "keep_timestamps": "타임스탬프 유지",
        "review_questions": "복습 질문 생성",
        "checklist": "체크리스트 생성",
        "log": "로그",
        "start": "변환 시작",
        "open_output": "출력 폴더 열기",
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

        self.ocr_checkbox = QCheckBox()
        self.separator_checkbox = QCheckBox()
        self.separator_checkbox.setChecked(True)

        self.preserve_combo = QComboBox()

        self.transcript_format_combo = QComboBox()

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
        options_row.addWidget(self.mode_label)
        options_row.addWidget(self.mode_combo)
        options_row.addWidget(self.quality_label)
        options_row.addWidget(self.quality_combo)
        options_row.addWidget(self.ocr_checkbox)
        options_row.addWidget(self.separator_checkbox)

        transcript_row = QHBoxLayout()
        self.transcript_preserve_label = QLabel()
        self.transcript_output_label = QLabel()
        transcript_row.addWidget(self.transcript_preserve_label)
        transcript_row.addWidget(self.preserve_combo)
        transcript_row.addWidget(self.transcript_output_label)
        transcript_row.addWidget(self.transcript_format_combo)

        transcript_checks = QHBoxLayout()
        transcript_checks.addWidget(self.keep_timestamps_checkbox)
        transcript_checks.addWidget(self.review_questions_checkbox)
        transcript_checks.addWidget(self.checklist_checkbox)

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
        layout.addLayout(transcript_checks)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_label)
        layout.addWidget(self.log_area, stretch=1)
        layout.addLayout(bottom_row)

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
        output_value = self.transcript_format_combo.currentData()

        self.setWindowTitle(self.tr("window_title"))
        self.file_list.setToolTip(self.tr("drop_tooltip"))

        self.language_label.setText(self.tr("language"))
        self.files_label.setText(self.tr("files"))
        self.add_files_button.setText(self.tr("select_files"))
        self.remove_button.setText(self.tr("remove_selected"))
        self.clear_button.setText(self.tr("clear"))
        self.output_button.setText(self.tr("select_output_folder"))
        self.mode_label.setText(self.tr("mode"))
        self.quality_label.setText(self.tr("quality"))
        self.ocr_checkbox.setText(self.tr("ocr"))
        self.separator_checkbox.setText(self.tr("separator"))
        self.transcript_preserve_label.setText(self.tr("transcript_preserve"))
        self.transcript_output_label.setText(self.tr("output"))
        self.keep_timestamps_checkbox.setText(self.tr("keep_timestamps"))
        self.review_questions_checkbox.setText(self.tr("review_questions"))
        self.checklist_checkbox.setText(self.tr("checklist"))
        self.log_label.setText(self.tr("log"))
        self.start_button.setText(self.tr("start"))
        self.open_output_button.setText(self.tr("open_output"))

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
        self._refresh_output_options(output_value)

    def _output_items_for_mode(self, mode: str | None) -> list[tuple[str, str]]:
        if mode == "lecture":
            return [
                (self.tr("format_study_note"), "study_note"),
                (self.tr("format_ebook_draft"), "ebook_draft"),
                (self.tr("format_obsidian_moc"), "obsidian_moc"),
            ]

        return [
            (self.tr("pdf_output_markdown_image"), "markdown_image"),
            (self.tr("pdf_output_webp_compression"), "webp_compression"),
        ]

    def _refresh_output_options(self, selected_data: str | None = None) -> None:
        mode_value = self.mode_combo.currentData() or "auto"
        self._reset_combo_items(
            self.transcript_format_combo,
            self._output_items_for_mode(mode_value),
            selected_data,
        )

    def update_output_options(self) -> None:
        self._refresh_output_options(self.transcript_format_combo.currentData())

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
            pdf_output_format=self.transcript_format_combo.currentData() or "markdown_image",
            transcript_preserve_level=self.preserve_combo.currentData(),
            transcript_output_format=self.transcript_format_combo.currentData(),
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
