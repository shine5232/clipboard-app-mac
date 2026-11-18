# 剪贴板助手 - macOS版 打包指南

## 环境要求

- macOS 10.13 或更高版本
- Python 3.8 或更高版本
- 已安装 Homebrew (推荐)

## 安装依赖

### 1. 安装 Python (如果还没有安装)

```bash
# 使用 Homebrew 安装 Python
brew install python@3.11
```

### 2. 创建虚拟环境 (推荐)

```bash
cd clipboard-app-mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装项目依赖

```bash
pip install -r requirements.txt
```

## 运行程序

### 直接运行

```bash
python main.py
```

### 首次运行需要授权

首次运行时,macOS 会提示需要以下权限:

1. **辅助功能权限**: 用于全局快捷键和键盘模拟
   - 打开"系统偏好设置" > "安全性与隐私" > "隐私" > "辅助功能"
   - 添加 Python 或终端到允许列表

2. **可访问性权限**: 用于窗口管理
   - 同样在"辅助功能"中授权

## 打包成 .app 应用

### 使用 PyInstaller 打包

```bash
# 激活虚拟环境
source venv/bin/activate

# 打包命令
pyinstaller --name="剪贴板助手" \
    --windowed \
    --icon=icon.icns \
    --osx-bundle-identifier=com.clipboardhelper.app \
    --add-data="ui:ui" \
    --add-data="utils:utils" \
    --add-data="services:services" \
    --add-data="models:models" \
    --add-data="themes:themes" \
    --hidden-import=PyQt5 \
    --hidden-import=pynput \
    --hidden-import=pyperclip \
    --hidden-import=AppKit \
    --hidden-import=Quartz \
    main.py
```

### 打包参数说明

- `--name`: 应用名称
- `--windowed`: 不显示终端窗口
- macOS 的 `.app` 使用目录模式，不要加 `--onefile`，否则容易缺 Qt 和 pyobjc 依赖。
- `--icon`: 应用图标 (需要准备 .icns 格式图标)
- `--osx-bundle-identifier`: macOS Bundle ID
- `--add-data`: 添加资源文件
- `--hidden-import`: 显式包含的模块

### 简化打包脚本

创建 `build.sh` 文件:

```bash
#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

# 清理旧的打包文件
rm -rf build dist *.spec

# 执行打包
pyinstaller --name="剪贴板助手" \
    --windowed \
    --osx-bundle-identifier=com.clipboardhelper.app \
    --hidden-import=PyQt5 \
    --hidden-import=pynput \
    --hidden-import=pyperclip \
    --hidden-import=AppKit \
    --hidden-import=Quartz \
    main.py

echo "打包完成! 应用位于: dist/剪贴板助手.app"
```

赋予执行权限并运行:

```bash
chmod +x build.sh
./build.sh
```

## 打包后的应用位置

打包完成后,应用程序位于 `dist/剪贴板助手.app`

可以将其拖到"应用程序"文件夹中安装。

## 快捷键说明

- `Cmd+Shift+C`: 显示/隐藏主窗口
- `Ctrl+Cmd+V`: 批量粘贴剪贴板内容（可在设置里改为 `Cmd+Shift+V` 或 `Cmd+Option+V`）
- `Cmd+Shift+Q`: 退出程序

## 功能特性

### 1. 自动监听剪贴板

程序会自动监听系统剪贴板,每次复制内容时自动添加到列表中。

### 2. 三种输出模式

- **逗号拼接**: 将所有选中内容用逗号连接后粘贴
- **顺序输出**: 按复制顺序依次粘贴每一项
- **倒序输出**: 按复制倒序依次粘贴每一项

### 3. 胶囊模式

- 将窗口拖拽到屏幕边缘会自动进入胶囊模式
- 鼠标悬停或双击胶囊可恢复主窗口
- 支持四个边缘吸附: 左、右、上、下

### 4. 主题切换

- 支持日间模式和暗夜模式
- 提供多种配色方案: 魅力蓝、天空蓝、青草绿、樱花粉

## 故障排除

### 1. 快捷键不工作

复制能用、粘贴快捷键不能用时，通常是辅助功能没有授给打包后的应用。

- 打开系统设置 > 隐私与安全性 > 辅助功能
- 勾选“剪贴板助手”本身，不要只勾选终端或 Python
- 重新打包后先移除旧的同名项，再重新勾选并打开应用
- 打包请使用 `./build.sh`，它会带上 Quartz 和 pynput 的 macOS 后端

### 2. 粘贴功能不工作

- 检查目标应用是否支持粘贴
- 确保剪贴板有内容
- 尝试重启应用

### 3. 应用无法启动

```bash
# 查看详细错误信息
./剪贴板助手.app/Contents/MacOS/剪贴板助手
```

### 4. PyObjC 相关错误

如果遇到 PyObjC 相关的错误,尝试重新安装:

```bash
pip uninstall pyobjc-framework-Cocoa pyobjc-framework-Quartz
pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz
```

## 开发说明

### 项目结构

```
clipboard-app-mac/
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖列表
├── BUILD_GUIDE.md         # 本文档
├── utils/                 # 工具模块
│   ├── clipboard_listener.py    # 剪贴板监听器
│   ├── clipboard_utils.py       # 剪贴板工具
│   ├── keyboard_simulator.py    # 键盘模拟
│   ├── window_manager.py        # 窗口管理
│   └── data_manager.py          # 数据管理
├── ui/                    # UI组件
│   └── components/
│       ├── floating_icon.py     # 浮动图标
│       ├── tray_menu.py         # 托盘菜单
│       └── clipboard_delegate.py # 列表委托
├── services/              # 业务逻辑
│   └── clipboard_service.py     # 剪贴板服务
├── models/                # 数据模型
│   └── data_model.py            # 数据模型
└── themes/                # 主题
    └── theme_manager.py         # 主题管理器
```

### Windows 版本差异

主要差异在于平台特定的API:

1. **剪贴板监听**:
   - Windows: `AddClipboardFormatListener` API
   - macOS: PyQt5 的 `QClipboard.dataChanged` 信号

2. **键盘模拟**:
   - Windows: `SendInput` API
   - macOS: Quartz 的 `CGEvent` 或 pynput

3. **窗口管理**:
   - Windows: `GetForegroundWindow`, `SetForegroundWindow`
   - macOS: AppKit 的 `NSWorkspace`, `NSRunningApplication`

4. **快捷键**:
   - Windows: Ctrl 键
   - macOS: Command (Cmd) 键

5. **单实例检测**:
   - Windows: Mutex
   - macOS: 文件锁 (fcntl)

## 许可证

请参考原项目许可证。

## 贡献

欢迎提交 Issue 和 Pull Request。

## 联系方式

如有问题,请在 GitHub 项目页面提交 Issue。
