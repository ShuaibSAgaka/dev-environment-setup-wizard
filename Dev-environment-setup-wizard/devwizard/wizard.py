"""
wizard.py — Orchestrates all setup steps with a Rich UI
"""

import sys
import os
import time

from rich.text import Text
from .ui import (
    console, print_banner, section, step_panel,
    success, warn, info, error, confirm,
    spinner_task, progress_steps, summary_table, final_panel,
    C_ACCENT, C_WARN, C_ERR, C_SUCCESS, C_INFO, C_DIM
)
from . import checks


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _escape(value) -> str:
    """Escape brackets so Rich doesn't treat them as markup tags."""
    return str(value).replace("[", "\\[").replace("]", "\\]")


def _ok_or_warn(condition: bool, ok_msg: str, warn_msg: str):
    if condition:
        success(ok_msg)
    else:
        warn(warn_msg)


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Environment detection
# ─────────────────────────────────────────────────────────────────────────────

def step_detect_env() -> checks.EnvInfo:
    step_panel(1, 5, "Detect Environment", "Scanning your WSL/Ubuntu system...")
    env = spinner_task("Gathering system info...", checks.detect_environment)

    _ok_or_warn(
        env.is_wsl,
        f"Running inside WSL  ({_escape(env.distro)})",
        f"Not detected as WSL - continuing anyway  ({_escape(env.distro)})"
    )
    info(f"Kernel   : {_escape(env.kernel)}")
    info(f"Arch     : {_escape(env.arch)}")
    info(f"User     : {_escape(env.username)}  ({_escape(env.home)})")
    info(f"Shell    : {_escape(env.shell)}")
    return env


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — curl
# ─────────────────────────────────────────────────────────────────────────────

def step_curl() -> bool:
    step_panel(2, 5, "Check curl", "curl is required to download nvm")
    curl = spinner_task("Checking curl...", checks.check_curl)

    if curl.installed:
        ver_str = curl.version.split()[1] if curl.version else "?"
        success(f"curl already installed  (v{_escape(ver_str)})")
        return True

    warn("curl not found.")
    if not confirm("Install curl via apt?"):
        error("curl is required - cannot continue without it.")
        return False

    ok = spinner_task("Installing curl...", checks.install_curl)
    if ok:
        success("curl installed successfully.")
    else:
        error("curl installation failed. Run:  sudo apt-get install curl")
    return ok


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — nvm
# ─────────────────────────────────────────────────────────────────────────────

def step_nvm() -> bool:
    step_panel(3, 5, "Install nvm", "Node Version Manager keeps multiple Node versions side-by-side")
    nvm = spinner_task("Checking nvm...", checks.check_nvm)

    if nvm.installed:
        success(f"nvm already installed  ({_escape(nvm.version)})  ->  {_escape(nvm.nvm_dir)}")
        patched = checks.ensure_nvm_in_rc()
        if patched:
            info("Added nvm init lines to your shell RC.")
        return True

    warn("nvm not found.")
    if not confirm("Install nvm (recommended)?", default=True):
        warn("Skipping nvm. You can install Node manually later.")
        return False

    info("Downloading and running the nvm install script...")
    ok = spinner_task("Installing nvm...", checks.install_nvm)
    if ok:
        checks.ensure_nvm_in_rc()
        success("nvm installed and shell RC updated.")
        info("nvm will be active in new terminal sessions.")
    else:
        error("nvm installation failed.")
        info("Manual install:  https://github.com/nvm-sh/nvm#installing-and-updating")
    return ok


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Node.js LTS
# ─────────────────────────────────────────────────────────────────────────────

def step_node() -> bool:
    step_panel(4, 5, "Install Node.js LTS", "Installing the latest Long-Term Support release via nvm")
    node = spinner_task("Checking Node.js...", checks.check_node)

    if node.installed:
        via = "(via nvm)" if node.via_nvm else "(system)"
        success(f"Node.js already installed  ({_escape(node.version)})  {via}")

        npm = spinner_task("Checking npm...", checks.check_npm)
        if npm.installed:
            success(f"npm already installed  (v{_escape(npm.version)})")
            if npm.update_available:
                warn(f"npm update available: v{_escape(npm.version)} -> v{_escape(npm.latest_version)}")
                if confirm("Update npm to latest?"):
                    ok = spinner_task("Updating npm...", checks.update_npm)
                    if ok:
                        success("npm updated.")
                    else:
                        warn("npm update failed - try:  npm install -g npm@latest")
        return True

    if not confirm("Install Node.js LTS via nvm?", default=True):
        warn("Skipping Node.js installation.")
        return False

    info("Fetching latest LTS version tag...")
    lts = spinner_task("Resolving LTS...", checks.get_node_lts_version)
    if lts:
        info(f"Latest LTS: {_escape(lts)}")

    info("This may take a minute...")
    ok = spinner_task("Installing Node.js LTS...", checks.install_node_lts)
    if ok:
        node2 = checks.check_node()
        npm2  = checks.check_npm()
        success(f"Node.js installed  ({_escape(node2.version or '?')})")
        success(f"npm installed  (v{_escape(npm2.version or '?')})")
    else:
        error("Node.js installation failed.")
        info("Try manually:  nvm install --lts")
    return ok


