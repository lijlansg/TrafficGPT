from __future__ import annotations
from typing import Any, Dict, List, Optional
from uuid import UUID
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish
from rich import print


class CustomHandler(BaseCallbackHandler):
    def __init__(self) -> None:
        super().__init__()
        self.memory: List[List[str]] = [[]]

    def on_agent_finish(self, finish: AgentFinish, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        self.memory.append([])
        return super().on_agent_finish(finish, run_id=run_id, parent_run_id=parent_run_id, **kwargs)

    def on_agent_action(self, action: AgentAction, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        self.memory[-1].append(action.log)
        return super().on_agent_action(action, run_id=run_id, parent_run_id=parent_run_id, **kwargs)
