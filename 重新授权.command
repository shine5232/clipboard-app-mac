#!/bin/bash
# 重新给「剪贴板助手」授权辅助功能。
# 每次重新打包后二进制指纹（CDHash）都会变，旧的授权条目就对不上了，需要跑一次这个。

cd "$(dirname "$0")" || exit 1

APP="dist/剪贴板助手.app"

if [ ! -d "$APP" ]; then
    echo "找不到 $APP，请先执行 bash build.sh 打包。"
    read -n 1 -s -r -p "按任意键关闭..."
    exit 1
fi

echo "1) 重置旧的辅助功能授权…"
tccutil reset Accessibility com.clipboardhelper.app

echo "2) 关闭正在运行的实例…"
pkill -f "MacOS/剪贴板助手" 2>/dev/null
sleep 1

echo "3) 打开应用…"
open "$APP"

echo ""
echo "接下来需要你手动做两步："
echo "  · 系统若弹出「想要控制这台电脑」→ 点「打开系统设置」"
echo "  · 在 辅助功能 列表里勾选「剪贴板助手」"
echo "然后按 Cmd+Shift+Q 退出应用，再双击打开一次，就能用了。"
echo ""
read -n 1 -s -r -p "按任意键关闭此窗口…"
