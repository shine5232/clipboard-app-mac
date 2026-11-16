"""macOS 全局快捷键。

pynput 的 GlobalHotKeys 按字符匹配。按住 Option 时 V 会变成 √，
所以 <cmd>+<alt>+v 在 macOS 上永远对不上。这里改用虚拟键码和修饰键标志。
"""

import os
import threading
import time


KVK_ANSI_C = 0x08
KVK_ANSI_V = 0x09
KVK_ANSI_Q = 0x0C

# 按住触发键时系统会自动重复 keydown，避免一次快捷键触发多次。
HOTKEY_COOLDOWN_SECONDS = 0.8


class MacHotkeyListener:
    """监听 Cmd+Option+V、Cmd+Shift+C、Cmd+Shift+Q。"""

    def __init__(self, on_paste, on_toggle, on_quit):
        self.on_paste = on_paste
        self.on_toggle = on_toggle
        self.on_quit = on_quit
        self.error = ""
        self._running = False
        self._thread = None
        self._loop = None
        self._tap = None
        self._pynput_listener = None
        self._last_fire = {}
        self._suspend_until = 0

    def start(self):
        if self._start_quartz():
            return True
        if self._start_pynput():
            return True
        if not self.error:
            self.error = "无法创建键盘监听，请授予辅助功能权限后重新打开"
        return False

    def stop(self):
        self._running = False
        listener = self._pynput_listener
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass
        loop = self._loop
        if loop is not None:
            try:
                from Quartz import CFRunLoopStop
                CFRunLoopStop(loop)
            except Exception:
                pass

    def _start_quartz(self):
        try:
            from Quartz import CGEventTapCreate
        except Exception as exc:
            self.error = "未加载 Quartz，打包时需要包含 pyobjc：%s" % exc
            return False

        self._running = True
        ready = threading.Event()
        self._thread = threading.Thread(
            target=self._quartz_loop,
            args=(ready,),
            name="clipboard-hotkeys",
            daemon=True,
        )
        self._thread.start()
        ready.wait(1.5)
        if self._tap is None:
            self._running = False
            if not self.error:
                self.error = "辅助功能未授权给当前应用，快捷键无法监听"
            return False
        return True

    def _quartz_loop(self, ready):
        try:
            from Quartz import (
                CFMachPortCreateRunLoopSource,
                CFRunLoopAddSource,
                CFRunLoopGetCurrent,
                CFRunLoopRunInMode,
                CGEventTapCreate,
                CGEventTapEnable,
                kCFRunLoopDefaultMode,
                kCGEventTapOptionDefault,
                kCGHeadInsertEventTap,
                kCGSessionEventTap,
                CGEventMaskBit,
                kCGEventKeyDown,
                kCGEventFlagsChanged,
            )
            mask = (
                CGEventMaskBit(kCGEventKeyDown)
                | CGEventMaskBit(kCGEventFlagsChanged)
            )
            tap = CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionDefault,
                mask,
                self._handle_event,
                None,
            )
            self._tap = tap
            if tap is None:
                ready.set()
                return

            source = CFMachPortCreateRunLoopSource(None, tap, 0)
            self._loop = CFRunLoopGetCurrent()
            CFRunLoopAddSource(self._loop, source, kCFRunLoopDefaultMode)
            CGEventTapEnable(tap, True)
            ready.set()

            while self._running:
                CFRunLoopRunInMode(kCFRunLoopDefaultMode, 0.5, False)
        except Exception as exc:
            self.error = "快捷键监听失败：%s" % exc
            self._tap = None
            ready.set()
        finally:
            self._loop = None

    def _handle_event(self, proxy, event_type, event, refcon):
        try:
            from Quartz import (
                CGEventGetFlags,
                CGEventGetIntegerValueField,
                CGEventGetType,
                CGEventTapEnable,
                kCGEventKeyDown,
                kCGKeyboardEventKeycode,
                kCGEventFlagMaskAlternate,
                kCGEventFlagMaskCommand,
                kCGEventFlagMaskControl,
                kCGEventFlagMaskShift,
                kCGEventSourceUnixProcessID,
            )
        except Exception:
            return event

        disabled = {0xFFFFFFFE, 0xFFFFFFFF, -2, -1}
        try:
            from Quartz import kCGEventTapDisabledByTimeout, kCGEventTapDisabledByUserInput
            disabled.update({kCGEventTapDisabledByTimeout, kCGEventTapDisabledByUserInput})
        except Exception:
            pass
        if event is None or event_type in disabled:
            if self._tap is not None and event_type in disabled:
                CGEventTapEnable(self._tap, True)
            return event

        if event_type != kCGEventKeyDown:
            return event

        try:
            sender = int(CGEventGetIntegerValueField(event, kCGEventSourceUnixProcessID) or 0)
        except Exception:
            sender = 0
        if sender == os.getpid():
            return event

        if time.monotonic() < self._suspend_until:
            return event

        flags = CGEventGetFlags(event)
        cmd = bool(flags & kCGEventFlagMaskCommand)
        alt = bool(flags & kCGEventFlagMaskAlternate)
        shift = bool(flags & kCGEventFlagMaskShift)
        ctrl = bool(flags & kCGEventFlagMaskControl)
        keycode = int(CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode))

        action = None
        if cmd and alt and not shift and not ctrl and keycode == KVK_ANSI_V:
            action = self.on_paste
        elif cmd and shift and not alt and not ctrl and keycode == KVK_ANSI_C:
            action = self.on_toggle
        elif cmd and shift and not alt and not ctrl and keycode == KVK_ANSI_Q:
            action = self.on_quit

        if action is None:
            return event
        if not self._mark_fired(keycode):
            return None

        # 粘贴期间放行后续按键，避免把我们自己发出的 Command+V 吃掉。
        self._suspend_until = time.monotonic() + 1.2
        try:
            action()
        except Exception:
            pass
        return None

    def _mark_fired(self, keycode):
        now = time.monotonic()
        if now - self._last_fire.get(keycode, 0) < HOTKEY_COOLDOWN_SECONDS:
            return False
        self._last_fire[keycode] = now
        return True

    def _start_pynput(self):
        """Quartz 事件钩子不可用时，按虚拟键码监听，不走字符匹配。"""
        try:
            from pynput.keyboard import Listener, Key
        except Exception as exc:
            self.error = self.error or ("pynput 不可用：%s" % exc)
            return False

        modifiers = set()

        def marker(key):
            vk = getattr(key, "vk", None)
            if vk is None and getattr(key, "value", None) is not None:
                vk = getattr(key.value, "vk", None)
            return key, vk

        def on_press(key):
            identity, vk = marker(key)
            if identity in (Key.cmd, Key.cmd_l, Key.cmd_r):
                modifiers.add("cmd")
            elif identity in (Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr):
                modifiers.add("alt")
            elif identity in (Key.shift, Key.shift_l, Key.shift_r):
                modifiers.add("shift")
            elif identity in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
                modifiers.add("ctrl")

            action = None
            if vk == KVK_ANSI_V and modifiers >= {"cmd", "alt"} and "shift" not in modifiers and "ctrl" not in modifiers:
                action = self.on_paste
            elif vk == KVK_ANSI_C and modifiers >= {"cmd", "shift"} and "alt" not in modifiers and "ctrl" not in modifiers:
                action = self.on_toggle
            elif vk == KVK_ANSI_Q and modifiers >= {"cmd", "shift"} and "alt" not in modifiers and "ctrl" not in modifiers:
                action = self.on_quit
            if action is None or not self._mark_fired(vk):
                return
            self._suspend_until = time.monotonic() + 1.2
            try:
                action()
            except Exception:
                pass

        def on_release(key):
            identity, _vk = marker(key)
            if identity in (Key.cmd, Key.cmd_l, Key.cmd_r):
                modifiers.discard("cmd")
            elif identity in (Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr):
                modifiers.discard("alt")
            elif identity in (Key.shift, Key.shift_l, Key.shift_r):
                modifiers.discard("shift")
            elif identity in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
                modifiers.discard("ctrl")

        try:
            listener = Listener(on_press=on_press, on_release=on_release)
            listener.start()
            time.sleep(0.2)
            if not getattr(listener, "running", True):
                self.error = self.error or "pynput 快捷键监听没有启动"
                return False
            self._pynput_listener = listener
            self._running = True
            self.error = ""
            return True
        except Exception as exc:
            self.error = self.error or ("pynput 快捷键监听失败：%s" % exc)
            return False
