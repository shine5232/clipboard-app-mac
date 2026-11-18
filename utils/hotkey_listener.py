"""macOS 全局快捷键。

pynput 的 GlobalHotKeys 按字符匹配。按住 Option 时 V 会变成 √，
所以 <cmd>+<alt>+v 在 macOS 上永远对不上。这里改用虚拟键码和修饰键标志。
"""

import os
import threading
import time

from utils.debug_log import log

# 所有 Quartz 符号在模块加载时解析一次。绝不能放在 event tap 回调里 import：
# 回调有严格的时间预算，超时会被系统禁用 tap。
try:
    from Quartz import (
        CFMachPortCreateRunLoopSource,
        CFRunLoopAddSource,
        CFRunLoopGetCurrent,
        CFRunLoopGetMain,
        CFRunLoopRemoveSource,
        CFRunLoopRunInMode,
        CFRunLoopStop,
        CGEventGetFlags,
        CGEventGetIntegerValueField,
        CGEventTapCreate,
        CGEventTapEnable,
        CGEventMaskBit,
        kCFRunLoopCommonModes,
        kCFRunLoopDefaultMode,
        kCGEventFlagMaskAlternate,
        kCGEventFlagMaskCommand,
        kCGEventFlagMaskControl,
        kCGEventFlagMaskShift,
        kCGEventFlagsChanged,
        kCGEventKeyDown,
        kCGEventSourceUnixProcessID,
        kCGKeyboardEventKeycode,
        kCGEventTapOptionDefault,
        kCGHeadInsertEventTap,
        kCGSessionEventTap,
    )
    QUARTZ_OK = True
except Exception as _quartz_exc:  # pragma: no cover
    QUARTZ_OK = False
    QUARTZ_ERROR = repr(_quartz_exc)

try:
    from Quartz import kCGEventTapDisabledByTimeout, kCGEventTapDisabledByUserInput
    _DISABLED_EVENTS = {kCGEventTapDisabledByTimeout, kCGEventTapDisabledByUserInput}
except Exception:  # pragma: no cover
    _DISABLED_EVENTS = set()

# ---------------------------------------------------------------------------
# 系统级热键（Carbon RegisterEventHotKey）
#
# CGEventTap 这条路在本机实测“创建成功、却收不到 keyDown”，换组合键没有任何意义：
# 事件根本到不了进程，什么组合都匹配不上。系统热键不同，它由 WindowServer 直接
# 派发给注册它的 app：
#   * 不依赖辅助功能权限
#   * 不依赖 tap 是否收到事件
#   * 命中后组合键不会继续传给前台 App（不会有“粘贴并匹配样式”的副作用）
# 用 ctypes 调 Carbon，不引入额外 Python 依赖，打包也不需要额外 collect。
# ---------------------------------------------------------------------------
CARBON_PATH = "/System/Library/Frameworks/Carbon.framework/Carbon"

_K_EVENT_CLASS_KEYBOARD = 0x6B657962          # 'keyb'
_K_EVENT_HOTKEY_PRESSED = 5
_K_EVENT_PARAM_DIRECT_OBJECT = 0x2D2D2D2D     # '----'
_TYPE_EVENT_HOTKEY_ID = 0x686B6964            # 'hkid'
_K_CLIP_SIGNATURE = 0x434C4950                # 'CLIP'

_CARBON_MODS = {"cmd": 0x0100, "shift": 0x0200, "alt": 0x0800, "ctrl": 0x1000}

