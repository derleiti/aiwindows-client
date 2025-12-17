"""
AIWindows File Browser
======================
Windows-optimierter Dateibrowser mit Laufwerks-Support (C:\, D:\, etc.)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QListView,
    QSplitter, QToolBar, QLineEdit, QComboBox, QMenu,
    QFileSystemModel, QAbstractItemView, QMessageBox,
    QPushButton, QLabel, QInputDialog, QProgressDialog
)
from PyQt6.QtCore import Qt, QDir, QModelIndex, pyqtSignal, QUrl, QMimeData
from PyQt6.QtGui import QAction, QDesktopServices, QDrag
import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("aiwindows.file_browser")


def get_windows_drives():
    """Get list of available Windows drives"""
    drives = []
    if sys.platform == 'win32':
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
    else:
        # Fallback für Entwicklung auf Linux
        drives = [str(Path.home())]
    return drives


class WindowsFileBrowser(QWidget):
    """
    File browser optimized for Windows with drive support.
    """
    
    file_selected = pyqtSignal(str)
    directory_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = str(Path.home())
        self._setup_ui()
        self._navigate_to(self.current_path)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 5, 5, 5)
        
        # Drive selector (Windows-spezifisch)
        self.drive_combo = QComboBox()
        self.drive_combo.setMinimumWidth(80)
        drives = get_windows_drives()
        for drive in drives:
            self.drive_combo.addItem(drive)
        self.drive_combo.currentTextChanged.connect(self._on_drive_changed)
        toolbar.addWidget(QLabel("Laufwerk:"))
        toolbar.addWidget(self.drive_combo)
        
        # Navigation buttons
        self.back_btn = QPushButton("←")
        self.back_btn.setMaximumWidth(30)
        self.back_btn.clicked.connect(self._go_back)
        toolbar.addWidget(self.back_btn)
        
        self.up_btn = QPushButton("↑")
        self.up_btn.setMaximumWidth(30)
        self.up_btn.clicked.connect(self._go_up)
        toolbar.addWidget(self.up_btn)
        
        self.home_btn = QPushButton("🏠")
        self.home_btn.setMaximumWidth(30)
        self.home_btn.clicked.connect(self._go_home)
        toolbar.addWidget(self.home_btn)
        
        # Path bar
        self.path_edit = QLineEdit()
        self.path_edit.returnPressed.connect(self._on_path_entered)
        toolbar.addWidget(self.path_edit, 1)
        
        # Refresh
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setMaximumWidth(30)
        self.refresh_btn.clicked.connect(self._refresh)
        toolbar.addWidget(self.refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Splitter: Tree + List view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Tree view (Ordner-Baum)
        self.tree_model = QFileSystemModel()
        self.tree_model.setRootPath("")
        self.tree_model.setFilter(QDir.Filter.Dirs | QDir.Filter.NoDotAndDotDot)
        
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setHeaderHidden(True)
        # Nur Name-Spalte zeigen
        for i in range(1, self.tree_model.columnCount()):
            self.tree_view.hideColumn(i)
        self.tree_view.clicked.connect(self._on_tree_clicked)
        self.tree_view.setMaximumWidth(250)
        splitter.addWidget(self.tree_view)
        
        # List view (Dateien)
        self.list_model = QFileSystemModel()
        self.list_model.setRootPath("")
        
        self.list_view = QListView()
        self.list_view.setModel(self.list_model)
        self.list_view.setViewMode(QListView.ViewMode.ListMode)
        self.list_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_view.doubleClicked.connect(self._on_item_double_clicked)
        self.list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self._show_context_menu)
        splitter.addWidget(self.list_view)
        
        splitter.setSizes([200, 600])
        layout.addWidget(splitter, 1)
        
        # Status bar
        self.status_label = QLabel("Bereit")
        layout.addWidget(self.status_label)
        
        # History
        self._history = []
        self._history_index = -1
    
    def _navigate_to(self, path: str):
        """Navigate to path"""
        if not os.path.exists(path):
            QMessageBox.warning(self, "Fehler", f"Pfad nicht gefunden: {path}")
            return
        
        self.current_path = path
        self.path_edit.setText(path)
        
        # Update list view
        index = self.list_model.setRootPath(path)
        self.list_view.setRootIndex(index)
        
        # Update tree view
        tree_index = self.tree_model.index(path)
        self.tree_view.setCurrentIndex(tree_index)
        self.tree_view.expand(tree_index)
        
        # Update drive combo
        if sys.platform == 'win32' and len(path) >= 2:
            drive = path[:3]
            idx = self.drive_combo.findText(drive)
            if idx >= 0:
                self.drive_combo.blockSignals(True)
                self.drive_combo.setCurrentIndex(idx)
                self.drive_combo.blockSignals(False)
        
        # History
        if not self._history or self._history[self._history_index] != path:
            self._history = self._history[:self._history_index + 1]
            self._history.append(path)
            self._history_index = len(self._history) - 1
        
        # Status
        try:
            items = len(os.listdir(path))
            self.status_label.setText(f"{items} Elemente in {path}")
        except:
            self.status_label.setText(path)
        
        self.directory_changed.emit(path)
    
    def _on_drive_changed(self, drive: str):
        """Drive selection changed"""
        if os.path.exists(drive):
            self._navigate_to(drive)
    
    def _on_tree_clicked(self, index: QModelIndex):
        """Tree item clicked"""
        path = self.tree_model.filePath(index)
        if os.path.isdir(path):
            self._navigate_to(path)
    
    def _on_item_double_clicked(self, index: QModelIndex):
        """List item double-clicked"""
        path = self.list_model.filePath(index)
        if os.path.isdir(path):
            self._navigate_to(path)
        elif os.path.isfile(path):
            self._open_file(path)
    
    def _open_file(self, path: str):
        """Open file with default application"""
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            self.file_selected.emit(path)
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Kann Datei nicht öffnen: {e}")
    
    def _on_path_entered(self):
        """Path manually entered"""
        path = self.path_edit.text().strip()
        if path:
            self._navigate_to(path)
    
    def _go_back(self):
        """Go back in history"""
        if self._history_index > 0:
            self._history_index -= 1
            path = self._history[self._history_index]
            self._navigate_to(path)
    
    def _go_up(self):
        """Go to parent directory"""
        parent = str(Path(self.current_path).parent)
        if parent != self.current_path:
            self._navigate_to(parent)
    
    def _go_home(self):
        """Go to home directory"""
        self._navigate_to(str(Path.home()))
    
    def _refresh(self):
        """Refresh current directory"""
        self._navigate_to(self.current_path)
    
    def _show_context_menu(self, pos):
        """Show context menu"""
        menu = QMenu(self)
        
        # Get selected items
        indexes = self.list_view.selectedIndexes()
        
        if indexes:
            path = self.list_model.filePath(indexes[0])
            
            open_action = menu.addAction("Öffnen")
            open_action.triggered.connect(lambda: self._open_file(path))
            
            if sys.platform == 'win32':
                explorer_action = menu.addAction("Im Explorer öffnen")
                explorer_action.triggered.connect(
                    lambda: subprocess.run(['explorer', '/select,', path])
                )
            
            menu.addSeparator()
            
            copy_action = menu.addAction("Kopieren")
            copy_action.triggered.connect(lambda: self._copy_path(path))
            
            delete_action = menu.addAction("Löschen")
            delete_action.triggered.connect(lambda: self._delete_item(path))
        
        menu.addSeparator()
        
        new_folder = menu.addAction("Neuer Ordner")
        new_folder.triggered.connect(self._create_folder)
        
        menu.exec(self.list_view.mapToGlobal(pos))
    
    def _copy_path(self, path: str):
        """Copy path to clipboard"""
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(path)
    
    def _delete_item(self, path: str):
        """Delete file or folder"""
        name = os.path.basename(path)
        reply = QMessageBox.question(
            self, "Löschen bestätigen",
            f"'{name}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self._refresh()
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Löschen fehlgeschlagen: {e}")
    
    def _create_folder(self):
        """Create new folder"""
        name, ok = QInputDialog.getText(self, "Neuer Ordner", "Name:")
        if ok and name:
            try:
                new_path = os.path.join(self.current_path, name)
                os.makedirs(new_path)
                self._refresh()
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Ordner erstellen fehlgeschlagen: {e}")
