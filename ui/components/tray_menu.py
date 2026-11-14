"""
自定义弹出菜单
用于菜单栏图标、主窗口和剪贴板记录的右键菜单。
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QPainter, QFont, QPen, QPixmap


class MenuSeparator(QWidget):
    """菜单分隔线"""

    def __init__(self, is_dark=False, parent=None):
        super().__init__(parent)
        self.is_dark = is_dark
        self.setFixedHeight(9)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_dark_mode(self, is_dark):
        self.is_dark = is_dark
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        color = QColor(255, 255, 255, 36) if self.is_dark else QColor(0, 0, 0, 28)
        painter.setPen(QPen(color, 1))
        y = self.height() // 2
        painter.drawLine(10, y, self.width() - 10, y)


class TrayMenuItem(QWidget):
    """弹出菜单项"""

    clicked = pyqtSignal()

    def __init__(self, icon_type, text, color="#667eea", is_danger=False, is_dark=False, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.text = text
        self.color = color
        self.is_danger = is_danger
        self.is_hovered = False
        self.is_dark = is_dark
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        self.update_icon()
        layout.addWidget(self.icon_label)

        self.text_label = QLabel(self.text)
        font = QFont("PingFang SC", 9)
        font.setStyleHint(QFont.SansSerif)
        self.text_label.setFont(font)
        layout.addWidget(self.text_label)
        layout.addStretch()
        self.setLayout(layout)
        self.update_style()

    def update_icon(self):
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        color = QColor("#e74c3c") if self.is_danger else QColor(self.color)
        painter.setPen(QPen(color, 1.5))
        painter.setBrush(Qt.NoBrush)

        if self.icon_type == "window":
            painter.drawRoundedRect(2, 3, 12, 10, 2, 2)
            painter.drawLine(2, 6, 14, 6)
            painter.setBrush(color)
            painter.drawEllipse(4, 4, 2, 2)
            painter.drawEllipse(7, 4, 2, 2)
        elif self.icon_type == "exit":
            painter.drawLine(4, 3, 12, 3)
            painter.drawLine(5, 3, 5, 13)
            painter.drawLine(11, 3, 11, 13)
            painter.drawLine(5, 13, 11, 13)
            painter.drawLine(2, 8, 8, 8)
            painter.drawLine(2, 8, 5, 5)
            painter.drawLine(2, 8, 5, 11)
        elif self.icon_type == "settings":
            import math
            painter.drawEllipse(5, 5, 6, 6)
            for i in range(8):
                angle = i * math.pi / 4
                painter.drawLine(
                    int(8 + 3 * math.cos(angle)),
                    int(8 + 3 * math.sin(angle)),
                    int(8 + 6 * math.cos(angle)),
                    int(8 + 6 * math.sin(angle)),
                )
        elif self.icon_type == "help":
            painter.drawEllipse(2, 2, 12, 12)
            font = QFont("Arial", 8, QFont.Bold)
            painter.setFont(font)
            painter.drawText(QRect(2, 1, 12, 13), Qt.AlignCenter, "?")
        elif self.icon_type == "clear":
            painter.drawLine(3, 4, 13, 4)
            painter.drawLine(6, 2, 10, 2)
            painter.drawLine(6, 2, 6, 4)
            painter.drawLine(10, 2, 10, 4)
            painter.drawRoundedRect(4, 5, 8, 8, 1, 1)
            painter.drawLine(7, 7, 7, 11)
            painter.drawLine(9, 7, 9, 11)
        elif self.icon_type == "copy":
            painter.drawRoundedRect(5, 2, 8, 9, 1, 1)
            painter.drawRoundedRect(2, 5, 8, 9, 1, 1)
        elif self.icon_type == "paste":
            painter.drawRoundedRect(3, 4, 10, 10, 1, 1)
            painter.drawLine(6, 2, 10, 2)
            painter.drawLine(6, 2, 6, 5)
            painter.drawLine(10, 2, 10, 5)
        elif self.icon_type == "delete":
            painter.drawLine(4, 4, 12, 12)
            painter.drawLine(12, 4, 4, 12)

        painter.end()
        self.icon_label.setPixmap(pixmap)

    def update_style(self):
        if self.is_hovered:
            if self.is_danger:
                bg_color = "rgba(231, 76, 60, 0.12)"
            else:
                tone = QColor(self.color)
                bg_color = f"rgba({tone.red()}, {tone.green()}, {tone.blue()}, 0.12)"
        else:
            bg_color = "transparent"

        text_color = "#e74c3c" if self.is_danger else self.color
        self.setStyleSheet(f"""
            TrayMenuItem {{
                background: {bg_color};
                border-radius: 6px;
            }}
        """)
        self.text_label.setStyleSheet(f"color: {text_color}; background: transparent;")

    def set_dark_mode(self, is_dark):
        self.is_dark = is_dark
        self.update_style()
        self.update_icon()

    def set_color(self, color):
        self.color = color
        self.update_style()
        self.update_icon()

    def enterEvent(self, event):
        self.is_hovered = True
        self.update_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class BasePopupMenu(QWidget):
    """无边框弹出菜单"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.color_scheme = "pure_blue"
        self._items = []
        self._separators = []
        self._init_chrome()

    def _init_chrome(self):
        self.setWindowFlags(
            Qt.Popup |
            Qt.FramelessWindowHint |
            Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedWidth(184)

        self.container = QWidget()
        self.container.setObjectName("trayMenuContainer")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.container.setGraphicsEffect(shadow)

        self.menu_layout = QVBoxLayout()
        self.menu_layout.setContentsMargins(6, 6, 6, 6)
        self.menu_layout.setSpacing(2)
        self.container.setLayout(self.menu_layout)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.addWidget(self.container)
        self.setLayout(main_layout)
        self.update_style()

    def add_action(self, icon_type, text, callback, is_danger=False):
        from themes.theme_manager import get_color_scheme_colors

        color1, _ = get_color_scheme_colors(self.color_scheme, self.is_dark)
        item = TrayMenuItem(icon_type, text, color1, is_danger, self.is_dark)
        item.clicked.connect(callback)
        self.menu_layout.addWidget(item)
        self._items.append(item)
        return item

    def add_separator(self):
        separator = MenuSeparator(self.is_dark)
        self.menu_layout.addWidget(separator)
        self._separators.append(separator)
        return separator

    def update_style(self):
        bg_color = "#2d2d2d" if self.is_dark else "#ffffff"
        border_color = "rgba(255,255,255,0.1)" if self.is_dark else "rgba(0,0,0,0.08)"
        self.container.setStyleSheet(f"""
            #trayMenuContainer {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """)

        from themes.theme_manager import get_color_scheme_colors
        color1, _ = get_color_scheme_colors(self.color_scheme, self.is_dark)
        for item in self._items:
            item.set_dark_mode(self.is_dark)
            if not item.is_danger:
                item.set_color(color1)
        for separator in self._separators:
            separator.set_dark_mode(self.is_dark)

    def set_theme(self, is_dark, color_scheme):
        self.is_dark = is_dark
        self.color_scheme = color_scheme
        self.update_style()

    def show_at(self, global_pos):
        from utils.screen_geometry import available_screen_geometry

        self.adjustSize()
        screen = available_screen_geometry(global_pos)
        menu_width = self.width()
        menu_height = self.height()

        x = global_pos.x()
        y = global_pos.y() - menu_height
        if x + menu_width > screen.left() + screen.width():
            x = screen.left() + screen.width() - menu_width
        if x < screen.left():
            x = screen.left()
        if y < screen.top():
            y = global_pos.y()
        if y + menu_height > screen.top() + screen.height():
            y = screen.top() + screen.height() - menu_height

        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def show_at_cursor(self):
        from PyQt5.QtGui import QCursor
        self.show_at(QCursor.pos())


class TrayMenu(BasePopupMenu):
    """主窗口和菜单栏图标右键菜单"""

    show_window_clicked = pyqtSignal()
    help_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    quit_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_action("window", "打开主界面", self.on_show_clicked)
        self.add_action("help", "操作说明", self.on_help_clicked)
        self.add_action("settings", "设置", self.on_settings_clicked)
        self.add_action("clear", "清空记录", self.on_clear_clicked)
        self.add_separator()
        self.add_action("exit", "退出程序", self.on_quit_clicked, is_danger=True)

    def on_show_clicked(self):
        self.hide()
        self.show_window_clicked.emit()

    def on_help_clicked(self):
        self.hide()
        self.help_clicked.emit()

    def on_settings_clicked(self):
        self.hide()
        self.settings_clicked.emit()

    def on_clear_clicked(self):
        self.hide()
        self.clear_clicked.emit()

    def on_quit_clicked(self):
        self.hide()
        self.quit_clicked.emit()


class ClipboardItemMenu(BasePopupMenu):
    """单条剪贴板记录的右键菜单"""

    copy_clicked = pyqtSignal(str)
    paste_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_text = ""
        self.add_action("copy", "复制此项", self.on_copy_clicked)
        self.add_action("paste", "粘贴此项", self.on_paste_clicked)
        self.add_separator()
        self.add_action("delete", "删除此项", self.on_delete_clicked, is_danger=True)

    def show_for_item(self, text, global_pos):
        self.item_text = text or ""
        self.show_at(global_pos)

    def on_copy_clicked(self):
        text = self.item_text
        self.hide()
        self.copy_clicked.emit(text)

    def on_paste_clicked(self):
        text = self.item_text
        self.hide()
        self.paste_clicked.emit(text)

    def on_delete_clicked(self):
        text = self.item_text
        self.hide()
        self.delete_clicked.emit(text)
