"""
macOS 窗口管理模块
提供 macOS 窗口焦点管理功能
"""

import time

try:
    from AppKit import NSWorkspace, NSRunningApplication
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    )
    APPKIT_AVAILABLE = True
except ImportError:
    APPKIT_AVAILABLE = False


def get_foreground_window():
    """
    获取当前活动窗口的信息

    Returns:
        dict: 窗口信息,失败返回 None
    """
    if not APPKIT_AVAILABLE:
        return None

    try:
        # 获取当前活动应用
        active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if active_app:
            return {
                'pid': active_app.processIdentifier(),
                'name': active_app.localizedName(),
                'bundle_id': active_app.bundleIdentifier()
            }
        return None
    except Exception:
        return None


def set_foreground_window(window_info):
    """
    激活指定窗口

    Args:
        window_info (dict): 窗口信息(包含 pid)

    Returns:
        bool: 成功返回 True,失败返回 False
    """
    if not APPKIT_AVAILABLE or not window_info:
        return False

    try:
        pid = window_info.get('pid')
        if not pid:
            return False

        # 根据 pid 激活应用
        app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
        if app:
            result = app.activateWithOptions_(1 << 1)  # NSApplicationActivateIgnoringOtherApps
            return bool(result)
        return False
    except Exception:
        return False


class WindowFocusManager:
    """
    窗口焦点管理器
    用于记录和恢复窗口焦点
    """

    def __init__(self):
        self.previous_window = None

    def save_current_window(self):
        """
        保存当前活动窗口

        Returns:
            bool: 成功返回 True,失败返回 False
        """
        self.previous_window = get_foreground_window()
        return bool(self.previous_window)

    def restore_previous_window(self, wait_time=0.1):
        """
        恢复之前保存的窗口焦点

        Args:
            wait_time (float): 等待时间(秒)

        Returns:
            bool: 成功返回 True,失败返回 False
        """
        if not self.previous_window:
            return False

        success = set_foreground_window(self.previous_window)

        if wait_time > 0:
            time.sleep(wait_time)

        return success

    def get_previous_window(self):
        """
        获取之前保存的窗口信息

        Returns:
            dict: 窗口信息
        """
        return self.previous_window
