"""
macOS 剪贴板监听器
后台轮询 NSPasteboard.changeCount。
Qt 的 dataChanged 在 macOS 上只有应用激活时才会收到其他应用的复制。
"""

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from utils.clipboard_utils import get_clipboard_change_count


class ClipboardListener(QObject):
    """剪贴板监听器"""

    clipboard_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._started = False
        self._change_count = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)

    def start(self):
        """开始监听剪贴板"""
        if self._started:
            return True

        try:
            self._change_count = get_clipboard_change_count()
            self._timer.start(300)
            self._started = True
            return True
        except Exception:
            return False

    def stop(self):
        """停止监听剪贴板"""
        self._timer.stop()
        self._started = False

    def _poll(self):
        change_count = get_clipboard_change_count()
        if change_count is None:
            return
        if self._change_count is None:
            self._change_count = change_count
            return
        if change_count != self._change_count:
            self._change_count = change_count
            self.clipboard_changed.emit()
