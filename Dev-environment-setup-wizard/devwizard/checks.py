"""
checks.py — Detection & installation helpers for WSL/Ubuntu + Node.js/npm
"""

import subprocess
import shutil
import os
import re
from dataclasses import dataclass, field
from typing import Optional


# ── Helpers ──────────────────────────────────────────────────────────────────

def _run(cmd: str, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, shell=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        text=True
    )


def _which(name: str) -> Optional[str]:
    return shutil.which(name)


def _version(cmd: str) -> Optional[str]:
    r = _run(cmd)
    if r.returncode == 0:
        return r.stdout.strip().splitlines()[0]
    return None


# ── Environment Detection ────────────────────────────────────────────────────

@dataclass
class EnvInfo:
    is_wsl: bool = False
    distro: str = "Unknown"
    kernel: str = "Unknown"
    username: str = ""
    home: str = ""
    arch: str = ""
    shell: str = ""


def detect_environment() -> EnvInfo:
    env = EnvInfo()
    env.username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    env.home     = os.path.expanduser("~")
    env.shell    = os.environ.get("SHELL", "bash")

    # Kernel / WSL
    kernel_r = _run("uname -r")
    if kernel_r.returncode == 0:
        env.kernel = kernel_r.stdout.strip()
        env.is_wsl = "microsoft" in env.kernel.lower() or "WSL" in env.kernel

    # Arch
    arch_r = _run("uname -m")
    if arch_r.returncode == 0:
        env.arch = arch_r.stdout.strip()

    # Distro name
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    env.distro = line.split("=",1)[1].strip().strip('"')
                    break

    return env


# ── Package Manager ──────────────────────────────────────────────────────────

def apt_update() -> bool:
    r = _run("sudo apt-get update -qq")
    return r.returncode == 0


def apt_install(package: str) -> bool:
    r = _run(f"sudo apt-get install -y -qq {package}")
    return r.returncode == 0


# ── curl ─────────────────────────────────────────────────────────────────────

@dataclass
class CurlStatus:
    installed: bool = False
    version: Optional[str] = None
    path: Optional[str] = None


def check_curl() -> CurlStatus:
    s = CurlStatus()
    s.path = _which("curl")
    if s.path:
        s.installed = True
        s.version = _version("curl --version")
    return s


def install_curl() -> bool:
    return apt_install("curl")


# ── nvm ──────────────────────────────────────────────────────────────────────

NVM_DIR  = os.path.expanduser("~/.nvm")
NVM_INIT = f'export NVM_DIR="{NVM_DIR}"\n[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"'

@dataclass
class NvmStatus:
    installed: bool = False
    version: Optional[str] = None
    nvm_dir: str = NVM_DIR


def check_nvm() -> NvmStatus:
    s = NvmStatus()
    nvm_sh = os.path.join(NVM_DIR, "nvm.sh")
    if os.path.exists(nvm_sh):
        s.installed = True
        r = _run(f'bash -c \'. {nvm_sh} && nvm --version\'')
        if r.returncode == 0:
            s.version = "v" + r.stdout.strip()
    return s


def install_nvm() -> bool:
    """Download and run the nvm install script."""
    # Get latest nvm release tag
    r = _run("curl -s https://api.github.com/repos/nvm-sh/nvm/releases/latest")
    tag = "v0.39.7"  # fallback
    if r.returncode == 0:
        m = re.search(r'"tag_name":\s*"(v[\d.]+)"', r.stdout)
        if m:
            tag = m.group(1)

    install_url = f"https://raw.githubusercontent.com/nvm-sh/nvm/{tag}/install.sh"
    r = _run(f'curl -o- {install_url} | bash')
    return r.returncode == 0


# ── Node.js ──────────────────────────────────────────────────────────────────

@dataclass
class NodeStatus:
    installed: bool = False
    version: Optional[str] = None
    path: Optional[str] = None
    via_nvm: bool = False
    lts_available: Optional[str] = None


def _nvm_run(cmd: str) -> subprocess.CompletedProcess:
    nvm_sh = os.path.join(NVM_DIR, "nvm.sh")
    return _run(f'bash -c \'. {nvm_sh} && {cmd}\'')


