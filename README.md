# 🤖 Code-buddy: Multi-Provider AI Coding Agent

> A terminal-based autonomous coding agent built with Python, FastAPI, and Rich — with the freedom to bring your own API key and provider.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

Code-buddy is a terminal-first autonomous coding agent — like Claude Code or Cursor, but without vendor lock-in. It reads, writes, and executes code directly in your workspace, while letting you choose your AI provider and bring your own API key.

**Supported providers:** NVIDIA NIM · Groq · OpenAI · Google Gemini · OpenRouter (includes Anthropic Claude)

---

## ✨ Features

- **Native Terminal UI** — Beautiful CLI with live streaming, tool-call panels, and reasoning/thinking support (including DeepSeek-R1 style chain-of-thought).
- **Multi-Provider Support** — Switch between NVIDIA, Groq, OpenAI, Gemini, and OpenRouter on the fly.
- **Autonomous Tools** — The agent can `read_file`, `write_file`, `list_directory`, `grep`, and run arbitrary `bash` commands in your workspace.
- **Zero Config** — Prompts for your API key on first run and saves it locally. No `.env` file required.
- **Standalone `.exe`** — Ships as a single executable for Windows users without Python installed.

---

## 🚀 Getting Started (From Source)

### Prerequisites

- Python 3.12 or higher — [Download from python.org](https://python.org)
- Python 3.12 stable - [Download python 3.12](https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe)

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/Code-buddy.git
cd Code-buddy
```

**2. Create and activate a virtual environment**

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the agent**

```bash
python codebuddy.py
```

On first launch, Code-buddy will walk you through selecting a provider, entering your API key, and choosing a model. It then opens a native folder picker so you can point it at your workspace.

---

## 💻 Standalone Executable (No Python Needed)

Prefer to skip the setup entirely?

1. Head to the [**Releases**](../../releases) page.
2. Download `CodeBuddy.exe`.
3. Double-click to run.

On first launch it will prompt you to paste your API key, then create a `codebuddy_config.json` file in the same folder so you won't be asked again.

---

## 🔑 Getting API Keys

Code-buddy requires an API key from one of the supported providers. All free tiers are available to get started.

| Provider | Cost | Tutorial |
|---|---|---|
| [NVIDIA NIM](https://build.nvidia.com) | Free | [How to get NVIDIA NIM API Key](https://youtu.be/QV9aiTmeiMs) |
| [Groq](https://groq.com) | Free | [How to get Groq API Key](https://www.youtube.com/live/enEXwXC-ysQ?si=2mOxvDtMAcd8mhA0) |
| [OpenRouter](https://openrouter.ai) | Freemium | [How to get OpenRouter API Key](https://youtu.be/ZELx_OzYAQo) |
| [Google Gemini](https://aistudio.google.com) | Free | [How to get Google Gemini API Key](https://youtu.be/yZN5a12CZD8) |
| [OpenAI](https://platform.openai.com) | Paid | [How to get OpenAI API Key](https://youtu.be/AVU4eF18DyI) |

> **Tip:** If you want to use Anthropic Claude models, sign up for **OpenRouter** — it provides access to Claude without needing a direct Anthropic API key.
> **Note:** Recommended to Use only one model per API key. Expecially in NVIDIA NIM API

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Uvicorn, Pydantic |
| Terminal UI | Rich (markdown rendering, spinners, panels) |
| HTTP Client | httpx |
| Packaging | PyInstaller |

---

## 📁 Project Structure

```
code-buddy/
├── .gitignore                 # Ignores venv, __pycache__, config files, and build folders
├── README.md                  # Project documentation and setup guide
├── requirements.txt           # Python dependencies
├── codebuddy.py                      # Main entry point! Run this to start the agent (CLI UI, Prompts, Server Startup)
│
└── backend/                   # FastAPI & Agent Logic
    ├── __init__.py            # Empty file (makes it a Python package)
    ├── config.py              # Pydantic settings & PROVIDERS dict (NVIDIA, Groq, OpenAI, etc.)
    ├── nvidia_client.py       # LLMClient class (OpenAI-compatible wrapper for streaming & reasoning tokens)
    ├── tools.py               # Tool schemas & execution logic (read_file, write_file, run_bash, grep)
    ├── sessions.py            # SessionStore (Holds workspace path, API keys, and chat history per session)
    ├── agent.py               # Agent loop (Orchestrates API calls, tool execution, and SSE event yielding)
    └── main.py                # FastAPI app (Endpoints for /sessions, /chat, and /files)
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">Built with ❤️ for developers who want AI coding assistance without vendor lock-in.</p>
