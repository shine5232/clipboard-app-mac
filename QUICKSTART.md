# 快速开始指南

## 在 macOS 上运行剪贴板助手

### 第一步: 环境准备

确保您的 Mac 已安装 Python 3.8 或更高版本:

```bash
python3 --version
```

如果没有安装,使用 Homebrew 安装:

```bash
brew install python@3.11
```

### 第二步: 安装依赖

在项目目录下运行:

```bash
# 创建虚拟环境(推荐)
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 第三步: 运行程序

```bash
python main.py
```

### 第四步: 授予权限

首次运行时,系统会提示需要授权:

1. 打开 **系统偏好设置** (或 **系统设置**)
2. 进入 **安全性与隐私** > **隐私** > **辅助功能**
3. 点击左下角的锁图标解锁
4. 勾选 **终端** 或 **Python**
5. 重启应用

## 常见问题

### Q: 提示"无法验证开发者"怎么办?

如果打包后的 .app 无法打开,右键点击应用,选择"打开",然后点击"打开"按钮。

### Q: 快捷键冲突怎么办?

可以在代码中修改快捷键定义,位于 `main.py` 的 `register_hotkeys` 方法中。

### Q: 如何卸载?

1. 退出程序 (Cmd+Shift+Q)
2. 删除应用程序
3. 删除配置文件:
   ```bash
   rm -rf ~/Library/Application\ Support/ClipboardHelper
   ```

## 下一步

- 阅读 [操作说明.md](操作说明.md),或在程序里按 `F1` 查看
- 阅读完整的 [README.md](README.md) 了解所有功能
- 查看 [BUILD_GUIDE.md](BUILD_GUIDE.md) 学习如何打包应用
- 根据需要自定义快捷键和主题

## 技术支持

如遇到问题,请检查:

1. Python 版本是否符合要求
2. 所有依赖是否正确安装
3. 是否授予了必要的系统权限

祝使用愉快! 🎉
