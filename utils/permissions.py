"""macOS 辅助功能权限检查。"""

import ctypes


def accessibility_is_trusted(prompt=False):
    """当前进程是否已获得辅助功能权限。

    prompt=True 时请求系统把当前应用加入辅助功能列表。
    检查本身失败时返回 True，避免在非 macOS 环境误报。
    """
    trusted = _trusted_with_pyobjc(prompt)
    if trusted is not None:
        return trusted
    if prompt:
        return _trusted_with_ctypes()
    return _trusted_with_ctypes()


def _trusted_with_pyobjc(prompt):
    try:
        import HIServices
    except Exception:
        return None

    try:
        if prompt and hasattr(HIServices, "AXIsProcessTrustedWithOptions"):
            from Foundation import NSDictionary
            options = NSDictionary.dictionaryWithDictionary_({
                "AXTrustedCheckOptionPrompt": True,
            })
            return bool(HIServices.AXIsProcessTrustedWithOptions(options))
        return bool(HIServices.AXIsProcessTrusted())
    except Exception:
        return None


def _trusted_with_ctypes():
    try:
        app_services = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        )
        app_services.AXIsProcessTrusted.restype = ctypes.c_bool
        return bool(app_services.AXIsProcessTrusted())
    except Exception:
        return True
