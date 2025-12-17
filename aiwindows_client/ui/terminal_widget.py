"""
AIWindows Terminal Widget
=========================

Windows Terminal Emulator using ConPTY (Windows 10 1809+)
Supports PowerShell and CMD with full ANSI color support.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPlainTextEdit, QToolButton, QPushButton, QSizePolicy, QLabel
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QProcess
from PyQt6.QtGui import (
    QFont, QTextCursor, QColor, QKeyEvent, QTextCharFormat,
    QPainter, QFontMetrics, QPalette
)
import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional

# Windows ConPTY via winpty
try:
    from winpty import PtyProcess
    HAS_WINPTY = True
except ImportError:
    HAS_WINPTY = False

# VT100 Emulator
try:
    import pyte
    HAS_PYTE = True
except ImportError:
    HAS_PYTE = False

logger = logging.getLogger("aiwindows.terminal_widget")


class ConPTYReader(QThread):
    """Thread for reading ConPTY output"""
    data_ready = pyqtSignal(bytes)
    finished = pyqtSignal(int)
    
    def __init__(self, pty_process):
        super().__init__()
        self.pty = pty_process
        self._running = True
    
    def run(self):
        """Read loop"""
        while self._running and self.pty.isalive():
            try:
                data = self.pty.read(4096)
                if data:
                    self.data_ready.emit(data.encode() if isinstance(data, str) else data)
            except Exception as e:
                if self._running:
                    logger.error(f"ConPTY read error: {e}")
                break
        
        exit_code = self.pty.exitstatus or 0
        self.finished.emit(exit_code)
    
    def stop(self):
        self._running = False


class WindowsTerminalCanvas(QWidget):
    """
    Terminal canvas with VT100 rendering for Windows.
    Uses pyte for escape sequence handling.
    """
    
    # ANSI 256-color palette (standard)
    COLORS_16 = [
        "#0c0c0c", "#c50f1f", "#13a10e", "#c19c00",
        "#0037da", "#881798", "#3a96dd", "#cccccc",
        "#767676", "#e74856", "#16c60c", "#f9f1a5",
        "#3b78ff", "#b4009e", "#61d6d6", "#f2f2f2"
    ]
    
    def __init__(self, cols=120, rows=30, parent=None):
        super().__init__(parent)
        self.cols = cols
        self.rows = rows
        
        # Font setup
        self.term_font = QFont("Cascadia Code", 11)
        if not QFontMetrics(self.term_font).horizontalAdvance("W"):
            self.term_font = QFont("Consolas", 11)
        self.term_font.setStyleHint(QFont.StyleHint.Monospace)
        
        metrics = QFontMetrics(self.term_font)
        self.char_width = metrics.horizontalAdvance("W")
        self.char_height = metrics.height()
        
        # Pyte screen
        if HAS_PYTE:
            self.screen = pyte.Screen(cols, rows)
            self.stream = pyte.Stream(self.screen)
        else:
            self.screen = None
            self.stream = None
            self._buffer = []
        
        # ConPTY process
        self.pty = None
        self.reader = None
        self.pid = None
        
        # Working directory
        self.working_dir = str(Path.home())
        
        # Focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(self.char_width * 80, self.char_height * 24)
        
        # Background
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#0c0c0c"))
        self.setPalette(pal)
    
    def start(self, working_dir: str = None, shell: str = None):
        """Start ConPTY with PowerShell"""
        if not HAS_WINPTY:
            logger.error("winpty not installed! pip install pywinpty")
            return
        
        if working_dir:
            self.working_dir = working_dir
        
        shell = shell or "powershell.exe"
        
        try:
            # Start ConPTY
            self.pty = PtyProcess.spawn(
                [shell],
                cwd=self.working_dir,
                dimensions=(self.rows, self.cols)
            )
            
            # Start reader thread
            self.reader = ConPTYReader(self.pty)
            self.reader.data_ready.connect(self._on_data)
            self.reader.finished.connect(self._on_finished)
            self.reader.start()
            
            logger.info(f"ConPTY started: {shell}")
            
        except Exception as e:
            logger.error(f"Failed to start ConPTY: {e}")
    
    def _on_data(self, data: bytes):
        """Handle incoming data"""
        try:
            text = data.decode("utf-8", errors="replace")
            if self.stream:
                self.stream.feed(text)
            else:
                self._buffer.append(text)
            self.update()
        except Exception as e:
            logger.error(f"Data handling error: {e}")
    
    def _on_finished(self, exit_code: int):
        """Terminal process finished"""
        logger.info(f"Terminal exited with code {exit_code}")
    
    def _write(self, data: str):
        """Write to ConPTY"""
        if self.pty and self.pty.isalive():
            try:
                self.pty.write(data)
            except Exception as e:
                logger.error(f"Write error: {e}")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard input"""
        key = event.key()
        mods = event.modifiers()
        text = event.text()
        
        # Special keys
        key_map = {
            Qt.Key.Key_Return: "\r",
            Qt.Key.Key_Enter: "\r",
            Qt.Key.Key_Backspace: "\x7f",
            Qt.Key.Key_Tab: "\t",
            Qt.Key.Key_Escape: "\x1b",
            Qt.Key.Key_Up: "\x1b[A",
            Qt.Key.Key_Down: "\x1b[B",
            Qt.Key.Key_Right: "\x1b[C",
            Qt.Key.Key_Left: "\x1b[D",
            Qt.Key.Key_Home: "\x1b[H",
            Qt.Key.Key_End: "\x1b[F",
            Qt.Key.Key_PageUp: "\x1b[5~",
            Qt.Key.Key_PageDown: "\x1b[6~",
            Qt.Key.Key_Insert: "\x1b[2~",
            Qt.Key.Key_Delete: "\x1b[3~",
        }
        
        # Ctrl+C
        if mods & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_C:
                self._write("\x03")
                return
            elif key == Qt.Key.Key_D:
                self._write("\x04")
                return
            elif key == Qt.Key.Key_Z:
                self._write("\x1a")
                return
            elif key == Qt.Key.Key_L:
                self._write("\x0c")
                return
        
        if key in key_map:
            self._write(key_map[key])
        elif text:
            self._write(text)
    
    def paintEvent(self, event):
        """Render terminal screen"""
        painter = QPainter(self)
        painter.setFont(self.term_font)
        
        # Background
        painter.fillRect(self.rect(), QColor("#0c0c0c"))
        
        if not self.screen:
            # Fallback ohne pyte
            painter.setPen(QColor("#cccccc"))
            y = self.char_height
            for line in self._buffer[-self.rows:]:
                painter.drawText(5, y, line.rstrip())
                y += self.char_height
            return
        
        # Render pyte screen
        for row_idx, row in enumerate(self.screen.buffer):
            y = (row_idx + 1) * self.char_height
            x = 0
            
            for col_idx, char in enumerate(row):
                # Get character attributes
                fg = char.fg if char.fg != "default" else "white"
                bg = char.bg if char.bg != "default" else "default"
                
                # Map color
                if isinstance(fg, int) and fg < 16:
                    fg_color = QColor(self.COLORS_16[fg])
                elif fg == "white":
                    fg_color = QColor("#cccccc")
                else:
                    fg_color = QColor("#cccccc")
                
                if bg != "default":
                    if isinstance(bg, int) and bg < 16:
                        bg_color = QColor(self.COLORS_16[bg])
                        painter.fillRect(x, row_idx * self.char_height, 
                                        self.char_width, self.char_height, bg_color)
                
                painter.setPen(fg_color)
                painter.drawText(x, y - 3, char.data)
                x += self.char_width
        
        # Cursor
        cursor = self.screen.cursor
        if 0 <= cursor.y < self.rows and 0 <= cursor.x < self.cols:
            cx = cursor.x * self.char_width
            cy = cursor.y * self.char_height
            painter.fillRect(cx, cy, self.char_width, self.char_height, 
                           QColor(255, 255, 255, 180))
    
    def resizeEvent(self, event):
        """Handle resize"""
        super().resizeEvent(event)
        new_cols = max(80, self.width() // self.char_width)
        new_rows = max(24, self.height() // self.char_height)
        
        if new_cols != self.cols or new_rows != self.rows:
            self.cols = new_cols
            self.rows = new_rows
            
            if self.screen:
                self.screen.resize(new_rows, new_cols)
            
            if self.pty and self.pty.isalive():
                try:
                    self.pty.setwinsize(new_rows, new_cols)
                except:
                    pass
    
    def stop(self):
        """Stop terminal"""
        if self.reader:
            self.reader.stop()
            self.reader.wait(1000)
        
        if self.pty and self.pty.isalive():
            self.pty.terminate(force=True)


class TerminalTabWidget(QWidget):
    """
    Tabbed terminal widget for Windows.
    Supports multiple PowerShell/CMD tabs.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
        # Create first terminal
        QTimer.singleShot(100, self._add_terminal)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 5, 5, 5)
        
        self.new_tab_btn = QToolButton()
        self.new_tab_btn.setText("+")
        self.new_tab_btn.setToolTip("Neues Terminal (PowerShell)")
        self.new_tab_btn.clicked.connect(self._add_terminal)
        toolbar.addWidget(self.new_tab_btn)
        
        self.cmd_btn = QToolButton()
        self.cmd_btn.setText("CMD")
        self.cmd_btn.setToolTip("Neues CMD Terminal")
        self.cmd_btn.clicked.connect(lambda: self._add_terminal("cmd.exe"))
        toolbar.addWidget(self.cmd_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        layout.addWidget(self.tabs, 1)
    
    def _add_terminal(self, shell: str = "powershell.exe"):
        """Add new terminal tab"""
        terminal = WindowsTerminalCanvas(parent=self)
        
        shell_name = "PowerShell" if "powershell" in shell.lower() else "CMD"
        idx = self.tabs.addTab(terminal, f"{shell_name} {self.tabs.count() + 1}")
        self.tabs.setCurrentIndex(idx)
        
        terminal.start(shell=shell)
        terminal.setFocus()
    
    def _close_tab(self, index: int):
        """Close terminal tab"""
        widget = self.tabs.widget(index)
        if isinstance(widget, WindowsTerminalCanvas):
            widget.stop()
        self.tabs.removeTab(index)
        
        # Ensure at least one tab
        if self.tabs.count() == 0:
            self._add_terminal()
