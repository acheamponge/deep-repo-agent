import argparse
import os
import shutil
import sys

from langgraph.errors import GraphRecursionError
from rich.console import Console
from rich.json import JSON
from rich.markdown import Markdown

from deep_repo_agent.agent import DEFAULT_MODEL, build_repo_agent
from deep_repo_agent.loader import load_repo
from deep_repo_agent.summary import SUMMARY_MODEL, summarize


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="deep-repo-agent",
        description="Chat with any GitHub repository, powered by Crusoe Managed Inference.",
    )
    parser.add_argument("source", help="GitHub URL or local path of the repository")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Crusoe model for the agent (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help=f"Print a structured summary (via {SUMMARY_MODEL}) and exit",
    )
    args = parser.parse_args()

    os.environ.setdefault("CRUSOE_API_BASE", "https://api.inference.crusoecloud.com/v1")
    if not os.environ.get("CRUSOE_API_KEY"):
        sys.exit(
            "Set CRUSOE_API_KEY first — get a key at https://console.crusoecloud.com/"
        )

    console = Console()
    with console.status(f"Loading {args.source} ..."):
        repo = load_repo(args.source)

    try:
        if args.summary:
            with console.status(f"Summarizing with {SUMMARY_MODEL} ..."):
                result = summarize(repo)
            console.print(JSON(result.model_dump_json()))
            return

        agent = build_repo_agent(repo, model=args.model)
        console.print(f"[bold]deep-repo-agent[/] · {repo.name} · {args.model}")
        console.print("Ask anything about the codebase. Type /exit to quit.\n")

        messages: list = []
        while True:
            try:
                question = console.input("[bold cyan]you>[/] ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not question:
                continue
            if question in {"/exit", "/quit"}:
                break

            messages.append({"role": "user", "content": question})
            try:
                with console.status(f"{args.model} thinking ..."):
                    result = agent.invoke(
                        {"messages": messages},
                        config={"recursion_limit": 60},
                    )
            except GraphRecursionError:
                messages.pop()
                console.print(
                    "[yellow]The agent ran out of exploration steps on that one — "
                    "try a narrower question.[/]\n"
                )
                continue

            for message in result["messages"][len(messages):]:
                for call in getattr(message, "tool_calls", None) or []:
                    rendered = ", ".join(
                        f"{key}={value!r}" for key, value in call["args"].items()
                    )
                    console.print(f"[dim]→ {call['name']}({rendered[:120]})[/]")
            console.print(Markdown(result["messages"][-1].content))
            console.print()
            messages = result["messages"]
    finally:
        if repo.cloned:
            shutil.rmtree(repo.root.parent, ignore_errors=True)


if __name__ == "__main__":
    main()
