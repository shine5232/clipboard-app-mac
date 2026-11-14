"""
剪贴板业务逻辑服务
处理剪贴板数据的核心业务逻辑
"""

import os
import time
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from utils.clipboard_utils import set_clipboard_text, process_clipboard_text
from utils.keyboard_simulator import simulate_paste, simulate_return
from utils.window_manager import get_foreground_window, set_foreground_window


class ClipboardService(QObject):
    """剪贴板服务 - 处理核心业务逻辑"""

    # 信号
    data_changed = pyqtSignal()  # 数据变化信号
    notification_requested = pyqtSignal(str)  # 请求显示通知

    def __init__(self):
        super().__init__()

        # 数据存储
        self.clipboard_data = []

        # 输出模式
        self.output_mode = 'comma'  # 'comma', 'sequential', 'reverse'

        # 状态管理
        self.last_pasted_text = ""
        self.last_paste_time = 0
        self.paste_ignore_until = 0
        self.sequential_index = -1
        self.previous_window = None
        self.last_clipboard_text = ""

    def get_data_count(self):
        """获取数据条数"""
        return len(self.clipboard_data)

    def get_all_data(self):
        """获取所有数据"""
        return self.clipboard_data.copy()

    def set_output_mode(self, mode):
        """设置输出模式"""
        if mode in ['comma', 'sequential', 'reverse']:
            self.output_mode = mode
            self.sequential_index = -1  # 重置索引

    def get_output_mode(self):
        """获取输出模式"""
        return self.output_mode

    def add_clipboard_item(self, text, timestamp=None, silent=False):
        """
        添加剪贴板项

        Args:
            text: 文本内容
            timestamp: 时间戳（可选）
            silent: 是否静默添加（不发送通知）

        Returns:
            int: 添加的条数
        """
        if not text:
            return 0

        # 处理文本（分割多行）
        texts = process_clipboard_text(text)

        added_count = 0
        for text_item in texts:
            # 检查是否已存在
            if not any(item['text'] == text_item for item in self.clipboard_data):
                self.clipboard_data.append({
                    'text': text_item,
                    'timestamp': timestamp or datetime.now().strftime('%H:%M:%S')
                })
                added_count += 1

        if added_count > 0:
            self.sequential_index = -1  # 重置顺序输出索引
            self.data_changed.emit()

            # 发送通知
            if not silent:
                if added_count == 1:
                    msg = f'已复制: {texts[0][:20]}...' if len(texts[0]) > 20 else f'已复制: {texts[0]}'
                else:
                    msg = f'已添加 {added_count} 项'
                self.notification_requested.emit(msg)

        return added_count

    def remove_item_by_text(self, text):
        """
        删除指定文本的项

        Args:
            text: 要删除的文本

        Returns:
            bool: 是否删除成功
        """
        original_length = len(self.clipboard_data)
        self.clipboard_data = [
            item for item in self.clipboard_data
            if (item['text'] if isinstance(item, dict) else item) != text
        ]

        if len(self.clipboard_data) < original_length:
            self.data_changed.emit()
            return True
        return False

    def clear_all(self):
        """清空所有数据"""
        if not self.clipboard_data:
            return False

        self.clipboard_data.clear()
        self.sequential_index = -1
        self.data_changed.emit()

        # 清空系统剪贴板
        set_clipboard_text('')
        self.last_clipboard_text = ''
        return True

    def should_ignore_clipboard_change(self, current_text):
        """
        判断是否应该忽略剪贴板变化

        Args:
            current_text: 当前剪贴板文本

        Returns:
            bool: 是否应该忽略
        """
        current_time = time.time()

        # 如果在忽略时间内，跳过
        if current_time < self.paste_ignore_until:
            return True

        # 检查是否是我们刚粘贴的内容
        if current_text == self.last_pasted_text and current_time < self.last_paste_time + 3.0:
            return True

        return False

    def handle_clipboard_change(self, new_text, is_window_visible=False):
        """
        处理剪贴板变化

        Args:
            new_text: 新的剪贴板文本
            is_window_visible: 窗口是否可见

        Returns:
            int: 添加的条数
        """
        if not new_text:
            return 0

        # 只在窗口隐藏时发送通知
        return self.add_clipboard_item(new_text, silent=is_window_visible)

    def build_paste_steps(self):
        """按输出模式生成一次批量粘贴步骤。顺序和倒序会在条目之间加回车。"""
        texts = [
            item["text"] if isinstance(item, dict) else item
            for item in self.clipboard_data
        ]
        if not texts:
            return []

        if self.output_mode == "reverse":
            texts = list(reversed(texts))

        if self.output_mode in ("sequential", "reverse"):
            steps = [
                {"text": text, "press_enter_after": index < len(texts) - 1}
                for index, text in enumerate(texts)
            ]
        else:
            steps = [{"text": ",".join(texts), "press_enter_after": False}]

        self.paste_ignore_until = time.time() + 1.0 + len(steps) * 0.6
        self.last_paste_time = time.time()
        return steps

    def remember_pasted_text(self, text):
        """记录刚写入剪贴板的内容，避免被监听器再次收录。"""
        self.last_pasted_text = text
        self.last_clipboard_text = text
        self.last_paste_time = time.time()
        self.paste_ignore_until = max(self.paste_ignore_until, time.time() + 1.5)

    def place_paste_text(self, text):
        """把待粘贴文本写入系统剪贴板。"""
        if not set_clipboard_text(text):
            return False
        self.remember_pasted_text(text)
        return True

    def send_paste_key(self):
        """发送 Command+V。"""
        return simulate_paste()

    def send_enter_key(self):
        """发送回车。"""
        return simulate_return()

    def capture_paste_target(self):
        """前台不是自己时记下目标应用。返回自己当前是否处于前台。"""
        current = get_foreground_window()
        if not current:
            return False
        if current.get("pid") == os.getpid():
            return True
        self.previous_window = current
        return False

    def save_previous_window(self):
        """保存当前活动应用。自己处于前台时不覆盖。"""
        current = get_foreground_window()
        if not current or current.get("pid") == os.getpid():
            return
        self.previous_window = current

    def restore_previous_window(self):
        """恢复之前保存的应用焦点。"""
        if not self.previous_window:
            return False
        if self.previous_window.get("pid") == os.getpid():
            return False
        return bool(set_foreground_window(self.previous_window))

    def load_data(self, data):
        """
        加载数据

        Args:
            data: 数据列表
        """
        self.clipboard_data = []
        for item in data:
            if isinstance(item, str):
                self.clipboard_data.append({
                    'text': item,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
            else:
                self.clipboard_data.append(item)
        self.data_changed.emit()

    def get_data_for_save(self):
        """获取用于保存的数据"""
        return self.clipboard_data.copy()