try:
    import ctypes
    from ctypes import (CFUNCTYPE, POINTER, Structure, byref, c_int, c_int32,
                        c_uint32, c_void_p)

    _carbon = ctypes.CDLL(CARBON_PATH)

    class _EventTypeSpec(Structure):
        _fields_ = [("eventClass", c_uint32), ("eventKind", c_uint32)]

    class _EventHotKeyID(Structure):
        _fields_ = [("signature", c_uint32), ("id", c_uint32)]

    _carbon.GetApplicationEventTarget.restype = c_void_p
    _carbon.GetApplicationEventTarget.argtypes = []
    _carbon.RegisterEventHotKey.restype = c_int32
    _carbon.RegisterEventHotKey.argtypes = [
        c_uint32, c_uint32, _EventHotKeyID, c_void_p, c_uint32, POINTER(c_void_p)]
    _carbon.UnregisterEventHotKey.restype = c_int32
    _carbon.UnregisterEventHotKey.argtypes = [c_void_p]
    _carbon.InstallEventHandler.restype = c_int32
    _carbon.InstallEventHandler.argtypes = [
        c_void_p, c_void_p, c_int, POINTER(_EventTypeSpec), c_void_p, POINTER(c_void_p)]
    _carbon.RemoveEventHandler.restype = c_int32
    _carbon.RemoveEventHandler.argtypes = [c_void_p]
    _carbon.GetEventParameter.restype = c_int32
    _carbon.GetEventParameter.argtypes = [
        c_void_p, c_uint32, c_uint32, c_void_p, c_int, POINTER(c_int), POINTER(_EventHotKeyID)]

    _HOTKEY_HANDLER = CFUNCTYPE(c_int32, c_void_p, c_void_p, c_void_p)
    CARBON_OK = True
    CARBON_ERROR = ""
except Exception as _carbon_exc:  # pragma: no cover
    CARBON_OK = False
    CARBON_ERROR = repr(_carbon_exc)
    _HOTKEY_HANDLER = None


KVK_ANSI_C = 0x08
KVK_ANSI_V = 0x09
KVK_ANSI_Q = 0x0C

# 批量粘贴的候选组合。⌥⌘V 在不少 App 里被“特殊粘贴”占用，所以默认用 ⌃⌘V。
PASTE_HOTKEY_PRESETS = {
    "ctrl_cmd_v": {
        "label": "⌃⌘V",
        "keycode": KVK_ANSI_V,
        "mods": frozenset({"cmd", "ctrl"}),
    },
    "cmd_shift_v": {
        "label": "⇧⌘V",
        "keycode": KVK_ANSI_V,
        "mods": frozenset({"cmd", "shift"}),
    },
    "cmd_alt_v": {
        "label": "⌥⌘V",
        "keycode": KVK_ANSI_V,
        "mods": frozenset({"cmd", "alt"}),
    },
}
DEFAULT_PASTE_HOTKEY = "ctrl_cmd_v"

# 按住触发键时系统会自动重复 keydown，避免一次快捷键触发多次。
HOTKEY_COOLDOWN_SECONDS = 0.8


def paste_hotkey_label(name):
    """给界面用的组合键文本。"""
    preset = PASTE_HOTKEY_PRESETS.get(name) or PASTE_HOTKEY_PRESETS[DEFAULT_PASTE_HOTKEY]
    return preset["label"]