# ─────────────────────────────────────────────────────────────────────────────
# Step 5 — Global npm packages
# ─────────────────────────────────────────────────────────────────────────────

def step_globals():
    step_panel(5, 5, "Global npm Packages", "Optional but highly recommended tools for every JS/TS project")

    console.print("  [bold cyan]Recommended globals:[/bold cyan]")
    for pkg, desc in checks.RECOMMENDED_GLOBALS:
        console.print(f"    [dim]*[/dim]  [bold]{pkg:<14}[/bold]  [dim]{desc}[/dim]")
    console.print()

    if not confirm("Check & install missing recommended globals?", default=True):
        warn("Skipping global packages.")
        return

    to_install = []
    info("Scanning installed globals...")
    for pkg, desc in checks.RECOMMENDED_GLOBALS:
        ver = checks.check_global_package(pkg)
        if ver:
            success(f"{pkg:<14}  already installed  (v{_escape(ver)})")
        else:
            warn(f"{pkg:<14}  not found")
            to_install.append(pkg)

    if not to_install:
        success("All recommended globals are already installed!")
        return

    console.print()
    if not confirm(f"Install {len(to_install)} missing package(s)?", default=True):
        warn("Skipping.")
        return

    steps = [
        (f"npm install -g {p}", lambda p=p: checks.install_global_package(p))
        for p in to_install
    ]
    results = progress_steps(steps)

    for pkg, ok in zip(to_install, results):
        if ok:
            success(f"{pkg} installed.")
        else:
            warn(f"{pkg} failed - try:  npm install -g {pkg}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

def print_summary():
    section("Installation Summary")

    rows = []

    env = checks.detect_environment()
    rows.append({
        "check": "WSL / Ubuntu",
        "status": "ok" if env.is_wsl else "warn",
        "detail": env.distro
    })

    curl = checks.check_curl()
    rows.append({
        "check": "curl",
        "status": "ok" if curl.installed else "fail",
        "detail": curl.version.split()[1] if curl.version else "not found"
    })

    nvm = checks.check_nvm()
    rows.append({
        "check": "nvm",
        "status": "ok" if nvm.installed else "fail",
        "detail": nvm.version or "not installed"
    })

    node = checks.check_node()
    via_label = " (nvm)" if node.via_nvm else ""
    rows.append({
        "check": "Node.js",
        "status": "ok" if node.installed else "fail",
        "detail": f"{node.version or 'not installed'}{via_label}"
    })

    npm = checks.check_npm()
    rows.append({
        "check": "npm",
        "status": "ok" if npm.installed else "fail",
        "detail": f"v{npm.version}" if npm.version else "not installed"
    })

    for pkg, _ in checks.RECOMMENDED_GLOBALS:
        ver = checks.check_global_package(pkg)
        rows.append({
            "check": f"npm global: {pkg}",
            "status": "ok" if ver else "skip",
            "detail": f"v{ver}" if ver else "not installed"
        })

    summary_table(rows)


def print_next_steps():
    final_panel("You're all set!", [
        "[bold]Reload your shell to activate nvm:[/bold]",
        "  source ~/.bashrc   [dim]# or ~/.zshrc[/dim]",
        "",
        "[bold]Quick Node.js commands:[/bold]",
        "  node --version          [dim]# check Node[/dim]",
        "  npm --version           [dim]# check npm[/dim]",
        "  nvm install --lts       [dim]# install a new LTS later[/dim]",
        "  nvm ls                  [dim]# list installed versions[/dim]",
        "  nvm use 20              [dim]# switch to Node 20[/dim]",
        "",
        "[bold]Start a new project:[/bold]",
        "  mkdir my-app && cd my-app",
        "  npm init -y",
        "",
        "[dim]Star this tool on GitHub if it helped you![/dim]",
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def run_wizard():
    print_banner()

    console.print("  [dim]This wizard will set up[/dim] [bold bright_green]Node.js + npm[/bold bright_green] [dim]on your WSL/Ubuntu machine.[/dim]")
    console.print("  [dim]It uses[/dim] [bold]nvm[/bold] [dim]for flexible version management.[/dim]")
    console.print()

    if not confirm("Ready to begin?", default=True):
        console.print("\n  [dim]Setup cancelled. Run[/dim] [bold]python main.py[/bold] [dim]whenever you're ready.[/dim]\n")
        sys.exit(0)

    env  = step_detect_env()
    ok2  = step_curl()
    if not ok2:
        sys.exit(1)
    ok3  = step_nvm()
    ok4  = step_node() if ok3 else False
    if ok4:
        step_globals()

    print_summary()
    print_next_steps()