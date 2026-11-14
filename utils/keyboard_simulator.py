"""
macOS 键盘模拟模块
使用 pyobjc 的 Quartz 实现键盘输入
"""

import time

try:
    from Quartz import (
        CGEventCreateKeyboardEvent,
        CGEventPost,
        kCGHIDEventTap,
        kCGEventFlagMaskCommand,
        CGEventSetFlags
    )
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False


kVK_ANSI_V = 0x09
kVK_Return = 0x24


def _post_key(key_code, flags=0):
    event_down = CGEventCreateKeyboardEvent(None, key_code, True)
    event_up = CGEventCreateKeyboardEvent(None, key_code, False)
    if flags:
        CGEventSetFlags(event_down, flags)
        CGEventSetFlags(event_up, flags)
    CGEventPost(kCGHIDEventTap, event_down)
    time.sleep(0.02)
    CGEventPost(kCGHIDEventTap, event_up)


def simulate_paste():
    """
    模拟 Command+V 粘贴操作

    Returns:
        bool: 成功返回 True,失败返回 False
    """
    if not QUARTZ_AVAILABLE:
        try:
            from pynput.keyboard import Controller, Key
            keyboard = Controller()
            with keyboard.pressed(Key.cmd):
                keyboard.press('v')
                keyboard.release('v')
            return True
        except Exception:
            return False

    try:
        _post_key(kVK_ANSI_V, kCGEventFlagMaskCommand)
        return True
    except Exception:
        return False


def simulate_return():
    """模拟回车。"""
    if not QUARTZ_AVAILABLE:
        try:
            from pynput.keyboard import Controller, Key
            keyboard = Controller()
            keyboard.press(Key.enter)
            keyboard.release(Key.enter)
            return True
        except Exception:
            return False

    try:
        _post_key(kVK_Return)
        return True
    except Exception:
        return False


def simulate_key_combo(*keys, hold_time=0.02):
    """
    模拟组合键操作(通用)

    Args:
        *keys: 键列表 (使用字符串或 pynput.keyboard.Key)
        hold_time (float): 按键保持时间(秒)
    """
    try:
        from pynput.keyboard import Controller
        keyboard = Controller()

        for key in keys:
            keyboard.press(key)
            time.sleep(hold_time)

        for key in reversed(keys):
            keyboard.release(key)
            time.sleep(hold_time)

        return True
    except Exception:
        return False


def release_all_modifiers():
    """释放所有修饰键"""
    try:
        from pynput.keyboard import Controller, Key
        keyboard = Controller()

        for key in [Key.cmd, Key.alt, Key.shift, Key.ctrl]:
            try:
                keyboard.release(key)
            except Exception:
                pass
    except Exception:
        pass
