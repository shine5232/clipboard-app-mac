#!/bin/bash
# 权限失效时双击这里：重置「剪贴板助手」的辅助功能授权，然后重新打开应用。
# 适用场景：之前能用，某天突然粘贴没反应（系统更新、应用被替换等）。

cd "$(dirname "$0")" || exit 1

APP=""
for candidate in "./剪贴板助手.app" "/Applications/剪贴板助手.app"; do
    if [ -d "$candidate" ]; then
        APP="$candidate"
        break
    fi
done

if [ -z "$APP" ]; then
    echo "没找到「剪贴板助手.app」。"
    echo ""
    echo "请把它放到「应用程序」文件夹，或放在这个脚本旁边，再双击本脚本。"
    echo ""
    read -n 1 -s -r -p "按任意键关闭..."
    exit 1
fi

echo "1) 重置辅助功能授权…"
tccutil reset Accessibility com.clipboardhelper.app

echo "2) 关闭正在运行的实例…"
pkill -f "MacOS/剪贴板助手" 2>/dev/null
sleep 1

echo "3) 重新打开应用…"
open "$APP"

echo ""
echo "接下来："
echo "  · 系统若弹出「想要控制这台电脑」→ 点「打开系统设置」"
echo "  · 在 辅助功能 列表里勾选「剪贴板助手」"
echo "  · 然后按 Cmd+Shift+Q 退出，再正常打开一次即可"
echo ""
read -n 1 -s -r -p "按任意键关闭此窗口…"