def check_node() -> NodeStatus:
    s = NodeStatus()
    # First try nvm node
    nvm_sh = os.path.join(NVM_DIR, "nvm.sh")
    if os.path.exists(nvm_sh):
        r = _nvm_run("node --version")
        if r.returncode == 0:
            s.installed = True
            s.version   = r.stdout.strip()
            s.via_nvm   = True
            rp = _nvm_run("which node")
            s.path = rp.stdout.strip() if rp.returncode == 0 else None
            return s
    # Fallback: system node
    s.path = _which("node")
    if s.path:
        s.installed = True
        s.version   = _version("node --version")
    return s


def get_node_lts_version() -> Optional[str]:
    nvm_sh = os.path.join(NVM_DIR, "nvm.sh")
    if not os.path.exists(nvm_sh):
        return None
    r = _nvm_run("nvm ls-remote --lts | tail -1")
    if r.returncode == 0:
        m = re.search(r'v([\d.]+)', r.stdout)
        if m:
            return "v" + m.group(1)
    return None


def install_node_lts() -> bool:
    nvm_sh = os.path.join(NVM_DIR, "nvm.sh")
    if not os.path.exists(nvm_sh):
        return False
    r = _nvm_run("nvm install --lts && nvm use --lts && nvm alias default 'lts/*'")
    return r.returncode == 0


# ── npm ──────────────────────────────────────────────────────────────────────

@dataclass
class NpmStatus:
    installed: bool = False
    version: Optional[str] = None
    path: Optional[str] = None
    update_available: bool = False
    latest_version: Optional[str] = None


def check_npm() -> NpmStatus:
    s = NpmStatus()
    nvm_sh = os.path.join(NVM_DIR, "nvm.sh")
    if os.path.exists(nvm_sh):
        r = _nvm_run("npm --version")
        if r.returncode == 0:
            s.installed = True
            s.version   = r.stdout.strip()
            rp = _nvm_run("which npm")
            s.path = rp.stdout.strip() if rp.returncode == 0 else None
    if not s.installed:
        s.path = _which("npm")
        if s.path:
            s.installed = True
            s.version = _version("npm --version")
    # Check for newer npm
    if s.installed:
        r = _run("npm view npm version 2>/dev/null")
        if r.returncode == 0:
            s.latest_version = r.stdout.strip()
            if s.latest_version and s.version and s.latest_version != s.version:
                s.update_available = True
    return s


def update_npm() -> bool:
    nvm_sh = os.path.join(NVM_DIR, "nvm.sh")
    if os.path.exists(nvm_sh):
        r = _nvm_run("npm install -g npm@latest")
        return r.returncode == 0
    r = _run("npm install -g npm@latest")
    return r.returncode == 0


# ── Shell RC patching ────────────────────────────────────────────────────────

def _rc_file() -> str:
    shell = os.environ.get("SHELL", "bash")
    if "zsh" in shell:
        return os.path.expanduser("~/.zshrc")
    return os.path.expanduser("~/.bashrc")


def ensure_nvm_in_rc() -> bool:
    """Append nvm init lines to shell RC if not already present."""
    rc = _rc_file()
    try:
        content = open(rc).read() if os.path.exists(rc) else ""
        if "nvm.sh" not in content:
            with open(rc, "a") as f:
                f.write(f"\n# nvm — added by Dev Wizard\n{NVM_INIT}\n")
            return True
        return False   # already present
    except Exception:
        return False


# ── Global npm packages ──────────────────────────────────────────────────────

RECOMMENDED_GLOBALS = [
    ("pnpm",       "Fast, disk-efficient package manager"),
    ("yarn",       "Alternative package manager by Meta"),
    ("nodemon",    "Auto-restart Node apps on file change"),
    ("typescript", "TypeScript compiler (tsc)"),
    ("eslint",     "JavaScript/TypeScript linter"),
]


def check_global_package(pkg: str) -> Optional[str]:
    nvm_sh = os.path.join(NVM_DIR, "nvm.sh")
    if os.path.exists(nvm_sh):
        r = _nvm_run(f"npm list -g {pkg} --depth=0 2>/dev/null | grep {pkg}")
    else:
        r = _run(f"npm list -g {pkg} --depth=0 2>/dev/null | grep {pkg}")
    if r.returncode == 0 and pkg in r.stdout:
        m = re.search(r'@([\d.]+)', r.stdout)
        return m.group(1) if m else "installed"
    return None


def install_global_package(pkg: str) -> bool:
    nvm_sh = os.path.join(NVM_DIR, "nvm.sh")
    if os.path.exists(nvm_sh):
        r = _nvm_run(f"npm install -g {pkg}")
    else:
        r = _run(f"npm install -g {pkg}")
    return r.returncode == 0