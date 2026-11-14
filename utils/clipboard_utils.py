"""
剪贴板工具模块
使用 macOS NSPasteboard 读写文本，失败时回退到 pyperclip 或 Qt。
"""

import time


def get_clipboard_change_count():
    """返回剪贴板变更计数。无法读取时用当前文本代替。"""
    try:
        from AppKit import NSPasteboard
        return int(NSPasteboard.generalPasteboard().changeCount())
    except Exception:
        return get_clipboard_text()


def get_clipboard_text():
    """
    安全地获取剪贴板文本，支持重试

    Returns:
        str: 剪贴板文本内容，失败返回 None
    """
    max_retries = 3
    retry_delay = 0.05

    for attempt in range(max_retries):
        text = _read_pasteboard()
        if text is not None:
            return text
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    return None


def set_clipboard_text(text):
    """
    安全地设置剪贴板文本，支持重试

    Args:
        text (str): 要设置的文本内容

    Returns:
        bool: 成功返回 True，失败返回 False
    """
    if text is None:
        text = ""

    max_retries = 3
    retry_delay = 0.05

    for attempt in range(max_retries):
        if _write_pasteboard(text):
            return True
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    return False


def _read_pasteboard():
    try:
        from AppKit import NSPasteboard
        value = NSPasteboard.generalPasteboard().stringForType_("public.utf8-plain-text")
        return "" if value is None else str(value)
    except Exception:
        pass

    try:
        import pyperclip
        value = pyperclip.paste()
        return "" if value is None else str(value)
    except Exception:
        pass

    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            return app.clipboard().text() or ""
    except Exception:
        pass
    return None


def _write_pasteboard(text):
    try:
        from AppKit import NSPasteboard
        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        if text == "":
            return True
        return bool(pasteboard.setString_forType_(text, "public.utf8-plain-text"))
    except Exception:
        pass

    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass

    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            app.clipboard().setText(text)
            return True
    except Exception:
        pass
    return False


def process_clipboard_text(text):
    """
    处理剪贴板文本，将多行文本分割成列表

    Args:
        text (str): 原始文本

    Returns:
        list: 处理后的文本列表
    """
    if not text:
        return []

    if '\n' in text or '\r' in text:
        lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        return [line.strip() for line in lines if line.strip()]
    else:
        return [text.strip()] if text.strip() else []
