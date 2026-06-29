import os
import sys
import time
import json
import threading
import tkinter as tk
from tkinter import filedialog
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.syntax import Syntax

# Import provider list
from backend.config import PROVIDERS

BANNER = r"""
          )  (                            (     (         )
   (   ( ╱(  )╲ )              (          )╲ )  )╲ )   ( ╱(
   )╲  )╲())(()╱(   (        ( )╲     (  (()╱( (()╱(   )╲())
 (((_)((_)╲  ╱(_))  )╲  ___  )((_)    )╲  ╱(_)) ╱(_)) ((_)╲
 )╲___  ((_)(_))_  ((_)│___│((_)_  _ ((_)(_))_ (_))_ __ ((_)
((╱ __│╱ _ ╲ │   ╲ │ __│     │ _ )│ │ │ │ │   ╲ │   ╲╲ ╲ ╱ ╱
 │ (__│ (_) ││ │) ││ _│      │ _ ╲│ │_│ │ │ │) ││ │) │╲ V ╱
  ╲___│╲___╱ │___╱ │___│     │___╱ ╲___╱  │___╱ │___╱  │_│   -BY CHARAN
"""

console = Console()
CONFIG_FILE = "codebuddy_config.json"

def render_tool_call(name: str, args: dict):
    body = Syntax(json.dumps(args, indent=2), "json", theme="monokai", word_wrap=True)
    console.print(Panel(body, title=f"🔧 Tool Call: {name}", border_style="cyan", expand=False))

def render_tool_result(name: str, result: str):
    display = result if len(result) < 2000 else result[:2000] + "\n…[truncated]"
    console.print(Panel(display, title=f"↩ {name} result", border_style="green", expand=False))

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def start_server(app):
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

def run_cli(workspace, model, provider, api_key):
    import httpx
    base_url = "http://127.0.0.1:8000"
    
    console.print(BANNER, style="bold orange3")
    console.print(Panel("Welcome to the CODE-BUDDY research preview!", style="bold white", expand=False))
    console.print("[bold green]Login successful.[/bold green] [dim]Press Enter to continue...[/]")
    input()
    
    console.clear()
    console.print(BANNER, style="bold orange3")
    console.print(f"[bold cyan]Workspace:[/] {workspace}")
    console.print(f"[bold cyan]Provider:[/] {provider}")
    console.print(f"[bold cyan]Model:[/]     {model}")
    console.print("[dim]Type 'exit' to quit.[/]\n")
    
    try:
        r = httpx.post(f"{base_url}/sessions", json={
            "workspace": workspace,
            "model": model,
            "provider": provider,
            "api_key": api_key
        }, timeout=30)
        r.raise_for_status()
        sess = r.json()
    except Exception as e:
        console.print(f"[red]Failed to create session:[/] {e}")
        return

    while True:
        try:
            console.print("\n[bold blue]┌─ You ─────────────────────────────[/bold blue]")
            user_input = console.input("[bold blue]└─>[/] ")
        except (EOFError, KeyboardInterrupt):
            break
        
        if user_input.strip().lower() in {"exit", "quit"}: break
        if not user_input.strip(): continue

        console.print("\n[bold magenta]┌─ Assistant ───────────────────────[/bold magenta]")
        
        from rich.live import Live
        spinner_live = Live(Spinner("dots", text="Thinking...", style="cyan"), refresh_per_second=10, console=console, transient=True)
        spinner_live.start()
        is_thinking = True
        
        try:
            with httpx.stream("POST", f"{base_url}/sessions/{sess['session_id']}/chat", json={"message": user_input}, timeout=600.0) as resp:
                resp.raise_for_status()
                event_type = None
                data_buf = ""
                
                for line in resp.iter_lines():
                    if not line: continue
                    if line.startswith("event:"): event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        data_buf = line[5:].strip()
                        if event_type and data_buf:
                            ev = json.loads(data_buf)
                            if ev["type"] == "text":
                                if is_thinking:
                                    spinner_live.stop()
                                    is_thinking = False
                                console.print(ev["text"], end="", markup=False, highlight=False)
                            elif ev["type"] == "tool_call":
                                if not is_thinking: console.print() 
                                else: spinner_live.stop(); is_thinking = False
                                render_tool_call(ev["name"], ev["args"])
                            elif ev["type"] == "tool_result":
                                render_tool_result(ev["name"], ev["result"])
                            elif ev["type"] == "error":
                                if not is_thinking: console.print()
                                else: spinner_live.stop(); is_thinking = False
                                console.print(f"[red]ERROR:[/] {ev['message']}")
                            elif ev["type"] == "done":
                                if not is_thinking: console.print() 
                                else: spinner_live.stop(); is_thinking = False
                                break
                            event_type = None; data_buf = ""
        except Exception as e:
            if is_thinking: spinner_live.stop()
            console.print(f"\n[red]Stream error:[/] {e}")
        
        console.print("[bold magenta]└───────────────────────────────────[/bold magenta]")

