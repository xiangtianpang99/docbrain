"""
docBrain 多余包清理工具

在 setup_intranet.bat 安装依赖后运行。
对比 runtime/python 中已安装的包和 offline_packages/ 中的包，
卸载不在离线包清单中的多余包（依赖被移除后的残留）。
"""

import subprocess
import sys
from pathlib import Path


# 不应被卸载的基础包
PROTECTED_PACKAGES = {
    "pip", "setuptools", "wheel", "_distutils_hack",
}


def get_wheel_package_name(filename: str) -> str:
    """从 wheel 文件名提取包名 (规范化为小写+下划线)"""
    return filename.split("-")[0].lower().replace("-", "_")


def main():
    project_root = Path(__file__).parent.parent.parent
    packages_dir = project_root / "offline_packages"

    # 确定 pip 路径
    runtime_pip = project_root / "runtime" / "python" / "Scripts" / "pip.exe"
    runtime_python = project_root / "runtime" / "python" / "python.exe"
    if not runtime_pip.exists():
        print("  [SKIP] 未找到 runtime pip，跳过清理。")
        return

    # 1. 获取已安装包列表
    result = subprocess.run(
        [str(runtime_pip), "list", "--format=json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("  [ERROR] 无法获取已安装包列表。")
        return

    import json
    installed = {}
    for pkg in json.loads(result.stdout):
        name = pkg["name"].lower().replace("-", "_")
        installed[name] = pkg["version"]

    # 2. 获取离线包中的包名集合
    offline_names = set()
    if packages_dir.exists():
        for f in packages_dir.iterdir():
            if f.suffix == ".whl":
                offline_names.add(get_wheel_package_name(f.name))

    # 3. 计算差集：已安装但不在离线包中的
    stale = set(installed.keys()) - offline_names - PROTECTED_PACKAGES

    if not stale:
        print("  ✓ 无多余包，环境干净。")
        return

    print(f"  发现 {len(stale)} 个多余包，正在清理...")
    for pkg_name in sorted(stale):
        version = installed.get(pkg_name, "?")
        print(f"    🗑 卸载: {pkg_name} ({version})")
        subprocess.run(
            [str(runtime_pip), "uninstall", pkg_name, "-y", "--quiet"],
            capture_output=True
        )

    print(f"  ✓ 清理完成，卸载了 {len(stale)} 个多余包。")


if __name__ == "__main__":
    main()
