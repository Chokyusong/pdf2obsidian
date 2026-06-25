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

        self.file_list = DropListWidget()
        self.file_list.files_dropped.connect(self.add_files)

        self.output_label = QLabel(str(self.last_output_folder))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["60", "75", "90"])
        self.quality_combo.setCurrentText("75")

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("PDF/Image conversion", "pdf_image")
        self.mode_combo.addItem("Lecture transcript note", "lecture")
        self.mode_combo.addItem("Auto detect", "auto")
        self.mode_combo.setCurrentIndex(2)

        self.ocr_checkbox = QCheckBox("Use OCR when available")
        self.separator_checkbox = QCheckBox("Insert page separators")
        self.separator_checkbox.setChecked(True)

        self.preserve_combo = QComboBox()
        self.preserve_combo.addItem("Low", "low")
        self.preserve_combo.addItem("Medium", "medium")
        self.preserve_combo.addItem("High", "high")
        self.preserve_combo.setCurrentIndex(1)

        self.transcript_format_combo = QComboBox()
        self.transcript_format_combo.addItem("Study note", "study_note")
        self.transcript_format_combo.addItem("Ebook draft", "ebook_draft")
        self.transcript_format_combo.addItem("Obsidian MOC", "obsidian_moc")

        self.keep_timestamps_checkbox = QCheckBox("Keep timestamps")
        self.keep_timestamps_checkbox.setChecked(True)
        self.review_questions_checkbox = QCheckBox("Generate review questions")
        self.review_questions_checkbox.setChecked(True)
        self.checklist_checkbox = QCheckBox("Generate checklist")
        self.checklist_checkbox.setChecked(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        self.open_output_button = QPushButton("Open output folder")
        self.open_output_button.setEnabled(False)
        self.open_output_button.clicked.connect(self.open_output_folder)

        self._build_layout()

    def _build_layout(self) -> None:
        add_files_button = QPushButton("Select files")
        add_files_button.clicked.connect(self.select_files)
        remove_button = QPushButton("Remove selected")
        remove_button.clicked.connect(self.remove_selected_files)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.file_list.clear)

        file_buttons = QHBoxLayout()
        file_buttons.addWidget(add_files_button)
        file_buttons.addWidget(remove_button)
        file_buttons.addWidget(clear_button)

        output_button = QPushButton("Select output folder")
        output_button.clicked.connect(self.select_output_folder)
        output_layout = QHBoxLayout()
        output_layout.addWidget(output_button)
        output_layout.addWidget(self.output_label, stretch=1)

        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("Mode"))
        options_row.addWidget(self.mode_combo)
        options_row.addWidget(QLabel("Quality"))
        options_row.addWidget(self.quality_combo)
        options_row.addWidget(self.ocr_checkbox)
        options_row.addWidget(self.separator_checkbox)

        transcript_row = QHBoxLayout()
        transcript_row.addWidget(QLabel("Transcript preserve"))
        transcript_row.addWidget(self.preserve_combo)
        transcript_row.addWidget(QLabel("Output"))
        transcript_row.addWidget(self.transcript_format_combo)

        transcript_checks = QHBoxLayout()
        transcript_checks.addWidget(self.keep_timestamps_checkbox)
        transcript_checks.addWidget(self.review_questions_checkbox)
        transcript_checks.addWidget(self.checklist_checkbox)

        start_button = QPushButton("Start conversion")
        start_button.clicked.connect(self.start_conversion)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(start_button)
        bottom_row.addWidget(self.open_output_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Files"))
        layout.addWidget(self.file_list)
        layout.addLayout(file_buttons)
        layout.addLayout(output_layout)
        layout.addLayout(options_row)
        layout.addLayout(transcript_row)
        layout.addLayout(transcript_checks)
        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("Log"))
        layout.addWidget(self.log_area, stretch=1)
        layout.addLayout(bottom_row)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

    def select_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files",
            str(Path.cwd()),
            "Supported files (*.pdf *.png *.jpg *.jpeg *.webp *.srt *.vtt *.txt *.md)",
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
                self.append_log(f"Skipped unsupported file: {path.name}")

    def remove_selected_files(self) -> None:
        for item in self.file_list.selectedItems():
            row = self.file_list.row(item)
            self.file_list.takeItem(row)

    def select_output_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
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
            QMessageBox.warning(self, "No files", "Add at least one file first.")
            return

        self.last_output_folder.mkdir(parents=True, exist_ok=True)
        options = ConversionOptions(
            output_root=self.last_output_folder,
            image_quality=int(self.quality_combo.currentText()),
            ocr_enabled=self.ocr_checkbox.isChecked(),
            include_page_separator=self.separator_checkbox.isChecked(),
            mode=self.mode_combo.currentData(),
            transcript_preserve_level=self.preserve_combo.currentData(),
            transcript_output_format=self.transcript_format_combo.currentData(),
            transcript_keep_timestamps=self.keep_timestamps_checkbox.isChecked(),
            transcript_review_questions=self.review_questions_checkbox.isChecked(),
            transcript_checklist=self.checklist_checkbox.isChecked(),
        )

        self.progress_bar.setValue(0)
        self.open_output_button.setEnabled(False)
        self.append_log("Starting conversion.")
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
        self.append_log("Conversion finished.")

    def conversion_failed(self, message: str) -> None:
        self.append_log(f"Error: {message}")
        QMessageBox.critical(self, "Conversion failed", message)

    def open_output_folder(self) -> None:
        self.last_output_folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_output_folder)))
