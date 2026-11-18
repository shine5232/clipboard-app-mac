"""
macOS 键盘模拟模块
使用 pyobjc 的 Quartz 实现键盘输入
"""

import time

try:
    from Quartz import (
        CGEventCreateKeyboardEvent,
        CGEventPost,
        CGEventSetFlags,
        CGEventSourceCreate,
        kCGHIDEventTap,
        kCGEventFlagMaskCommand,
        kCGEventSourceStateHIDSystemState,
    )
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False
    kCGEventFlagMaskCommand = 0
    kCGEventSourceStateHIDSystemState = 1


kVK_ANSI_V = 0x09
kVK_Return = 0x24

# 左右 Command / Option / Shift / Control，以及触发粘贴的 V。
_MODIFIER_KEYCODES = (
    0x37, 0x36,
    0x3A, 0x3D,
    0x38, 0x3C,
    0x3B, 0x3E,
    kVK_ANSI_V,
)


def _event_source():
    if not QUARTZ_AVAILABLE:
        return None
    return CGEventSourceCreate(kCGEventSourceStateHIDSystemState)


def release_modifiers():
    """松开快捷键残留的修饰键，避免随后的 Command+V 被 Option 吃掉。"""
    if not QUARTZ_AVAILABLE:
        return False
    source = _event_source()
    for keycode in _MODIFIER_KEYCODES:
        event_up = CGEventCreateKeyboardEvent(source, keycode, False)
        CGEventSetFlags(event_up, 0)
        CGEventPost(kCGHIDEventTap, event_up)
    time.sleep(0.06)
    return True


def _post_key(key_code, flags=0):
    source = _event_source()
    event_down = CGEventCreateKeyboardEvent(source, key_code, True)
    event_up = CGEventCreateKeyboardEvent(source, key_code, False)
    CGEventSetFlags(event_down, flags)
    CGEventSetFlags(event_up, flags)
    CGEventPost(kCGHIDEventTap, event_down)
    time.sleep(0.02)
    CGEventPost(kCGHIDEventTap, event_up)
    time.sleep(0.02)


def can_send_keys():
    """当前进程能否把按键事件发给其他应用（辅助功能权限）。"""
    try:
        from utils.permissions import accessibility_is_trusted
        return bool(accessibility_is_trusted())
    except Exception:
        return True


def simulate_paste():
    """
    模拟 Command+V 粘贴操作

    CGEventPost 在没有辅助功能权限时会被系统静默丢弃。
    这里仍然照常发送（权限检测本身可能失准），但把检测结果返回给上层，
    让上层能在“发了也没用”的时候提示用户去授权。

    Returns:
        bool: 事件已发出且当前进程有辅助功能权限时返回 True
    """
    trusted = can_send_keys()

    if QUARTZ_AVAILABLE:
        try:
            release_modifiers()
            _post_key(kVK_ANSI_V, kCGEventFlagMaskCommand)
            return trusted
        except Exception:
            return False

    try:
        from pynput.keyboard import Controller, Key
        keyboard = Controller()
        for key in (Key.cmd, Key.alt, Key.shift, Key.ctrl):
            try:
                keyboard.release(key)
            except Exception:
                pass
        time.sleep(0.06)
        with keyboard.pressed(Key.cmd):
            keyboard.press("v")
            keyboard.release("v")
        return trusted
    except Exception:
        return False


def simulate_return():
    """模拟回车。"""
    if QUARTZ_AVAILABLE:
        try:
            _post_key(kVK_Return)
            return True
        except Exception:
            return False

    try:
        from pynput.keyboard import Controller, Key
        keyboard = Controller()
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
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
    if release_modifiers():
        return
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
