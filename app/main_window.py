from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QListWidget, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget
)
from PIL import Image

from .stitcher import image_files, stitch
from .odg_export import export_images_to_odg


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JASS Image Stitcher v1.2.0 — Original Quality")
        self.resize(1100, 750)
        self.folder = None
        self.result = None
        self.bg = (255, 255, 255, 255)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        top = QHBoxLayout()
        self.folder_label = QLabel("No folder selected")
        choose = QPushButton("Select Folder")
        choose.clicked.connect(self.choose_folder)
        top.addWidget(choose)
        top.addWidget(self.folder_label, 1)
        layout.addLayout(top)

        body = QHBoxLayout()
        layout.addLayout(body, 1)

        left = QVBoxLayout()
        body.addLayout(left, 0)

        files_box = QGroupBox("Images")
        files_layout = QVBoxLayout(files_box)
        self.list_widget = QListWidget()
        files_layout.addWidget(self.list_widget)
        left.addWidget(files_box, 1)

        settings = QGroupBox("Stitch Settings")
        form = QFormLayout(settings)

        self.direction = QComboBox()
        self.direction.addItems(["Vertical", "Horizontal"])
        form.addRow("Direction", self.direction)

        self.gap = QSpinBox()
        self.gap.setRange(0, 10000)
        self.gap.setValue(0)
        form.addRow("Gap (pixels)", self.gap)

        self.labels = QCheckBox("Add filename labels")
        form.addRow("", self.labels)

        bg_btn = QPushButton("Background")
        bg_btn.clicked.connect(self.choose_background)
        form.addRow("", bg_btn)

        quality = QGroupBox("Output Quality")
        qform = QFormLayout(quality)

        self.jpeg_quality = QSpinBox()
        self.jpeg_quality.setRange(1, 100)
        self.jpeg_quality.setValue(100)
        qform.addRow("JPEG quality", self.jpeg_quality)

        self.webp_lossless = QCheckBox("WEBP lossless")
        self.webp_lossless.setChecked(True)
        qform.addRow("", self.webp_lossless)

        self.dpi = QSpinBox()
        self.dpi.setRange(72, 1200)
        self.dpi.setValue(300)
        qform.addRow("PDF DPI", self.dpi)

        note = QLabel(
            "Original pixel dimensions are preserved by default.\n"
            "No resize/downscale is performed during stitching."
        )
        note.setWordWrap(True)
        qform.addRow(note)

        left.addWidget(settings)
        left.addWidget(quality)

        buttons = QHBoxLayout()
        stitch_btn = QPushButton("Stitch — Preserve Original Pixels")
        stitch_btn.clicked.connect(self.do_stitch)
        save_img = QPushButton("Save Image")
        save_img.clicked.connect(self.save_image)
        save_pdf = QPushButton("Save PDF")
        save_pdf.clicked.connect(self.save_pdf)
        save_odg = QPushButton("Save in LibreOffice Draw")
        save_odg.clicked.connect(self.save_odg)
        buttons.addWidget(stitch_btn)
        buttons.addWidget(save_img)
        buttons.addWidget(save_pdf)
        buttons.addWidget(save_odg)
        left.addLayout(buttons)

        self.info = QLabel("Ready")
        self.info.setWordWrap(True)
        left.addWidget(self.info)

        preview_box = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_box)
        self.preview = QLabel("Stitched image preview")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(500, 500)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.preview)
        preview_layout.addWidget(self.scroll)
        body.addWidget(preview_box, 1)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not folder:
            return
        self.folder = Path(folder)
        files = image_files(folder)
        self.list_widget.clear()
        self.list_widget.addItems([p.name for p in files])
        self.folder_label.setText(str(self.folder))
        self.info.setText(f"{len(files)} supported image(s) found.")

    def choose_background(self):
        c = QColorDialog.getColor(QColor(*self.bg[:3]), self, "Choose Background")
        if c.isValid():
            self.bg = (c.red(), c.green(), c.blue(), 255)

    def current_paths(self):
        if not self.folder:
            return []
        return image_files(self.folder)

    def do_stitch(self):
        paths = self.current_paths()
        if not paths:
            QMessageBox.warning(self, "No images", "Select a folder containing supported images.")
            return
        try:
            self.result = stitch(
                paths,
                direction=self.direction.currentText(),
                gap=self.gap.value(),
                background=self.bg,
                labels=self.labels.isChecked(),
            )
            self.show_preview()
            self.info.setText(
                f"Output: {self.result.width:,} × {self.result.height:,} pixels\n"
                f"Images: {len(paths)}\n"
                f"Pixels are preserved; no automatic resizing is applied."
            )
        except Exception as e:
            QMessageBox.critical(self, "Stitching error", str(e))

    def show_preview(self):
        if self.result is None:
            return
        rgba = self.result.convert("RGBA")
        data = rgba.tobytes("raw", "RGBA")
        qimg = QImage(data, rgba.width, rgba.height, rgba.width * 4, QImage.Format_RGBA8888)
        pix = QPixmap.fromImage(qimg.copy())
        max_w = max(300, self.scroll.viewport().width() - 20)
        max_h = max(300, self.scroll.viewport().height() - 20)
        pix = pix.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview.setPixmap(pix)

    def save_image(self):
        if self.result is None:
            QMessageBox.information(self, "Nothing to save", "Stitch the images first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Combined Image", "stitched.png",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;WEBP (*.webp)"
        )
        if not path:
            return

        suffix = Path(path).suffix.lower()
        try:
            if suffix == ".png":
                # Lossless.
                self.result.save(path, "PNG", compress_level=0)
            elif suffix in (".jpg", ".jpeg"):
                # JPEG requires RGB; quality 100 minimizes additional loss.
                self.result.convert("RGB").save(
                    path, "JPEG", quality=self.jpeg_quality.value(),
                    subsampling=0, optimize=True
                )
            elif suffix == ".webp":
                if self.webp_lossless.isChecked():
                    self.result.save(path, "WEBP", lossless=True, method=6)
                else:
                    self.result.save(path, "WEBP", quality=100, method=6)
            else:
                self.result.save(path)
            QMessageBox.information(self, "Saved", f"Saved:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Save error", str(e))

    def save_pdf(self):
        if self.result is None:
            QMessageBox.information(self, "Nothing to save", "Stitch the images first.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "stitched.pdf", "PDF (*.pdf)")
        if not path:
            return

        try:
            # Embed the complete stitched pixel data at the selected DPI.
            # No resizing is performed here.
            rgb = self.result.convert("RGB")
            rgb.save(path, "PDF", resolution=float(self.dpi.value()))
            QMessageBox.information(
                self, "Saved",
                f"PDF saved:\n{path}\n\n"
                f"Pixel dimensions preserved: {self.result.width:,} × {self.result.height:,}"
            )
        except Exception as e:
            QMessageBox.critical(self, "PDF error", str(e))

    def save_odg(self):
        paths = self.current_paths()
        if not paths:
            QMessageBox.information(self, "No images", "Select a folder containing supported images.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save LibreOffice Draw Document", "stitched-images.odg",
            "LibreOffice Draw (*.odg)"
        )
        if not path:
            return
        try:
            export_images_to_odg(paths, path, dpi=96.0)
            QMessageBox.information(
                self, "Saved in LibreOffice Draw",
                f"Saved:\n{path}\n\n"
                f"{len(paths)} page(s) created.\n"
                "Each page contains one original image embedded at its native pixel resolution.\n"
                "Open the .odg file with LibreOffice Draw."
            )
        except Exception as e:
            QMessageBox.critical(self, "LibreOffice Draw export error", str(e))


def run():
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
