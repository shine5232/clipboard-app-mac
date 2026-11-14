"""macOS 辅助功能权限检查。"""

import ctypes


def accessibility_is_trusted():
    """当前进程是否已获得辅助功能权限。检查失败时返回 True，避免误报。"""
    try:
        app_services = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        )
        app_services.AXIsProcessTrusted.restype = ctypes.c_bool
        return bool(app_services.AXIsProcessTrusted())
    except Exception:
        return True
