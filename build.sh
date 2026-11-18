#!/bin/bash
set -o pipefail

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

# 目标架构：universal2 / x86_64 / arm64。不传就按当前机器的 Python 原生架构。
# 用法：bash build.sh universal2
TARGET_ARCH="${1:-${TARGET_ARCH:-}}"
ARCH_ARG=""
if [ -n "$TARGET_ARCH" ]; then
    case "$TARGET_ARCH" in
        universal2|x86_64|arm64) ARCH_ARG="--target-arch=$TARGET_ARCH" ;;
        *) echo "❌ 架构参数无效: $TARGET_ARCH（可选 universal2 / x86_64 / arm64）"; exit 1 ;;
    esac
    echo "目标架构: $TARGET_ARCH"
fi

# 清理旧的打包文件。删不掉也不影响，下面用 --noconfirm 让 PyInstaller 自己覆盖。
echo "清理旧的打包文件..."
rm -rf build dist "剪贴板助手.spec" 2>/dev/null || true

# 执行打包
echo "开始打包..."
pyinstaller --noconfirm --name="剪贴板助手" \
    --windowed \
    $ARCH_ARG \
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

# 以 pyinstaller 的退出码为准，避免旧产物留在 dist 里被误判成成功
BUILD_STATUS=$?

if [ $BUILD_STATUS -ne 0 ]; then
    echo ""
    echo "❌ 打包失败 (pyinstaller exit=$BUILD_STATUS)，请检查上面的错误信息"
    echo ""
    exit 1
fi

if [ -d "dist/剪贴板助手.app" ]; then
    echo ""
    echo "✅ 打包成功!"
    echo "应用位于: dist/剪贴板助手.app"
    echo "架构: $(lipo -archs "dist/剪贴板助手.app/Contents/MacOS/剪贴板助手" 2>/dev/null)"
    echo "（注意：重新打包后签名会变，首次运行需在 系统设置 > 辅助功能 里重新勾选一次）"
    echo ""
    echo "您可以:"
    echo "1. 直接运行: open dist/剪贴板助手.app"
    echo "2. 移动到应用程序文件夹: cp -r dist/剪贴板助手.app /Applications/"
    echo ""
else
    echo ""
    echo "❌ 打包失败: 没有生成 dist/剪贴板助手.app"
    echo ""
    exit 1
fi
