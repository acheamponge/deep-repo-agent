import re

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_crusoe import ChatCrusoe

from deep_repo_agent.loader import Repo, build_tree, iter_files

DEFAULT_MODEL = "zai/GLM-5.2"
MAX_FILE_CHARS = 40_000
MAX_SEARCH_RESULTS = 50

SYSTEM_PROMPT = """You are deep-repo-agent, an expert guide to the repository "{name}".

Answer questions about this codebase with specifics: cite file paths and line numbers, \
quote the relevant code, and explain how the pieces connect. Use your tools to look \
before you answer — never guess at file contents. If a question can't be answered from \
the repository, say so.

Repository file map:
{tree}
"""


def build_tools(repo: Repo) -> list:
    @tool
    def list_files(subdirectory: str = "") -> str:
        """List files in the repository, optionally under a subdirectory."""
        base = (repo.root / subdirectory).resolve()
        if not base.is_relative_to(repo.root) or not base.is_dir():
            return f"No such directory: {subdirectory}"
        return build_tree(base)

    @tool
    def read_file(path: str, offset: int = 0) -> str:
        """Read a file from the repository. Use offset (in characters) to page through large files."""
        target = (repo.root / path).resolve()
        if not target.is_relative_to(repo.root) or not target.is_file():
            return f"No such file: {path}"
        try:
            text = target.read_text(errors="replace")
        except OSError as exc:
            return f"Could not read {path}: {exc}"
        chunk = text[offset : offset + MAX_FILE_CHARS]
        if offset + MAX_FILE_CHARS < len(text):
            chunk += (
                f"\n... truncated ({len(text)} chars total); "
                f"call again with offset={offset + MAX_FILE_CHARS}"
            )
        return chunk or f"{path} is empty"

    @tool
    def search_code(pattern: str) -> str:
        """Search every text file in the repository with a regular expression and return matching lines."""
        try:
            regex = re.compile(pattern)
        except re.error as exc:
            return f"Invalid regex: {exc}"
        hits: list[str] = []
        for path in iter_files(repo.root):
            try:
                lines = path.read_text(errors="replace").splitlines()
            except OSError:
                continue
            for number, line in enumerate(lines, 1):
                if regex.search(line):
                    rel = path.relative_to(repo.root)
                    hits.append(f"{rel}:{number}: {line.strip()[:200]}")
                    if len(hits) >= MAX_SEARCH_RESULTS:
                        hits.append(f"... stopped at {MAX_SEARCH_RESULTS} matches")
                        return "\n".join(hits)
        return "\n".join(hits) if hits else f"No matches for {pattern}"

    return [list_files, read_file, search_code]


def build_repo_agent(repo: Repo, model: str = DEFAULT_MODEL):
    llm = ChatCrusoe(model=model, temperature=0.2)
    prompt = SYSTEM_PROMPT.format(name=repo.name, tree=build_tree(repo.root))
    return create_react_agent(llm, build_tools(repo), prompt=prompt)
