"""
macOS 剪贴板监听器
使用 PyQt5 剪贴板变化信号
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QTimer


class ClipboardListener(QObject):
    """
    剪贴板监听器
    使用 PyQt5 的剪贴板变化信号监听剪贴板变化
    """

    # 剪贴板变化信号
    clipboard_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._started = False
        self.clipboard = QApplication.clipboard()

    def start(self):
        """开始监听剪贴板"""
        if self._started:
            return True

        try:
            # 连接剪贴板变化信号
            self.clipboard.dataChanged.connect(self._on_clipboard_changed)
            self._started = True
            return True
        except Exception:
            return False

    def stop(self):
        """停止监听剪贴板"""
        if not self._started:
            return

        try:
            # 断开剪贴板变化信号
            self.clipboard.dataChanged.disconnect(self._on_clipboard_changed)
            self._started = False
        except Exception:
            pass

    def _on_clipboard_changed(self):
        """剪贴板内容已更新,发出信号"""
        self.clipboard_changed.emit()
