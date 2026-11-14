"""当前窗口所在显示器的可用区域，避开菜单栏和程序坞。"""

from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtWidgets import QApplication


def available_screen_geometry(global_pos=None):
    """
    返回可用屏幕区域。

    Args:
        global_pos: 全局坐标或带 x()/y() 的对象。为空时使用主屏幕。
    """
    app = QApplication.instance()
    if app is None:
        return QRect(0, 0, 1280, 800)

    screen = None
    if global_pos is not None:
        if isinstance(global_pos, QPoint):
            point = global_pos
        else:
            point = QPoint(int(global_pos.x()), int(global_pos.y()))
        screen = app.screenAt(point)

    if screen is None:
        screen = app.primaryScreen()
    if screen is None:
        return app.desktop().availableGeometry()
    return screen.availableGeometry()
