from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class KeyResult:
    description: str
    target: float
    unit: str = ""

@dataclass
class Objective:
    title: str
    key_results: List[KeyResult] = field(default_factory=list)

@dataclass
class Goal:
    domain: str
    objective: Objective
    skills: List[str] = field(default_factory=list)
    priority: int = 3  # 1 high, 5 low

@dataclass
class Task:
    title: str
    minutes: int
    energy: str  # low, medium, high
    priority: int = 3
    tags: List[str] = field(default_factory=list)