class MacHotkeyListener:
    """监听 Cmd+Option+V、Cmd+Shift+C、Cmd+Shift+Q。"""

    def __init__(self, on_paste, on_toggle, on_quit, paste_hotkey=DEFAULT_PASTE_HOTKEY):
        self.on_paste = on_paste
        self.on_toggle = on_toggle
        self.on_quit = on_quit
        self.error = ""
        self.paste_keycode = KVK_ANSI_V
        self.paste_mods = PASTE_HOTKEY_PRESETS[DEFAULT_PASTE_HOTKEY]["mods"]
        self.set_paste_hotkey(paste_hotkey)
        self._running = False
        self._thread = None
        self._loop = None
        self._tap = None
        self._tap_callback = None
        self._runloop_source = None
        self._event_count = 0
        self._carbon_handler = None
        self._carbon_handler_ref = None
        self._carbon_hotkeys = []
        self._carbon_ok = False
        self._nsevent_monitor = None
        self._nsevent_handler = None
        self._pynput_listener = None
        self._last_fire = {}
        self._suspend_until = 0

    def set_paste_hotkey(self, name):
        preset = PASTE_HOTKEY_PRESETS.get(name) or PASTE_HOTKEY_PRESETS[DEFAULT_PASTE_HOTKEY]
        self.paste_hotkey = name if name in PASTE_HOTKEY_PRESETS else DEFAULT_PASTE_HOTKEY
        self.paste_keycode = preset["keycode"]
        self.paste_mods = preset["mods"]

    @property
    def paste_hotkey_label(self):
        return PASTE_HOTKEY_PRESETS[self.paste_hotkey]["label"]

    def start(self):
        log("hotkey.start preset=%s keycode=0x%02x mods=%s"
            % (self.paste_hotkey, self.paste_keycode, sorted(self.paste_mods)))

        # 首选：系统级热键。不依赖辅助功能，也不依赖 CGEventTap 能否收到事件，
        # 而且系统会让组合键不再传给前台 App。
        if self._start_carbon():
            self._carbon_ok = True
            self._running = True
            self.error = ""
            # 额外再挂一条 tap 做保险：能装就装（需要辅助功能），装不上也不影响热键。
            # 两条通道都命中时由 _fire 的冷却去重，不会重复粘贴。
            if self._start_quartz():
                log("hotkey.start -> 系统热键就绪（另挂了 tap 保险），不依赖辅助功能权限")
            else:
                log("hotkey.start -> 系统热键就绪（tap 未挂上，不影响快捷键）")
            # tap 的失败信息只表示“没有辅助功能”，不该污染整体的快捷键状态
            self.error = ""
            return True
        log("hotkey.start -> 系统热键不可用，回退 CGEventTap:", self.error)

        quartz_ok = self._start_quartz()
        log("hotkey.start -> Quartz tap:", quartz_ok, "|", self.error)

        # NSEvent 全局监听作为备用通道：Quartz tap 在某些环境下会
        # “创建成功但收不到事件”，两条通道同时挂着，任一条触发即可（靠冷却去重）。
        nsevent_ok = self._start_nsevent()

        if quartz_ok or nsevent_ok:
            self.error = ""
            log("hotkey.start -> 就绪 quartz=%s nsevent=%s" % (quartz_ok, nsevent_ok))
            return True

        if self._start_pynput():
            log("hotkey.start -> pynput 回退可用")
            self.error = ""
            return True

        log("hotkey.start -> 全部失败:", self.error)
        if not self.error:
            self.error = "无法注册快捷键，请重启应用或检查系统设置"
        return False

    def _start_carbon(self):
        """注册系统级热键（粘贴 / 显示隐藏 / 退出）。"""
        if not CARBON_OK:
            self.error = "系统热键接口不可用：%s" % CARBON_ERROR
            log("carbon: 不可用", CARBON_ERROR)
            return False

        try:
            target = _carbon.GetApplicationEventTarget()
            if not target:
                log("carbon: GetApplicationEventTarget 返回空")
                return False

            handler = _HOTKEY_HANDLER(self._carbon_handle)
            self._carbon_handler = handler  # 必须自己持有，否则回调被回收后热键静默失效

            spec = _EventTypeSpec(_K_EVENT_CLASS_KEYBOARD, _K_EVENT_HOTKEY_PRESSED)
            href = c_void_p()
            status = _carbon.InstallEventHandler(
                target, ctypes.cast(handler, c_void_p), 1, byref(spec), None, byref(href))
            if status != 0:
                log("carbon: InstallEventHandler 失败 status=%s" % status)
                self.error = "安装热键处理器失败（status=%s）" % status
                return False
            self._carbon_handler_ref = href

            plan = [
                (1, "paste", self.paste_keycode, self.paste_mods),
                (2, "toggle", KVK_ANSI_C, frozenset({"cmd", "shift"})),
                (3, "quit", KVK_ANSI_Q, frozenset({"cmd", "shift"})),
            ]
            registered = 0
            for hotkey_id, label, keycode, mods in plan:
                modifier = 0
                for name in mods:
                    modifier |= _CARBON_MODS.get(name, 0)
                ref = c_void_p()
                st = _carbon.RegisterEventHotKey(
                    keycode, modifier,
                    _EventHotKeyID(_K_CLIP_SIGNATURE, hotkey_id), target, 0, byref(ref))
                if st == 0 and ref.value:
                    self._carbon_hotkeys.append(ref)
                    registered += 1
                    log("carbon: 已注册 %s keycode=0x%02x mods=%s" % (label, keycode, sorted(mods)))
                else:
                    log("carbon: 注册失败 %s status=%s（-9878=已被其它程序占用）" % (label, st))

            if registered == 0:
                self.error = "快捷键全部注册失败，可能已被其它程序占用"
                return False
            return True
        except Exception as exc:
            self.error = "系统热键注册异常：%s" % exc
            log("carbon: 注册异常", repr(exc))
            return False

    def _carbon_handle(self, call_ref, event, user_data):
        try:
            hotkey = _EventHotKeyID()
            size = c_int(ctypes.sizeof(_EventHotKeyID))
            _carbon.GetEventParameter(
                event, _K_EVENT_PARAM_DIRECT_OBJECT, _TYPE_EVENT_HOTKEY_ID, None,
                ctypes.sizeof(_EventHotKeyID), byref(size), byref(hotkey))
            hotkey_id = int(hotkey.id)
            action = {1: "paste", 2: "toggle", 3: "quit"}.get(hotkey_id)
            log("carbon: 热键触发 id=%s -> %s" % (hotkey_id, action))
            if action:
                self._fire(action, "carbon")
        except Exception as exc:
            log("carbon: 回调异常", repr(exc))
        return 0


    def _start_nsevent(self):
        """用 NSEvent 全局监听做第二条通道（不吞事件，只用于触发）。"""
        try:
            from AppKit import NSEvent, NSKeyDownMask
        except Exception as exc:
            log("nsevent: AppKit 导入失败", repr(exc))
            return False

        try:
            def handler(event):
                try:
                    self._nsevent_handle(event)
                except Exception as exc:
                    log("nsevent: 回调异常", repr(exc))

            monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                NSKeyDownMask, handler)
            if monitor is None:
                log("nsevent: 安装返回 None（可能缺少监听权限）")
                return False

            # 没授权时它也会“安装成功”，但一个事件都收不到，不能据此认为可用
            try:
                from utils.permissions import accessibility_is_trusted
                if not accessibility_is_trusted():
                    log("nsevent: 已安装但无辅助功能权限，判定无效")
                    try:
                        NSEvent.removeMonitor_(monitor)
                    except Exception:
                        pass
                    return False
            except Exception:
                pass

            self._nsevent_monitor = monitor
            self._nsevent_handler = handler
            log("nsevent: 全局监听已安装")
            return True
        except Exception as exc:
            log("nsevent: 安装失败", repr(exc))
            return False

    def _nsevent_handle(self, event):
        try:
            from AppKit import (
                NSEventModifierFlagCommand as CMD_F,
                NSEventModifierFlagControl as CTRL_F,
                NSEventModifierFlagOption as ALT_F,
                NSEventModifierFlagShift as SHIFT_F,
            )
        except Exception:
            return

        flags = event.modifierFlags()
        mods = set()
        if flags & CMD_F:
            mods.add("cmd")
        if flags & ALT_F:
            mods.add("alt")
        if flags & SHIFT_F:
            mods.add("shift")
        if flags & CTRL_F:
            mods.add("ctrl")
        keycode = event.keyCode()

        if "cmd" in mods or "ctrl" in mods:
            log("nsevent key keycode=0x%02x mods=%s" % (keycode, sorted(mods)))

        self._dispatch(keycode, mods, "nsevent")

    def stop(self):
        self._running = False

        # 先注销系统热键，否则重新设置快捷键时旧组合会继续被这个进程占着。
        for ref in list(self._carbon_hotkeys or []):
            try:
                _carbon.UnregisterEventHotKey(ref)
            except Exception:
                pass
        self._carbon_hotkeys = []
        handler_ref = self._carbon_handler_ref
        if handler_ref is not None:
            try:
                _carbon.RemoveEventHandler(handler_ref)
            except Exception:
                pass
            self._carbon_handler_ref = None
        self._carbon_handler = None
        self._carbon_ok = False

        monitor = getattr(self, "_nsevent_monitor", None)
        if monitor is not None:
            try:
                from AppKit import NSEvent
                NSEvent.removeMonitor_(monitor)
            except Exception:
                pass
            self._nsevent_monitor = None
        listener = self._pynput_listener
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass
        source = getattr(self, "_runloop_source", None)
        loop = self._loop
        if source is not None and loop is not None:
            try:
                CFRunLoopRemoveSource(loop, source, kCFRunLoopCommonModes)
            except Exception:
                pass
        if self._tap is not None:
            try:
                CGEventTapEnable(self._tap, False)
            except Exception:
                pass
        self._runloop_source = None
        self._tap = None

    def _start_quartz(self):
        """把 event tap 装到主 runloop 上，由 App 自己的事件循环驱动。

        之前是在后台线程里自建 runloop 跑 tap，实测只收到第一个事件就再无回调
        （runloop 进出之间的事件会丢）。装到主 runloop 既不会丢事件，
        也不会有 GIL 争用问题。
        """
        if not QUARTZ_OK:
            self.error = "未加载 Quartz，打包时需要包含 pyobjc：%s" % QUARTZ_ERROR
            return False

        try:
            mask = (
                CGEventMaskBit(kCGEventKeyDown)
                | CGEventMaskBit(kCGEventFlagsChanged)
            )
            # 必须自己持有回调引用：只把 self._handle_event 传进 C 侧，Python 侧对象可能被回收，
            # tap 还在但永远不再回调。
            self._tap_callback = self._handle_event
            tap = CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionDefault,
                mask,
                self._tap_callback,
                None,
            )
            if tap is None:
                log("quartz: CGEventTapCreate 返回 None（无辅助功能权限）")
                if not self.error:
                    self.error = "辅助功能未授权给当前应用，快捷键无法监听"
                return False

            source = CFMachPortCreateRunLoopSource(None, tap, 0)
            self._runloop_source = source
            self._loop = CFRunLoopGetMain()
            CFRunLoopAddSource(self._loop, source, kCFRunLoopCommonModes)
            CGEventTapEnable(tap, True)
            self._tap = tap
            self._running = True
            log("quartz: tap 已安装到主 runloop 并启用")
            return True
        except Exception as exc:
            self.error = "快捷键监听失败：%s" % exc
            log("quartz: 安装异常", repr(exc))
            self._tap = None
            return False

    def _handle_event(self, proxy, event_type, event, refcon):
        # 这里运行在系统的事件 tap 线程上，任何异常都必须吞掉并记录，
        # 否则系统会直接把 tap 禁用，表现为“快捷键彻底失灵”。
        try:
            return self._handle_event_inner(event_type, event)
        except Exception as exc:
            log("tap 回调异常:", repr(exc))
            return event

    def _handle_event_inner(self, event_type, event):
        self._event_count += 1
        if self._event_count == 1 or self._event_count % 40 == 0:
            log("tap 收到事件 #%d type=%s" % (self._event_count, event_type))

        disabled = {0xFFFFFFFE, 0xFFFFFFFF, -2, -1} | _DISABLED_EVENTS
        if event is None or event_type in disabled:
            if self._tap is not None and event_type in disabled:
                log("quartz: tap 被禁用(event_type=%s)，重新启用" % event_type)
                CGEventTapEnable(self._tap, True)
            return event

        if event_type != kCGEventKeyDown:
            # 修饰键变化：记下是哪个键、带了什么 flags，用来判断组合键是否被系统识别
            try:
                kc = int(CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode))
                fl = CGEventGetFlags(event)
                log("flagsChanged keycode=0x%02x flags=0x%x" % (kc, fl))
            except Exception:
                pass
            return event

        try:
            sender = int(CGEventGetIntegerValueField(event, kCGEventSourceUnixProcessID) or 0)
        except Exception:
            sender = 0
        if sender == os.getpid():
            log("keydown: 忽略自己进程合成的事件")
            return event

        if time.monotonic() < self._suspend_until:
            log("keydown: 处于粘贴后的放行窗口，跳过")
            return event

        flags = CGEventGetFlags(event)
        mods = set()
        if flags & kCGEventFlagMaskCommand:
            mods.add("cmd")
        if flags & kCGEventFlagMaskAlternate:
            mods.add("alt")
        if flags & kCGEventFlagMaskShift:
            mods.add("shift")
        if flags & kCGEventFlagMaskControl:
            mods.add("ctrl")
        keycode = int(CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode))

        # 记录所有 keyDown，才能判断到底是没收到、还是 flags 对不上
        log("keydown keycode=0x%02x flags=0x%x mods=%s target=0x%02x/%s"
            % (keycode, flags, sorted(mods), self.paste_keycode, sorted(self.paste_mods)))

        if self._dispatch(keycode, mods, "quartz"):
            return None
        return event

    def _dispatch(self, keycode, mods, source):
        """事件通道共用：匹配组合键并执行动作。命中返回 True。"""
        label = self._match(keycode, mods)
        if label is None:
            return False
        self._fire(label, source)
        return True

    def _match(self, keycode, mods):
        if keycode == self.paste_keycode and mods == set(self.paste_mods):
            return "paste"
        if keycode == KVK_ANSI_C and mods == {"cmd", "shift"}:
            return "toggle"
        if keycode == KVK_ANSI_Q and mods == {"cmd", "shift"}:
            return "quit"
        return None

    def _fire(self, label, source):
        """统一出口：冷却去重 + 放行窗口 + 执行动作。多条通道同时挂也不会重复触发。"""
        if not self._mark_fired(label):
            log("key: 命中但被冷却忽略(%s) %s" % (source, label))
            return False

        # 粘贴期间放行后续按键，避免把我们自己发出的 Command+V 吃掉。
        self._suspend_until = time.monotonic() + 1.2
        log("key: 命中快捷键(%s) %s" % (source, label))
        action = {"paste": self.on_paste, "toggle": self.on_toggle,
                  "quit": self.on_quit}.get(label)
        if action is None:
            return False
        try:
            action()
        except Exception as exc:
            log("key: 动作抛异常", repr(exc))
        return True

    def _mark_fired(self, name):
        now = time.monotonic()
        if now - self._last_fire.get(name, 0) < HOTKEY_COOLDOWN_SECONDS:
            return False
        self._last_fire[name] = now
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
            label = self._match(vk, modifiers) if vk is not None else None
            if label is None:
                return
            self._fire(label, "pynput")

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

            # pynput 的线程是活着的，但没授权时系统不会把按键交给它。
            # 这里必须复核权限，否则会误报“监听成功”，用户按键毫无反应且收不到任何提示。
            try:
                from utils.permissions import accessibility_is_trusted
                if not accessibility_is_trusted():
                    try:
                        listener.stop()
                    except Exception:
                        pass
                    if not self.error:
                        self.error = "辅助功能未授权给当前应用，快捷键无法监听"
                    log("pynput: 线程活着但没有辅助功能权限，判定为失败")
                    return False
            except Exception:
                pass

            self._pynput_listener = listener
            self._running = True
            self.error = ""
            return True
        except Exception as exc:
            self.error = self.error or ("pynput 快捷键监听失败：%s" % exc)
            return False
