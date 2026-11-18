#!/bin/bash
# 生成可直接发给别人的分发包（zip）。
# 只做打包，不碰 dist/剪贴板助手.app —— 不会改变签名指纹，不会影响已有授权。
#
# 用法：bash packaging/make_zip.sh
# 也可以由 build.sh 在构建成功后自动调用。

set -euo pipefail

cd "$(dirname "$0")/.." || exit 1

APP="dist/剪贴板助手.app"
OUT="剪贴板助手-macOS-分发版.zip"
NAME="剪贴板助手-macOS"

if [ ! -d "$APP" ]; then
    echo "❌ 找不到 $APP，请先执行 bash build.sh universal2"
    exit 1
fi

# 用 ditto 复制，保留签名、可执行权限和符号链接；缺一样对方都打不开
STAGE_ROOT="$(mktemp -d)"
trap 'rm -rf "$STAGE_ROOT"' EXIT
STAGE="$STAGE_ROOT/$NAME"
mkdir -p "$STAGE"

ditto "$APP" "$STAGE/剪贴板助手.app"
cp "packaging/首次打开必读.txt" "$STAGE/"
cp "packaging/授权失效时双击这里.command" "$STAGE/"
chmod +x "$STAGE/授权失效时双击这里.command"

# 复制后立刻校验，避免把损坏的包发出去
if ! codesign --verify --deep --strict "$STAGE/剪贴板助手.app" 2>/dev/null; then
    echo "❌ 复制后签名校验失败，已中止。"
    exit 1
fi

rm -f "$OUT"
ditto -c -k --keepParent "$STAGE" "$OUT"

ARCHS="$(lipo -archs "$APP/Contents/MacOS/剪贴板助手" 2>/dev/null)"
SIZE="$(du -h "$OUT" | cut -f1)"

echo ""
echo "✅ 分发包已生成: $OUT"
echo "   架构: $ARCHS   体积: $SIZE"
echo "   内容: 剪贴板助手.app + 首次打开必读.txt + 授权失效时双击这里.command"
echo ""
