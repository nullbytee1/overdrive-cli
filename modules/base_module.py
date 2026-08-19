"""
OVERDRIVE - Base Optimization Module Interface
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any
from rich.console import Console
from core.ssh_client import SSHClientWrapper

class BaseOptimizerModule(ABC):
    def __init__(self, name: str, description: str, category: str = "General"):
        self.name = name
        self.description = description
        self.category = category

    @abstractmethod
    def run(self, ssh: SSHClientWrapper, console: Console) -> Tuple[bool, str]:
        """Executes the optimization logic on the remote target"""
        pass

    @abstractmethod
    def verify(self, ssh: SSHClientWrapper, console: Console) -> Dict[str, Any]:
        """Verifies the state and returns metric audit results"""
        pass
