"""
docBrain 离线依赖智能同步工具

功能：
1. 逐个检查 requirements.txt 中的依赖及其子依赖
2. 仅下载缺失的 wheel 文件，跳过已有的
3. 删除不再需要的多余 wheel 文件
4. 在 exportLog/ 目录下生成变更日志 + 新增 wheel 文件副本
"""

import os
import sys
import shutil
import subprocess
import json
import time
import threading
from datetime import datetime
from pathlib import Path


# ============================================================
# 进度显示工具
# ============================================================

def progress_bar(current, total, prefix="", width=40):
    """打印一行内更新的进度条"""
    if total == 0:
        return
    pct = current / total
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r  {prefix} [{bar}] {current}/{total} ({pct:.0%})")
    sys.stdout.flush()
    if current >= total:
        sys.stdout.write("\n")
        sys.stdout.flush()


class Spinner:
    """旋转动画，用于无法确定总量的长耗时操作"""
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message="处理中"):
        self.message = message
        self._stop = threading.Event()
        self._thread = None
        self._elapsed = 0

    def _spin(self):
        start = time.time()
        i = 0
        while not self._stop.is_set():
            self._elapsed = time.time() - start
            frame = self.FRAMES[i % len(self.FRAMES)]
            sys.stdout.write(f"\r  {frame} {self.message}... ({self._elapsed:.0f}s)")
            sys.stdout.flush()
            i += 1
            self._stop.wait(0.12)
        # 结束时清行
        sys.stdout.write(f"\r  ✓ {self.message} 完成 ({self._elapsed:.0f}s)   \n")
        sys.stdout.flush()

    def __enter__(self):
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args):
        self._stop.set()
        self._thread.join()


# ============================================================
# 核心逻辑
# ============================================================

def get_wheel_package_name(filename: str) -> str:
    """从 wheel 文件名提取包名 (规范化为小写+下划线)"""
    parts = filename.split("-")
    return parts[0].lower().replace("-", "_")


def get_wheel_version(filename: str) -> str:
    """从 wheel 文件名提取版本号"""
    parts = filename.split("-")
    return parts[1] if len(parts) >= 2 else "unknown"


def get_existing_wheels(packages_dir: Path) -> dict:
    """获取已有的 wheel 文件 {规范化包名: 文件名}，带进度条"""
    wheels = {}
    if not packages_dir.exists():
        return wheels

    all_files = [f for f in packages_dir.iterdir() if f.is_file()]
    total = len(all_files)

    for i, f in enumerate(all_files):
        progress_bar(i + 1, total, prefix="扫描现有包")
        if f.suffix == ".whl":
            pkg_name = get_wheel_package_name(f.name)
            wheels[pkg_name] = f.name
        elif f.name.endswith((".tar.gz", ".zip")):
            wheels[f.stem.split("-")[0].lower().replace("-", "_")] = f.name

    return wheels


def detect_version_updates(packages_dir: Path, before_wheels: dict) -> dict:
    """
    检测版本更新：扫描目录中同名包是否有多个版本文件。
    pip download 会下载新版本但不删除旧版本，导致同包多文件。
    返回 {包名: {"old": 旧文件名, "new": 新文件名}}
    """
    from collections import defaultdict

    # 按包名分组所有文件
    pkg_files = defaultdict(list)
    for f in packages_dir.iterdir():
        if f.suffix == ".whl":
            pkg_name = get_wheel_package_name(f.name)
            pkg_files[pkg_name].append(f.name)

    updates = {}
    for pkg_name, files in pkg_files.items():
        if len(files) > 1:
            # 多个版本存在，旧的是 before 中的，新的是另一个
            old_file = before_wheels.get(pkg_name)
            if old_file and old_file in files:
                new_files = [f for f in files if f != old_file]
                if new_files:
                    new_file = new_files[0]
                    old_ver = get_wheel_version(old_file)
                    new_ver = get_wheel_version(new_file)
                    updates[pkg_name] = {
                        "old_file": old_file, "new_file": new_file,
                        "old_ver": old_ver, "new_ver": new_ver
                    }
                    # 删除旧版本
                    old_path = packages_dir / old_file
                    if old_path.exists():
                        old_path.unlink()
                        print(f"  🔄 版本更新: {pkg_name} {old_ver} → {new_ver}")

    return updates

    return wheels


