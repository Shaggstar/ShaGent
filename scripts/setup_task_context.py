#!/usr/bin/env python3
"""
Interactive script to gather context for your tasks.

Usage:
    python scripts/setup_task_context.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.server.context_store import (
    CONTEXTS_FILE,
    CONTEXT_QUESTIONS,
    load_contexts,
    save_contexts,
)
from app.server.goals import load_goals

console = Console()


def show_task_table(df: pd.DataFrame, contexts: Dict[str, Dict]) -> None:
    table = Table(title="Your Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Task", style="white")
    table.add_column("Domain", style="magenta")
    table.add_column("Status", style="bold")

    for idx, row in df.iterrows():
        task_id = str(idx)
        context = contexts.get(task_id, {})
        needs_context = bool(
            CONTEXT_QUESTIONS.get(row["domain"], {}).get(row["objective"], [])
        )
        ready = bool(context.get("answers")) or not needs_context
        status = "[green]✓ Ready[/green]" if ready else "[red]⚠ Needs Context[/red]"

        task_display = row["task"]
        if len(task_display) > 50:
            task_display = task_display[:47] + "..."

        table.add_row(task_id, task_display, f"{row['domain']}", status)

    console.print(table)


def gather_context_for_task(task_id: str, row: pd.Series, contexts: Dict[str, Dict]) -> None:
    console.print(
        Panel(
            f"[bold cyan]{row['task']}[/bold cyan]\n\n"
            f"Domain: {row['domain']}\n"
            f"Objective: {row['objective']}\n"
            f"Priority: {row.get('priority')}\n"
            f"Time: {row.get('minutes', 'n/a')} minutes",
            title="Task Details",
        )
    )

    questions = CONTEXT_QUESTIONS.get(row["domain"], {}).get(row["objective"], [])
    if not questions:
        console.print("[green]This task doesn't require context setup![/green]")
        contexts[task_id] = {
            "answers": {},
            "timestamp": datetime.now().isoformat(),
            "status": "ready",
        }
        return

    console.print("\n[bold]Please answer these questions to make this task actionable:[/bold]\n")

    answers: Dict[str, str] = {}
    for idx, question in enumerate(questions, 1):
        console.print(f"[cyan]{idx}. {question}[/cyan]")
        answer = Prompt.ask("Your answer")
        answers[question] = answer
        console.print()

    contexts[task_id] = {
        "answers": answers,
        "timestamp": datetime.now().isoformat(),
        "status": "ready",
    }
    console.print("[green]✓ Context saved! This task is now ready to start.[/green]\n")


def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Task Context Setup[/bold cyan]\n\n"
            "Gather the context you need so every task is actionable the moment you sit down.",
            border_style="cyan",
        )
    )

    df = load_goals()
    contexts = load_contexts()
    active = df[df.get("status", "") != "Done"].copy()

    while True:
        console.print("\n" + "=" * 60 + "\n")
        show_task_table(active, contexts)

        console.print("\n[bold]Options:[/bold]")
        console.print("1. Add context for a specific task (by ID)")
        console.print("2. Set up all high-priority tasks (P0–P1)")
        console.print("3. Review what's ready vs needs context")
        console.print("4. Save and exit")
        choice = Prompt.ask("\nWhat would you like to do?", choices=["1", "2", "3", "4"])

        if choice == "1":
            task_id = Prompt.ask("Enter task ID")
            if not task_id.isdigit() or int(task_id) not in active.index:
                console.print("[red]Invalid task ID[/red]")
                continue
            gather_context_for_task(task_id, active.loc[int(task_id)], contexts)
            save_contexts(contexts)

        elif choice == "2":
            high_priority = active[active.get("priority_num", 3) <= 2]
            console.print(
                f"\n[bold]Setting up {len(high_priority)} high-priority tasks...[/bold]\n"
            )
            for idx, row in high_priority.iterrows():
                task_id = str(idx)
                context = contexts.get(task_id, {})
                questions = CONTEXT_QUESTIONS.get(row["domain"], {}).get(row["objective"], [])
                if not questions or context.get("answers"):
                    console.print(
                        f"[dim]Skipping {row['task'][:40]}... context already set or not required[/dim]"
                    )
                    continue
                gather_context_for_task(task_id, row, contexts)
                save_contexts(contexts)
                if not Confirm.ask("Continue to next task?"):
                    break

        elif choice == "3":
            ready, needs = [], []
            for idx, row in active.iterrows():
                task_id = str(idx)
                context = contexts.get(task_id, {})
                questions = CONTEXT_QUESTIONS.get(row["domain"], {}).get(row["objective"], [])
                if context.get("answers") or not questions:
                    ready.append(row["task"])
                else:
                    needs.append(row["task"])

            console.print("\n[bold green]Ready to Start:[/bold green]")
            for task in ready or ["(none yet)"]:
                console.print(f"  ✓ {task[:60]}")

            console.print("\n[bold red]Needs Context:[/bold red]")
            for task in needs or ["(none – you're all set)"]:
                console.print(f"  ⚠ {task[:60]}")

            Prompt.ask("\nPress Enter to continue")

        else:
            save_contexts(contexts)
            console.print("\n[green]Context saved! Your tasks are ready.[/green]")
            console.print("\nStart your day with:")
            console.print("[cyan]uvicorn app.server.main:app --reload --port 9999[/cyan]")
            console.print("Then open:")
            console.print("[cyan]http://localhost:9999/ui/day.html[/cyan]\n")
            break


if __name__ == "__main__":
    main()
