"""把 venv 里的 PyQt5 补成 universal2（x86_64 + arm64）。

背景：
  Riverbank 只发布按架构分开的 macosx_11_0_x86_64 / macosx_11_0_arm64 轮子，
  没有 universal2 轮子。而 Python、PyInstaller bootloader、pyobjc 本身都是
  universal2，所以只要把 PyQt5 / PyQt5-Qt5 里 193 个单架构 Mach-O 用 lipo
  合并成胖二进制，PyInstaller 的 --target-arch universal2 就能出通用包。

用法：
  python tools/merge_pyqt_universal.py <arm64 轮子目录> [--check]

  arm64 轮子目录里放 PyQt5 和 PyQt5-Qt5 的 macosx_11_0_arm64.whl，脚本会解压
  并与 venv 中已安装的 x86_64 版本逐文件合并。合并前自动备份到
  /tmp/PyQt5-x86-backup。--check 只检查不修改。
"""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "venv" / "lib" / "python3.10" / "site-packages"
PYQT = SITE / "PyQt5"
BACKUP = Path("/tmp/PyQt5-x86-backup")


def is_macho(path):
    """先看魔数，避免对上千个资源文件都调一次 lipo。"""
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
    except Exception:
        return None
    if magic in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe"):
        return "thin"
    if magic in (b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"):
        return "fat"
    return None


def archs(path):
    """返回 lipo -archs 结果；不是 Mach-O 就返回 None。"""
    if is_macho(path) is None:
        return None
    try:
        out = subprocess.run(["lipo", "-archs", str(path)],
                             capture_output=True, text=True, timeout=20)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    value = out.stdout.strip()
    return value or None


def extract_wheels(wheel_dir, dest):
    wheels = sorted(Path(wheel_dir).glob("*macosx_11_0_arm64.whl"))
    if not wheels:
        raise SystemExit("在 %s 里没找到 *macosx_11_0_arm64.whl" % wheel_dir)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for wheel in wheels:
        print("解压", wheel.name)
        with zipfile.ZipFile(wheel) as zf:
            zf.extractall(dest)
    return dest


def merge(arm_root, check_only=False):
    merged, skipped, missing, failed = 0, 0, 0, 0
    for arm_file in arm_root.rglob("*"):
        if not arm_file.is_file() or arm_file.is_symlink():
            continue
        arm_arch = archs(arm_file)
        if arm_arch is None or "arm64" not in arm_arch:
            continue  # 只处理 arm64 的 Mach-O

        rel = arm_file.relative_to(arm_root)
        # 轮子里带 "PyQt5/" 前缀，而 PYQT 已经指向 site-packages/PyQt5
        if rel.parts and rel.parts[0] == "PyQt5":
            rel = Path(*rel.parts[1:])
        target = PYQT / rel
        if not target.exists():
            missing += 1
            if missing <= 5:
                print("  跳过（venv 里没有对应文件）:", rel)
            continue
        if target.is_symlink():
            target = target.resolve()

        target_arch = archs(target)
        if target_arch is None:
            continue
        if "arm64" in target_arch and "x86_64" in target_arch:
            skipped += 1
            continue

        if check_only:
            merged += 1
            continue

        tmp = target.with_suffix(target.suffix + ".fat")
        result = subprocess.run(
            ["lipo", "-create", str(target), str(arm_file), "-output", str(tmp)],
            capture_output=True, text=True)
        if result.returncode != 0:
            failed += 1
            print("  合并失败:", rel, result.stderr.strip()[:120])
            if tmp.exists():
                tmp.unlink()
            continue
        tmp.chmod(target.stat().st_mode)
        tmp.replace(target)
        merged += 1
        if merged % 40 == 0:
            print("  已合并 %d 个…" % merged)

    return merged, skipped, missing, failed


def verify():
    bad = []
    for f in PYQT.rglob("*"):
        if not f.is_file() or f.is_symlink():
            continue
        a = archs(f)
        if a is None:
            continue
        if not ("arm64" in a and "x86_64" in a):
            bad.append((f.relative_to(PYQT), a))
    return bad


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check" in sys.argv

    if not PYQT.is_dir():
        raise SystemExit("找不到 %s，请先在本目录建好 venv 并安装 PyQt5" % PYQT)

    if not BACKUP.exists() and not check_only:
        print("备份 x86_64 版本到", BACKUP)
        shutil.copytree(PYQT, BACKUP, symlinks=True)

    wheel_dir = args[0] if args else "/tmp/wheels"
    arm_root = extract_wheels(wheel_dir, Path("/tmp/wheels/arm64"))
    if (arm_root / "PyQt5").is_dir():
        arm_root = arm_root / "PyQt5"

    moved, skipped, missing, failed = merge(arm_root, check_only)
    action = "待合并" if check_only else "已合并"
    print("\n%s %d 个，已是双架构跳过 %d 个，venv 缺失 %d 个，失败 %d 个"
          % (action, moved, skipped, missing, failed))

    if not check_only:
        bad = verify()
        if bad:
            print("\n仍有 %d 个单架构文件：" % len(bad))
            for rel, a in bad[:15]:
                print("  %-60s %s" % (rel, a))
            return 1
        print("\n✅ PyQt5 已全部是 universal2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
