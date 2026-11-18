"""轻量调试日志。

排查「快捷键没反应 / 粘贴没反应」时用：记录按键匹配、粘贴流程每一步的结果。
写入应用数据目录，异步写盘，避免阻塞键盘事件回调（event tap 回调超时会被系统禁用）。
"""

import atexit
import queue
import threading
import time
from pathlib import Path

LOG_FILE = Path.home() / "Library" / "Application Support" / "ClipboardHelper" / "debug.log"
_MAX_BYTES = 512 * 1024

_queue = queue.Queue()
_started = False
_worker_thread = None
_lock = threading.Lock()


def _worker():
    while True:
        line = _queue.get()
        try:
            if line is None:
                return
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            if LOG_FILE.exists() and LOG_FILE.stat().st_size > _MAX_BYTES:
                LOG_FILE.write_text("", encoding="utf-8")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass
        finally:
            _queue.task_done()


def _ensure_worker():
    global _started, _worker_thread
    if _started:
        return
    with _lock:
        if _started:
            return
        _worker_thread = threading.Thread(target=_worker, name="debug-log", daemon=True)
        _worker_thread.start()
        _started = True


def flush(timeout=1.5):
    """把队列里剩下的日志写完。进程退出前必须调用，否则最后几行会丢。"""
    global _started, _worker_thread
    try:
        if not _started:
            return
        _queue.put_nowait(None)
        thread = _worker_thread
        if thread is not None:
            thread.join(timeout)
        _started = False
        _worker_thread = None
    except Exception:
        pass


atexit.register(flush)


def log(*parts):
    """异步写一行日志，任何异常都吞掉，绝不影响主流程。"""
    try:
        _ensure_worker()
        stamp = time.strftime("%H:%M:%S")
        _queue.put_nowait("%s %s\n" % (stamp, " ".join(str(p) for p in parts)))
    except Exception:
        pass


def reset():
    """每次启动清空，只保留本次运行的记录。"""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE.write_text("", encoding="utf-8")
    except Exception:
        pass