def get_required_packages(pip_exe: str, requirements_file: str) -> set:
    """通过 pip 解析 requirements.txt 的完整依赖树，带 Spinner 动画"""
    # 方案1: pip download --dry-run --report
    with Spinner("解析依赖树 (dry-run)") as sp:
        try:
            result = subprocess.run(
                [pip_exe, "download", "-r", requirements_file,
                 "--dry-run", "--report", "-", "--quiet",
                 "--python-version", "3.10",
                 "--only-binary", ":all:",
                 "--platform", "win_amd64"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    report = json.loads(result.stdout)
                    packages = set()
                    for item in report.get("install", []):
                        name = item.get("metadata", {}).get("name", "")
                        if name:
                            packages.add(name.lower().replace("-", "_"))
                    if packages:
                        return packages
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # 方案2: 回退，pip download 到临时目录
    import tempfile
    with Spinner("解析依赖树 (回退方案，需要更长时间)") as sp:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [pip_exe, "download", "-r", requirements_file,
                 "-d", tmpdir,
                 "--python-version", "3.10",
                 "--only-binary", ":all:",
                 "--platform", "win_amd64"],
                capture_output=True, text=True, timeout=600
            )
            if result.returncode != 0:
                result = subprocess.run(
                    [pip_exe, "download", "-r", requirements_file, "-d", tmpdir],
                    capture_output=True, text=True, timeout=600
                )

            packages = set()
            for f in Path(tmpdir).iterdir():
                if f.suffix == ".whl":
                    packages.add(get_wheel_package_name(f.name))
            return packages


def download_missing(pip_exe: str, requirements_file: str, packages_dir: Path):
    """下载缺失的 wheel 包，流式输出 pip 进度"""
    print("  ⬇ 检查并下载缺失的依赖...")

    process = subprocess.Popen(
        [pip_exe, "download", "-r", requirements_file,
         "-d", str(packages_dir),
         "--python-version", "3.10",
         "--only-binary", ":all:",
         "--platform", "win_amd64"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )

    downloaded = 0
    skipped = 0
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue
        if "already satisfied" in line.lower() or "File was already downloaded" in line:
            skipped += 1
            sys.stdout.write(f"\r  ⏭ 已有: {skipped} | 新增: {downloaded}")
            sys.stdout.flush()
        elif "Saved" in line or "saved" in line.lower():
            downloaded += 1
            sys.stdout.write(f"\r  ⏭ 已有: {skipped} | 新增: {downloaded}")
            sys.stdout.flush()

    process.wait()
    sys.stdout.write(f"\r  ✓ 下载完成 — 跳过: {skipped}, 新增: {downloaded}   \n")
    sys.stdout.flush()

    if process.returncode != 0:
        print("  [WARNING] 部分包不支持 only-binary，尝试包含源码包...")
        subprocess.run(
            [pip_exe, "download", "-r", requirements_file,
             "-d", str(packages_dir)],
            timeout=600
        )

    return process.returncode == 0


def main():
    # backend/scripts/sync_offline_packages.py -> backend/scripts -> backend -> 项目根
    project_root = Path(__file__).parent.parent.parent
    packages_dir = project_root / "offline_packages"
    export_log_dir = project_root / "exportLog"
    requirements_file = str(project_root / "backend" / "requirements.txt")

    # 确定 pip 路径
    venv_pip = project_root / ".venv" / "Scripts" / "pip.exe"
    runtime_pip = project_root / "runtime" / "python" / "Scripts" / "pip.exe"
    if venv_pip.exists():
        pip_exe = str(venv_pip)
    elif runtime_pip.exists():
        pip_exe = str(runtime_pip)
    else:
        print("[ERROR] 未找到 pip，请确保 .venv 或 runtime/python 存在。")
        sys.exit(1)

    packages_dir.mkdir(exist_ok=True)
    export_log_dir.mkdir(exist_ok=True)

    # ===== 1. 记录同步前的状态 =====
    print()
    before_wheels = get_existing_wheels(packages_dir)
    print(f"  📦 当前离线包: {len(before_wheels)} 个")
    print()

    # ===== 2. 获取完整依赖列表 =====
    required_packages = get_required_packages(pip_exe, requirements_file)
    print(f"  📋 需要的包: {len(required_packages)} 个")
    print()

    # ===== 3. 下载缺失的包 =====
    download_missing(pip_exe, requirements_file, packages_dir)
    print()

    # ===== 4. 检测版本更新 =====
    version_updates = detect_version_updates(packages_dir, before_wheels)

    # ===== 5. 同步后获取新状态 =====
    after_wheels = get_existing_wheels(packages_dir)

    # ===== 6. 计算差异 =====
    added_names = set(after_wheels.keys()) - set(before_wheels.keys())
    removed_candidates = set(before_wheels.keys()) - required_packages

    # 实际删除多余的 wheel 文件
    actually_removed = {}
    for pkg_name in removed_candidates:
        if pkg_name in before_wheels:
            file_to_remove = packages_dir / before_wheels[pkg_name]
            if file_to_remove.exists():
                actually_removed[pkg_name] = before_wheels[pkg_name]
                file_to_remove.unlink()
                print(f"  🗑 删除: {before_wheels[pkg_name]}")

    # ===== 7. 生成日志 + 拷贝新增 wheel =====
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_session_dir = export_log_dir / timestamp
    log_session_dir.mkdir(exist_ok=True)

    log_lines = []
    log_lines.append(f"docBrain 离线包同步日志")
    log_lines.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_lines.append(f"{'='*50}")
    log_lines.append(f"")
    log_lines.append(f"同步前包数量: {len(before_wheels)}")
    log_lines.append(f"同步后包数量: {len(after_wheels) - len(actually_removed)}")
    log_lines.append(f"需要的包总数: {len(required_packages)}")
    log_lines.append(f"")

    if added_names:
        log_lines.append(f"[新增] ({len(added_names)} 个)")
        new_wheels_dir = log_session_dir / "new_wheels"
        new_wheels_dir.mkdir(exist_ok=True)
        for pkg_name in sorted(added_names):
            filename = after_wheels[pkg_name]
            log_lines.append(f"  + {filename}")
            src = packages_dir / filename
            if src.exists():
                shutil.copy2(src, new_wheels_dir / filename)
    else:
        log_lines.append("[新增] 无")

    log_lines.append(f"")

    if actually_removed:
        log_lines.append(f"[删除] ({len(actually_removed)} 个)")
        for pkg_name in sorted(actually_removed):
            log_lines.append(f"  - {actually_removed[pkg_name]}")
    else:
        log_lines.append("[删除] 无")

    log_lines.append(f"")

    if version_updates:
        log_lines.append(f"[版本更新] ({len(version_updates)} 个)")
        update_wheels_dir = log_session_dir / "updated_wheels"
        update_wheels_dir.mkdir(exist_ok=True)
        for pkg_name in sorted(version_updates):
            info = version_updates[pkg_name]
            log_lines.append(f"  ↑ {pkg_name}: {info['old_ver']} → {info['new_ver']}")
            log_lines.append(f"    旧: {info['old_file']}")
            log_lines.append(f"    新: {info['new_file']}")
            # 拷贝新版本 wheel 到日志目录
            src = packages_dir / info['new_file']
            if src.exists():
                shutil.copy2(src, update_wheels_dir / info['new_file'])
    else:
        log_lines.append("[版本更新] 无")

    log_lines.append(f"")
    log_lines.append(f"{'='*50}")

    if not added_names and not actually_removed and not version_updates:
        log_lines.append("所有依赖已是最新，无变更。")

    log_content = "\n".join(log_lines)
    log_file = log_session_dir / "sync_log.txt"
    log_file.write_text(log_content, encoding="utf-8")

    # 打印摘要
    print()
    print(f"  {'='*40}")
    print(f"  同步完成:")
    print(f"    ✅ 新增: {len(added_names)} 个包")
    print(f"    🔄 版本更新: {len(version_updates)} 个包")
    print(f"    🗑 删除: {len(actually_removed)} 个包")
    print(f"    📄 日志: exportLog/{timestamp}/sync_log.txt")
    if added_names:
        print(f"    📦 新增wheel副本: exportLog/{timestamp}/new_wheels/")
    if version_updates:
        print(f"    📦 更新wheel副本: exportLog/{timestamp}/updated_wheels/")
    print(f"  {'='*40}")


if __name__ == "__main__":
    main()