def main():
    config = load_config()
    
    # 1. Select Provider
    console.print(BANNER, style="bold orange3")
    console.print("[bold cyan]Select API Provider:[/]")
    providers = list(PROVIDERS.keys())
    for i, p in enumerate(providers, 1):
        console.print(f"[{i}] {p}")
    
    p_choice = console.input("[bold yellow]Enter choice: [/]")
    try:
        provider = providers[int(p_choice)-1]
    except:
        provider = "NVIDIA"
        
    # 2. Check API Key for selected provider
    api_key_env = f"{provider.upper()}_API_KEY"
    api_key = config.get(api_key_env, "")
    expected_prefix = PROVIDERS[provider].get("key_prefix", "")
    
    if not api_key:
        console.print(f"\n[bold cyan]You need an API key for {provider}.[/]")
        
        while True:
            prompt_text = f"[bold yellow]Enter {provider} API Key"
            if expected_prefix:
                prompt_text += f" (must start with '{expected_prefix}')"
            prompt_text += ": [/]"
            
            api_key = console.input(prompt_text).strip()
            
            if not api_key:
                console.print("[red]API key cannot be empty. Please try again.[/]")
                continue
                
            if expected_prefix and not api_key.startswith(expected_prefix):
                console.print(f"[red]Invalid format! The key must start with '{expected_prefix}'.[/]")
                continue
                
            # If it passes both checks, break the loop
            break
            
        config[api_key_env] = api_key
        save_config(config)
        console.print("[green]API Key saved locally! ✔[/]\n")
        
    # 3. Select Model
    # 3. Select Model (Dynamically fetched, filtering for FREE models!)
    console.print(f"\n[bold cyan]Fetching available FREE {provider} models...[/]")
    import httpx
    base_url = PROVIDERS[provider]["base_url"]
    
    models = []
    try:
        res = httpx.get(f"{base_url}/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        res.raise_for_status()
        raw_models = res.json().get("data", [])
        
        for m in raw_models:
            model_id = m["id"]
            
            # Skip embedding, audio, and image models
            if any(x in model_id.lower() for x in ["embed", "tts", "whisper", "dall-e", "image", "vision"]):
                continue
                
            # OpenRouter specific check: pricing.prompt == "0" means it's free
            if provider == "OpenRouter":
                pricing = m.get("pricing", {})
                if pricing.get("prompt") == "0" and pricing.get("completion") == "0":
                    models.append(model_id)
            # Groq & NVIDIA are generally free with API limits, so include all chat models
            elif provider in ["Groq", "NVIDIA"]:
                models.append(model_id)
            # Gemini: Free tier exists for flash models, we'll include standard chat models
            elif provider == "Gemini":
                if "gemini" in model_id.lower():
                    models.append(model_id)
            # OpenAI: Fallback to hardcoded (since none are free)
            else:
                if model_id in PROVIDERS[provider]["models"]:
                    models.append(model_id)
                    
    except Exception as e:
        console.print(f"[yellow]Failed to fetch live models ({e}). Using default list.[/]")
        models = PROVIDERS[provider]["models"]

    # If API fetch returned nothing useful, fallback to config
    if not models:
        models = PROVIDERS[provider]["models"]

    # Sort alphabetically for a cleaner menu
    models.sort()
    
    console.print(f"[bold cyan]Select {provider} Model (showing {min(len(models), 30)} of {len(models)}):[/]")
    
    # Show up to 30 models to avoid spamming the terminal
    display_models = models[:50]
    for i, m in enumerate(display_models, 1):
        console.print(f"[{i}] {m}")
        
    m_choice = console.input("[bold yellow]Enter choice (or type exact model name): [/]")
    try:
        # If they typed a number, get from the displayed list
        if m_choice.isdigit():
            model = display_models[int(m_choice)-1]
        # If they typed a custom string, use it directly
        else:
            model = m_choice
            
    except Exception:
        # Fallback if they type an invalid number
        model = models[0] if models else "gpt-4o-mini"
        
    console.print(f"[green]Selected model: {model}[/]")
        
    # 4. Import backend and start
    from backend.main import app
    
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    workspace = filedialog.askdirectory(title="Select Workspace Folder for CODE-BUDDY")
    root.destroy()
    
    if not workspace:
        console.print("[red]No workspace selected. Exiting.[/]")
        sys.exit(0)
        
    console.print("[dim]Starting backend...[/]")
    server_thread = threading.Thread(target=start_server, args=(app,), daemon=True)
    server_thread.start()
    time.sleep(2)

    run_cli(workspace, model, provider, api_key)
    sys.exit(0)

if __name__ == "__main__":
    main()