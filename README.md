# ⚡ Dev Environment Setup Wizard

> **Day 1 of 30** — [30-Day GitHub Build Roadmap]  
> An interactive CLI tool that auto-configures **Node.js + npm** on **WSL/Ubuntu** with a beautiful Rich terminal UI.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Rich](https://img.shields.io/badge/Rich-TUI-brightgreen?style=flat-square)
![WSL](https://img.shields.io/badge/WSL-Ubuntu-E95420?style=flat-square&logo=ubuntu&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## ✨ What It Does

Runs an **interactive, step-by-step wizard** in your terminal that:

| Step | Action |
|------|--------|
| 1 | Detects your WSL/Ubuntu environment (kernel, distro, arch) |
| 2 | Checks / installs **curl** |
| 3 | Installs **nvm** (Node Version Manager) |
| 4 | Installs **Node.js LTS** + **npm** via nvm |
| 5 | Optionally installs **recommended global packages** (pnpm, yarn, nodemon, typescript, eslint) |
| ✅ | Prints a full **summary table** and next-steps guide |

Everything is interactive — it asks before it acts. Nothing is installed without your confirmation.

---

## 🖥️ Demo

```
 ██████╗ ███████╗██╗   ██╗    ██╗    ██╗██╗███████╗ █████╗ ██████╗ ██████╗
 ...
⚡  Dev Environment Setup Wizard  ·  Node.js + npm  ·  WSL/Ubuntu  ⚡

  ? Ready to begin? [Y/n]

  STEP 1/5   Detect Environment
  ✔  Running inside WSL  [Ubuntu 22.04.3 LTS]
  ℹ  Kernel   : 5.15.90.1-microsoft-standard-WSL2
  ℹ  Arch     : x86_64

  STEP 2/5   Check curl
  ✔  curl already installed  [8.1.2]

  STEP 3/5   Install nvm
  ⠴  Installing nvm…  0:00:04
  ✔  nvm installed and shell RC updated.

  ...
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- WSL 2 with Ubuntu (20.04 / 22.04 / 24.04)
- `sudo` privileges inside WSL

### Install & Run

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/dev-wizard.git
cd dev-wizard

# 2. Install Python dependency
pip install rich

# 3. Run the wizard
python main.py
```

### Or install as a CLI command

```bash
pip install -e .
devwizard
```

---

## 📁 Project Structure

```
dev-wizard/
├── main.py               # Entry point
├── requirements.txt      # Python deps (rich)
├── setup.py              # pip-installable package config
└── devwizard/
    ├── __init__.py
    ├── ui.py             # Rich TUI components (banner, panels, tables, progress)
    ├── checks.py         # System detection + curl/nvm/node/npm installers
    └── wizard.py         # Step orchestration & main flow
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| [Python 3.9+](https://python.org) | Core language |
| [Rich](https://github.com/Textualize/rich) | Beautiful terminal UI (panels, progress, tables, spinners) |
| [nvm](https://github.com/nvm-sh/nvm) | Node version management |
| `subprocess` / `shutil` | System detection & command execution |

---

## 🔧 Recommended Globals Installed

| Package | Description |
|---------|-------------|
| `pnpm` | Fast, disk-efficient package manager |
| `yarn` | Alternative package manager by Meta |
| `nodemon` | Auto-restart Node apps on file change |
| `typescript` | TypeScript compiler (`tsc`) |
| `eslint` | JavaScript/TypeScript linter |

---

## 🗺️ Roadmap

- [ ] Add Git + SSH key setup
- [ ] Add VS Code extensions installation via `code --install-extension`
- [ ] Support `.nvmrc` file detection in current directory
- [ ] Config file (`wizard.yml`) to pre-select tools
- [ ] `--dry-run` flag to preview without installing

---

## 📄 License

MIT © Shuaib S. Agaka

---
