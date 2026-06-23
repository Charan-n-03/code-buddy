import uuid
import time
from dataclasses import dataclass, field
from pathlib import Path

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

class SessionStore:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create(self, workspace: Path, model: str, api_key: str, base_url: str) -> Session:
        sid = uuid.uuid4().hex[:12]
        session = Session(
            id=sid,
            workspace=workspace.resolve(),
            model=model,
            api_key=api_key,
            base_url=base_url,
            messages=[{
                "role": "system",
                "content": (
                    "You are an autonomous coding agent operating inside a workspace. "
                    "Use the provided tools to read, write, and run code to accomplish the user's task. "
                    "Think step-by-step. Always verify your changes. Be concise."
                ),
            }],
        )
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