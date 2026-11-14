"""操作说明对话框。"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
    QScrollArea, QFrame, QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QFont

from themes.theme_manager import ThemeManager, get_color_scheme_colors
from utils.screen_geometry import available_screen_geometry


HELP_SECTIONS = [
    (
        "快速开始",
        [
            "在其他应用里正常复制，内容会自动出现在列表中。",
            "先点一下要接收内容的输入框，再按 <b>Cmd+Option+V</b>，即可按当前输出模式批量粘贴。",
        ],
    ),
    (
        "添加记录",
        [
            "使用 <b>Cmd+C</b> 复制后自动记录，相同内容不会重复添加。",
            "一次复制多行时，每个非空行会单独成为一条记录。",
            "主窗口隐藏时会提示“已复制”；窗口已经打开时不再重复提示。",
        ],
    ),
    (
        "右键菜单",
        [
            "右键标题栏、列表空白处，或右键屏幕右上角的菜单栏图标：打开主界面、操作说明、设置、清空记录、退出程序。",
            "右键某一条记录：复制此项、粘贴此项、删除此项。",
            "标题栏问号按钮，或窗口在前台时按 <b>F1</b>，也可以打开本说明。",
        ],
    ),
    (
        "批量粘贴",
        [
            "快捷键是 <b>Cmd+Option+V</b>。请先让光标停在目标输入框。",
            "如果助手窗口正在最前面，会先切回上一个应用，再执行粘贴。",
            "全局快捷键和模拟按键需要辅助功能权限。",
        ],
    ),
    (
        "输出模式",
        [
            "<b>拼 / 逗号拼接</b>：全部记录用英文逗号连成一条，一次粘贴。",
            "<b>顺 / 顺序输出</b>：按添加顺序逐条粘贴，条目之间自动按回车。",
            "<b>倒 / 倒序输出</b>：从最新一条开始逐条粘贴，条目之间自动按回车。",
            "标题栏中间的字就是当前模式。可在设置或右键菜单进入的设置里切换。",
        ],
    ),
    (
        "胶囊模式",
        [
            "双击标题栏，或点击标题栏右侧 ×，窗口会缩成屏幕边缘的胶囊。",
            "把窗口拖到屏幕左、右、上、下边缘后松开，也会进入胶囊模式。",
            "鼠标移到胶囊上，或双击胶囊，会恢复主窗口。胶囊上的数字是当前记录条数。",
        ],
    ),
    (
        "快捷键",
        [
            "<b>Cmd+Shift+C</b>：显示或隐藏主窗口。",
            "<b>Cmd+Option+V</b>：批量粘贴。",
            "<b>Cmd+Shift+Q</b>：退出程序。",
            "<b>F1</b>：主窗口在前台时打开操作说明。",
        ],
    ),
    (
        "权限与数据",
        [
            "请在“系统设置 &gt; 隐私与安全性 &gt; 辅助功能”中允许终端、Python 或本应用。",
            "记录保存在 ~/Library/Application Support/ClipboardHelper/。",
            "退出程序时会清除剪贴板记录；主题、配色和输出模式会保留。",
        ],
    ),
]


class HelpDialog(QDialog):
    """与主界面风格一致的操作说明。"""

    def __init__(self, parent=None, theme="light", color_scheme="pure_blue"):
        super().__init__(parent)
        self.theme_name = theme
        self.color_scheme = color_scheme
        self.dragging = False
        self.drag_position = None
        self.theme_manager = ThemeManager(theme=theme, color_scheme=color_scheme)
        self.section_titles = []
        self.section_bodies = []
        self.cards = []
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        self.setWindowTitle("操作说明")
        self.setFixedSize(460, 620)
        self.setWindowFlags(
            Qt.Dialog |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.ApplicationModal)

        container = QWidget()
        container.setObjectName("helpContainer")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 45))
        container.setGraphicsEffect(shadow)

        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = _HelpHeader()
        self.header.setFixedHeight(58)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 0, 10, 0)
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_box.setContentsMargins(0, 8, 0, 8)
        self.header_title = QLabel("操作说明")
        self.header_title.setFont(QFont("PingFang SC", 13, QFont.DemiBold))
        self.header_subtitle = QLabel("剪贴板助手 · macOS")
        self.header_subtitle.setFont(QFont("PingFang SC", 9))
        title_box.addWidget(self.header_title)
        title_box.addWidget(self.header_subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                font-size: 18px;
                border-radius: 12px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.18); }
        """)
        header_layout.addWidget(close_btn)
        self.header.setLayout(header_layout)
        self.header.mousePressEvent = self.header_mouse_press
        self.header.mouseMoveEvent = self.header_mouse_move
        self.header.mouseReleaseEvent = self.header_mouse_release
        root.addWidget(self.header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll = scroll

        content = QWidget()
        content.setObjectName("helpContent")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(18, 16, 18, 8)
        content_layout.setSpacing(12)

        self.intro = QLabel("下面是日常使用时会用到的操作。设置里的输出模式，会决定批量粘贴如何输出。")
        self.intro.setWordWrap(True)
        self.intro.setFont(QFont("PingFang SC", 10))
        content_layout.addWidget(self.intro)

        for title, lines in HELP_SECTIONS:
            card = QWidget()
            card.setObjectName("helpCard")
            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(12, 10, 12, 10)
            card_layout.setSpacing(6)
            title_label = QLabel(title)
            title_label.setFont(QFont("PingFang SC", 11, QFont.DemiBold))
            body = QLabel(self._lines_to_html(lines))
            body.setTextFormat(Qt.RichText)
            body.setWordWrap(True)
            body.setTextInteractionFlags(Qt.TextSelectableByMouse)
            body.setFont(QFont("PingFang SC", 10))
            card_layout.addWidget(title_label)
            card_layout.addWidget(body)
            card.setLayout(card_layout)
            content_layout.addWidget(card)
            self.cards.append(card)
            self.section_titles.append(title_label)
            self.section_bodies.append(body)

        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)
        self.content = content
        root.addWidget(scroll, 1)

        footer = QWidget()
        footer.setObjectName("helpFooter")
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(18, 8, 18, 14)
        footer_layout.addStretch()
        self.ok_btn = QPushButton("我知道了")
        self.ok_btn.setObjectName("helpOkBtn")
        self.ok_btn.setFixedSize(96, 32)
        self.ok_btn.setCursor(Qt.PointingHandCursor)
        self.ok_btn.clicked.connect(self.accept)
        footer_layout.addWidget(self.ok_btn)
        footer.setLayout(footer_layout)
        self.footer = footer
        root.addWidget(footer)

        container.setLayout(root)
        outer = QVBoxLayout()
        outer.setContentsMargins(12, 12, 12, 12)
        outer.addWidget(container)
        self.setLayout(outer)
        self.container = container

    def _lines_to_html(self, lines):
        items = "".join(f"<div style='margin: 0 0 4px 0;'>• {line}</div>" for line in lines)
        return f"<div style='line-height: 145%;'>{items}</div>"

    def apply_theme(self):
        is_dark = self.theme_name == "dark"
        self.theme_manager.set_theme(self.theme_name)
        self.theme_manager.set_color_scheme(self.color_scheme)
        self.header.set_theme(is_dark, self.color_scheme)

        bg = "#1e1e1e" if is_dark else "#ffffff"
        card = "#2a2a2a" if is_dark else "#f5f7fa"
        title = "#f2f2f2" if is_dark else "#303133"
        body = "#c8c8c8" if is_dark else "#606266"
        muted = "#9a9a9a" if is_dark else "#909399"
        border = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.06)"

        self.container.setStyleSheet(f"""
            #helpContainer {{
                background: {bg};
                border: 1px solid rgba(102, 126, 234, 0.28);
                border-radius: 12px;
            }}
        """)
        self.content.setStyleSheet(f"background: {bg};")
        self.footer.setStyleSheet(f"""
            #helpFooter {{
                background: {bg};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
        """)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background: {bg}; border: none; }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 4px 2px 4px 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(128, 128, 128, 0.45);
                border-radius: 4px;
                min-height: 24px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        self.scroll.viewport().setStyleSheet(f"background: {bg};")
        self.header_title.setStyleSheet("color: white; background: transparent;")
        self.header_subtitle.setStyleSheet("color: rgba(255,255,255,0.82); background: transparent;")
        self.intro.setStyleSheet(f"color: {muted}; background: transparent;")
        for label in self.section_titles:
            label.setStyleSheet(f"color: {title}; background: transparent;")
        for label in self.section_bodies:
            label.setStyleSheet(f"color: {body}; background: transparent;")
        card_style = (
            "QWidget#helpCard {"
            f"background: {card};"
            f"border: 1px solid {border};"
            "border-radius: 8px;"
            "}"
        )
        for card_widget in self.cards:
            card_widget.setStyleSheet(card_style)
        self.ok_btn.setStyleSheet(self.theme_manager.get_primary_button_style("#helpOkBtn"))

    def showEvent(self, event):
        super().showEvent(event)
        screen = available_screen_geometry(self.frameGeometry().center())
        parent = self.parent()
        if parent is not None and parent.isVisible():
            center = parent.frameGeometry().center()
            x = center.x() - self.width() // 2
            y = center.y() - self.height() // 2
        else:
            x = screen.left() + (screen.width() - self.width()) // 2
            y = screen.top() + (screen.height() - self.height()) // 2
        x = max(screen.left(), min(x, screen.left() + screen.width() - self.width()))
        y = max(screen.top(), min(y, screen.top() + screen.height() - self.height()))
        self.move(x, y)

    def header_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def header_mouse_move(self, event):
        if self.dragging and self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def header_mouse_release(self, event):
        self.dragging = False
        event.accept()


class _HelpHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.color_scheme = "pure_blue"

    def set_theme(self, is_dark, color_scheme):
        self.is_dark = is_dark
        self.color_scheme = color_scheme
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        radius = 12
        path.moveTo(rect.left(), rect.bottom())
        path.lineTo(rect.left(), rect.top() + radius)
        path.quadTo(rect.left(), rect.top(), rect.left() + radius, rect.top())
        path.lineTo(rect.right() - radius, rect.top())
        path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + radius)
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(rect.left(), rect.bottom())

        color1, color2 = get_color_scheme_colors(self.color_scheme, self.is_dark)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(color1))
        gradient.setColorAt(1, QColor(color2))
        painter.fillPath(path, gradient)
