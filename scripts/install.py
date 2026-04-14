#!/usr/bin/env python3
"""One-command installer for ClaudeFusion360MCP.

Detects the OS, installs Python dependencies, and copies the Fusion 360
add-in to the correct location.

Usage:
    python scripts/install.py           # Install everything
    python scripts/install.py --dry-run # Show what would happen
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ADDIN_SOURCE = PROJECT_ROOT / "fusion-addin"
BANNER_WIDTH = 60


def _get_addin_dirs() -> dict[str, Path]:
    """Build OS-specific Fusion 360 add-in directory map.

    Validates APPDATA on Windows rather than silently falling back to an
    empty string (which would create a relative path and bypass safety checks).
    """
    dirs: dict[str, Path] = {
        "Darwin": Path.home()
        / "Library"
        / "Application Support"
        / "Autodesk"
        / "Autodesk Fusion 360"
        / "API"
        / "AddIns",
    }
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            print("APPDATA environment variable is not set. Cannot locate Fusion 360 add-in directory.")
            sys.exit(1)
        dirs["Windows"] = Path(appdata) / "Autodesk" / "Autodesk Fusion 360" / "API" / "AddIns"
    return dirs


def detect_platform() -> tuple[str, Path]:
    """Return (os_name, addin_dir) for the current platform."""
    system = platform.system()
    addin_dirs = _get_addin_dirs()
    if system not in addin_dirs:
        print(f"Unsupported platform: {system}. Only macOS and Windows are supported.")
        sys.exit(1)
    addin_dir = addin_dirs[system]
    return system, addin_dir


def check_prerequisites(dry_run: bool = False):
    """Verify Python version and pip availability."""
    if dry_run:
        py_version = sys.version.split()[0]
        ok = sys.version_info >= (3, 10)
        print(f"  DRY RUN: Python {py_version} {'meets' if ok else 'does NOT meet'} >= 3.10 requirement")
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, check=True)
            print("  DRY RUN: pip is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  DRY RUN: pip is NOT available — install would fail")
        return

    if sys.version_info < (3, 10):
        print(f"Python 3.10+ required (found {sys.version})")
        sys.exit(1)

    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pip is not available. Install pip first: https://pip.pypa.io/en/stable/installation/")
        sys.exit(1)


def install_dependencies(dry_run: bool):
    """Install MCP server dependencies via pip."""
    print("\n[2/3] Installing Python dependencies...")
    cmd = [sys.executable, "-m", "pip", "install", "-e", str(PROJECT_ROOT)]
    if dry_run:
        print(f"  DRY RUN: would run: {' '.join(cmd)}")
        return
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  pip install failed:\n{result.stderr}")
        sys.exit(1)
    print("  Dependencies installed successfully.")


def deploy_addin(addin_dir: Path, dry_run: bool):
    """Copy the Fusion 360 add-in to the OS-specific directory."""
    system = platform.system()
    print("\n[3/3] Deploying Fusion 360 add-in...")
    target = addin_dir / "FusionMCP"

    if dry_run:
        print(f"  DRY RUN: would copy {ADDIN_SOURCE} -> {target}")
        return

    if not addin_dir.exists():
        print(f"  Fusion 360 add-in directory not found: {addin_dir}")
        print("  Is Autodesk Fusion 360 installed? If so, create the directory manually:")
        if system == "Windows":
            print(f'    mkdir "{addin_dir}"')
        else:
            print(f"    mkdir -p '{addin_dir}'")
        sys.exit(1)

    # Safety: resolve real path to prevent symlink-based writes outside home
    real_addin_dir = addin_dir.resolve()
    if not real_addin_dir.is_relative_to(Path.home().resolve()):
        print(f"  Add-in directory resolved outside home: {real_addin_dir}")
        sys.exit(1)

    real_target = (real_addin_dir / "FusionMCP").resolve()
    if not real_target.is_relative_to(Path.home().resolve()):
        print(f"  Target path resolved outside home: {real_target}")
        sys.exit(1)

    if target.exists():
        print(f"  Existing installation found at {target}. Backing up...")
        backup = target.with_name("FusionMCP.backup")
        if backup.exists():
            shutil.rmtree(backup)
        target.rename(backup)
        print(f"  Backup created at {backup}")

    shutil.copytree(ADDIN_SOURCE, target, symlinks=False)
    print(f"  Add-in deployed to {target}")


def print_next_steps():
    """Print manual configuration steps after installation."""
    server_path = str(PROJECT_ROOT / "mcp-server" / "fusion360_mcp_server.py")
    python_cmd = sys.executable
    print("\n" + "=" * BANNER_WIDTH)
    print("Installation complete!")
    print("=" * BANNER_WIDTH)
    print(
        f"""
Next steps:

1. Open Autodesk Fusion 360

2. Enable the add-in:
   Utilities > Scripts and Add-ins > Add-ins tab
   Find "FusionMCP" and check "Run on Startup"

3. Configure Claude Desktop (add to claude_desktop_config.json):
   {{
     "mcpServers": {{
       "fusion360": {{
         "command": "{python_cmd}",
         "args": ["{server_path}"]
       }}
     }}
   }}

4. Restart Claude Desktop and start designing!
"""
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Install ClaudeFusion360MCP")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without making changes")
    args = parser.parse_args()
    dry_run = args.dry_run

    print("ClaudeFusion360MCP Installer")
    print("=" * BANNER_WIDTH)

    system, addin_dir = detect_platform()
    print(f"\n[1/3] Detected platform: {system}")
    print(f"  Add-in directory: {addin_dir}")

    check_prerequisites(dry_run)
    print(f"  Python: {sys.version.split()[0]}")

    install_dependencies(dry_run)
    deploy_addin(addin_dir, dry_run)

    if not dry_run:
        print_next_steps()
    else:
        print("\nDRY RUN complete. No changes were made.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
