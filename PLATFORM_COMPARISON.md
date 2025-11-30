# Windows 版本 vs macOS 版本对比

## 功能对比

| 功能 | Windows 版 | macOS 版 | 说明 |
|------|-----------|----------|------|
| 剪贴板监听 | ✅ | ✅ | 实现方式不同 |
| 批量粘贴 | ✅ | ✅ | 完全兼容 |
| 三种输出模式 | ✅ | ✅ | 完全兼容 |
| 胶囊模式 | ✅ | ✅ | 完全兼容 |
| 全局快捷键 | ✅ | ✅ | 按键不同 |
| 主题切换 | ✅ | ✅ | 完全兼容 |
| 系统托盘 | ✅ | ✅ | 菜单栏图标 |
| 单实例运行 | ✅ | ✅ | 实现方式不同 |

## 快捷键对比

| 功能 | Windows | macOS |
|------|---------|-------|
| 显示/隐藏 | Ctrl+Shift+C | Cmd+Shift+C |
| 批量粘贴 | Ctrl+Space | Cmd+Space |
| 退出程序 | Ctrl+Shift+Q | Cmd+Shift+Q |

## 技术实现差异

### 1. 剪贴板监听

**Windows:**
```python
# 使用 Windows API: AddClipboardFormatListener
user32.AddClipboardFormatListener(hwnd)
```

**macOS:**
```python
# 使用 PyQt5 的剪贴板信号
clipboard.dataChanged.connect(handler)
```

### 2. 键盘模拟

**Windows:**
```python
# 使用 SendInput API
ctypes.windll.user32.SendInput(...)
```

**macOS:**
```python
# 使用 Quartz CGEvent 或 pynput
from Quartz import CGEventCreateKeyboardEvent
from pynput.keyboard import Controller
```

### 3. 窗口管理

**Windows:**
```python
# 使用 Win32 API
hwnd = user32.GetForegroundWindow()
user32.SetForegroundWindow(hwnd)
```

**macOS:**
```python
# 使用 AppKit
from AppKit import NSWorkspace, NSRunningApplication
active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
```

### 4. 单实例检测

**Windows:**
```python
# 使用互斥量 (Mutex)
kernel32.CreateMutexW(None, False, mutex_name)
```

**macOS:**
```python
# 使用文件锁
import fcntl
fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
```

## 依赖库差异

### Windows 版依赖

```
PyQt5>=5.15.0
pynput>=1.7.6
pyperclip>=1.8.2
pywin32>=311          # Windows 特有
PyInstaller>=6.0.0
```

### macOS 版依赖

```
PyQt5>=5.15.0
pynput>=1.7.6
pyperclip>=1.8.2
pyobjc-framework-Cocoa>=9.0    # macOS 特有
pyobjc-framework-Quartz>=9.0   # macOS 特有
PyInstaller>=6.0.0
```

## 打包方式差异

### Windows 打包

```bash
# 使用 PyInstaller 生成 .exe
pyinstaller --onefile --windowed main.py
```

生成文件: `dist/剪贴板助手.exe`

### macOS 打包

```bash
# 使用 PyInstaller 生成 .app
pyinstaller --windowed --onefile --osx-bundle-identifier=... main.py
```

生成文件: `dist/剪贴板助手.app`

## 权限要求差异

### Windows

- 无需特殊权限
- 首次运行可能被杀毒软件拦截

### macOS

需要授予以下权限:
- **辅助功能权限**: 用于全局快捷键和键盘模拟
- **可访问性权限**: 用于窗口管理

授权路径:
- 系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能

## 用户体验差异

### Windows

- 托盘图标位于任务栏右下角
- 使用 Ctrl 键作为主要修饰键
- 支持 Windows 10/11 通知

### macOS

- 菜单栏图标位于屏幕右上角
- 使用 Command (Cmd) 键作为主要修饰键
- 支持 macOS 原生通知中心

## 文件路径差异

### Windows 配置目录

```
%APPDATA%\ClipboardHelper\
```

### macOS 配置目录

```
~/Library/Application Support/ClipboardHelper/
```

## 迁移注意事项

### 从 Windows 迁移到 macOS

1. **数据文件不兼容**: 配置文件路径不同,需要重新设置
2. **快捷键习惯**: Ctrl 改为 Cmd
3. **权限设置**: 首次运行需要授权
4. **依赖安装**: 需要安装 pyobjc 相关库

### 代码迁移要点

迁移时主要修改的文件:

1. `utils/clipboard_listener.py` - 剪贴板监听实现
2. `utils/keyboard_simulator.py` - 键盘模拟实现
3. `utils/window_manager.py` - 窗口管理实现
4. `main.py` - 快捷键定义、单实例检测
5. `requirements.txt` - 依赖库列表

## 性能对比

| 指标 | Windows | macOS |
|------|---------|-------|
| 启动速度 | 快 | 快 |
| 内存占用 | ~50MB | ~60MB |
| CPU 占用 | 低 | 低 |
| 剪贴板响应 | 即时 | 即时 |

## 建议

### Windows 用户

- 更适合在 Windows 环境下使用
- 无需额外权限配置
- 打包后体积更小

### macOS 用户

- 需要首次授权
- 符合 macOS 使用习惯
- 更好的系统集成

## 总结

两个版本在功能上完全对等,主要区别在于底层平台 API 的实现方式。macOS 版本保持了与 Windows 版本相同的用户体验,只是将底层实现适配到了 macOS 平台。
