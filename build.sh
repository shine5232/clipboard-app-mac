#!/bin/bash

# 剪贴板助手 - macOS 打包脚本

echo "开始打包剪贴板助手 macOS 版本..."

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "警告: 未检测到虚拟环境,尝试激活..."
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "虚拟环境已激活"
    else
        echo "未找到虚拟环境,将使用系统 Python"
    fi
fi

# 清理旧的打包文件
echo "清理旧的打包文件..."
rm -rf build dist *.spec

# 执行打包
echo "开始打包..."
pyinstaller --name="剪贴板助手" \
    --windowed \
    --osx-bundle-identifier=com.clipboardhelper.app \
    --collect-all PyQt5 \
    --collect-all pynput \
    --collect-submodules pynput \
    --collect-all Quartz \
    --collect-all AppKit \
    --collect-all Foundation \
    --collect-all objc \
    --hidden-import=PyQt5 \
    --hidden-import=pynput.keyboard._darwin \
    --hidden-import=pynput._util.darwin \
    --hidden-import=pyperclip \
    --hidden-import=AppKit \
    --hidden-import=Quartz \
    --hidden-import=Quartz.CoreGraphics \
    --hidden-import=HIServices \
    --hidden-import=ApplicationServices \
    --hidden-import=Foundation \
    --hidden-import=objc \
    main.py

# 检查打包是否成功
if [ -d "dist/剪贴板助手.app" ]; then
    echo ""
    echo "✅ 打包成功!"
    echo "应用位于: dist/剪贴板助手.app"
    echo ""
    echo "您可以:"
    echo "1. 直接运行: open dist/剪贴板助手.app"
    echo "2. 移动到应用程序文件夹: cp -r dist/剪贴板助手.app /Applications/"
    echo ""
else
    echo ""
    echo "❌ 打包失败,请检查错误信息"
    echo ""
    exit 1
fi
