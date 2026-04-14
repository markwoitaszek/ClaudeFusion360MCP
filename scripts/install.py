#!/usr/bin/env python3
"""One-command installer for ClaudeFusion360MCP.

Detects the OS, installs Python dependencies, and copies the Fusion 360
add-in to the correct location.

Usage:
    python scripts/install.py           # Install everything
    python scripts/install.py --dry-run # Show what would happen
"""
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ADDIN_SOURCE = PROJECT_ROOT / "fusion-addin"

# OS-specific Fusion 360 add-in directories
ADDIN_DIRS = {
    "Darwin": Path.home() / "Library" / "Application Support" / "Autodesk" / "Autodesk Fusion 360" / "API" / "AddIns",
    "Windows": Path(__import__("os").environ.get("APPDATA", ""))
    / "Autodesk"
    / "Autodesk Fusion 360"
    / "API"
    / "AddIns",
}


def detect_platform() -> tuple[str, Path]:
    """Return (os_name, addin_dir) for the current platform."""
    system = platform.system()
    if system not in ADDIN_DIRS:
        print(f"Unsupported platform: {system}. Only macOS and Windows are supported.")
        sys.exit(1)
    addin_dir = ADDIN_DIRS[system]
    return system, addin_dir


def check_prerequisites():
    """Verify Python version and pip availability."""
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
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        sys.exit(1)
    print("  Dependencies installed successfully.")


def deploy_addin(addin_dir: Path, dry_run: bool):
    """Copy the Fusion 360 add-in to the OS-specific directory."""
    print("\n[3/3] Deploying Fusion 360 add-in...")
    target = addin_dir / "FusionMCP"

    if dry_run:
        print(f"  DRY RUN: would copy {ADDIN_SOURCE} -> {target}")
        return

    if not addin_dir.exists():
        print(f"  Fusion 360 add-in directory not found: {addin_dir}")
        print("  Is Autodesk Fusion 360 installed? If so, create the directory manually:")
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
    print("\n" + "=" * 60)
    print("Installation complete!")
    print("=" * 60)
    print(
        """
Next steps:

1. Open Autodesk Fusion 360

2. Enable the add-in:
   Utilities > Scripts and Add-ins > Add-ins tab
   Find "FusionMCP" and check "Run on Startup"

3. Configure Claude Desktop (add to claude_desktop_config.json):
   {
     "mcpServers": {
       "fusion360": {
         "command": "python",
         "args": ["%s"]
       }
     }
   }

4. Restart Claude Desktop and start designing!
"""
        % str(PROJECT_ROOT / "mcp-server" / "fusion360_mcp_server.py")
    )


def main():
    dry_run = "--dry-run" in sys.argv

    print("ClaudeFusion360MCP Installer")
    print("=" * 40)

    system, addin_dir = detect_platform()
    print(f"\n[1/3] Detected platform: {system}")
    print(f"  Add-in directory: {addin_dir}")

    check_prerequisites()
    print(f"  Python: {sys.version.split()[0]}")

    install_dependencies(dry_run)
    deploy_addin(addin_dir, dry_run)

    if not dry_run:
        print_next_steps()
    else:
        print("\nDRY RUN complete. No changes were made.")


if __name__ == "__main__":
    main()
