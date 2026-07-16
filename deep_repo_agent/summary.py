from langchain_crusoe import ChatCrusoe
from pydantic import BaseModel, Field

from deep_repo_agent.loader import Repo, build_tree

SUMMARY_MODEL = "zai/GLM-5.2"

DOC_FILES = (
    "README.md",
    "README.rst",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
)

MAX_DOC_CHARS = 12_000


class Component(BaseModel):
    """A significant file or directory in the repository."""

    path: str = Field(description="Path relative to the repository root")
    role: str = Field(description="What this component does")


class RepoSummary(BaseModel):
    """Structured summary of a code repository."""

    purpose: str = Field(description="One paragraph on what the project does and who it is for")
    primary_language: str = Field(description="Main programming language")
    key_components: list[Component] = Field(description="The most important files or directories")
    entry_points: list[str] = Field(description="Files where execution starts")
    how_to_run: str = Field(description="Shortest path to running the project locally")
    notable_dependencies: list[str] = Field(description="Key external libraries or services")


def summarize(repo: Repo, model: str = SUMMARY_MODEL) -> RepoSummary:
    docs = []
    for name in DOC_FILES:
        path = repo.root / name
        if path.is_file():
            docs.append(f"--- {name} ---\n{path.read_text(errors='replace')[:MAX_DOC_CHARS]}")
    llm = ChatCrusoe(model=model, temperature=0)
    structured = llm.with_structured_output(RepoSummary)
    prompt = (
        f'Summarize the repository "{repo.name}".\n\n'
        f"File map:\n{build_tree(repo.root)}\n\n" + "\n\n".join(docs)
    )
    return structured.invoke(prompt)
