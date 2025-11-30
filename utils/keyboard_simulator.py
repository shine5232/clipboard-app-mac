"""
macOS 键盘模拟模块
使用 pyobjc 的 Quartz 和 AppKit 实现键盘输入
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


# 虚拟键码 (macOS)
kVK_ANSI_V = 0x09


def simulate_paste():
    """
    模拟 Command+V 粘贴操作

    Returns:
        bool: 成功返回 True,失败返回 False
    """
    if not QUARTZ_AVAILABLE:
        # 如果 Quartz 不可用,尝试使用 pynput
        try:
            from pynput.keyboard import Controller, Key
            keyboard = Controller()

            # Command+V
            with keyboard.pressed(Key.cmd):
                keyboard.press('v')
                keyboard.release('v')
            return True
        except Exception:
            return False

    try:
        # 使用 Quartz 模拟 Command+V
        # 创建 V 键按下事件
        event_down = CGEventCreateKeyboardEvent(None, kVK_ANSI_V, True)
        # 设置 Command 修饰键
        CGEventSetFlags(event_down, kCGEventFlagMaskCommand)

        # 创建 V 键释放事件
        event_up = CGEventCreateKeyboardEvent(None, kVK_ANSI_V, False)

        # 发送事件
        CGEventPost(kCGHIDEventTap, event_down)
        time.sleep(0.02)
        CGEventPost(kCGHIDEventTap, event_up)

        return True
    except Exception:
        return False


def simulate_key_combo(*keys, hold_time=0.02):
    """
    模拟组合键操作(通用)

    Args:
        *keys: 键列表 (使用字符串或 pynput.keyboard.Key)
        hold_time (float): 按键保持时间(秒)

    Example:
        simulate_key_combo(Key.cmd, 'v')  # Command+V
        simulate_key_combo(Key.cmd, Key.shift, 'c')  # Command+Shift+C
    """
    try:
        from pynput.keyboard import Controller
        keyboard = Controller()

        # 按下所有键
        for key in keys:
            keyboard.press(key)
            time.sleep(hold_time)

        # 释放所有键(逆序)
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

        # 释放常用修饰键
        for key in [Key.cmd, Key.alt, Key.shift, Key.ctrl]:
            try:
                keyboard.release(key)
            except:
                pass
    except Exception:
        pass
