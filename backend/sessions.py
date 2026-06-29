import uuid
import time
import json
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class Session:
    id: str
    workspace: Path
    model: str
    api_key: str
    base_url: str
    messages: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    
    def touch(self):
        self.last_active = time.time()

    def save_history(self):
        """Saves chat history to the workspace."""
        history_dir = self.workspace / ".codebuddy_history"
        history_dir.mkdir(exist_ok=True)
        hist_file = history_dir / f"{self.id}.json"
        with open(hist_file, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, indent=2)

    def load_history(self):
        """Loads chat history if it exists."""
        hist_file = self.workspace / ".codebuddy_history" / f"{self.id}.json"
        if hist_file.exists():
            with open(hist_file, "r", encoding="utf-8") as f:
                self.messages = json.load(f)

class SessionStore:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create(self, workspace: Path, model: str, api_key: str, base_url: str, resume_id: str = None) -> Session:
        sid = resume_id or uuid.uuid4().hex[:12]
        session = Session(
            id=sid,
            workspace=workspace.resolve(),
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
        session.load_history() # Load if resuming
        
        # If no history was loaded, initialize with system prompt
        if not session.messages:
            session.messages = [{
                "role": "system",
                "content": (
                    "You are an autonomous coding agent operating inside a Windows workspace. "
                    "Use the provided tools to read, write, and run code. "
                    "Prefer native file tools (read_file, write_file) for direct file manipulation. "
                    "Use `run_bash` for cmd commands and `run_powershell` for advanced Windows operations. "
                    
                    "WINDOWS POWERSHELL BEST PRACTICES:\n"
                    "1. STRUCTURAL OUTPUT PARSING: Force PowerShell to return clean JSON data.\n"
                    "   Example: Get-ChildItem | Select-Object Name, Length | ConvertTo-Json\n"
                    "2. TEXT MATCHING: Use Select-String to find text with line numbers.\n"
                    "   Example: Select-String -Pattern 'API_KEY' config.env | Select-Object LineNumber, Line | ConvertTo-Json\n"
                    "3. ERROR HANDLING: Use try/catch blocks to prevent agent crashes.\n"
                    "   Example: try { Remove-Item 'file.txt' -ErrorAction Stop } catch { Write-Output 'Error: $_' }\n"
                    "4. CHAINING: Use `if (-not $?) { Write-Output 'Failed' }` to check if the last command succeeded.\n"
                    
                    "Think step-by-step. Always verify your changes. Be concise."
                ),
            }]
            
        self._sessions[sid] = session
        return session

    def get(self, sid: str) -> Session | None:
        s = self._sessions.get(sid)
        if s:
            s.touch()
        return s

    def list_sessions(self) -> list[Session]:
        return list(self._sessions.values())

sessions = SessionStore()