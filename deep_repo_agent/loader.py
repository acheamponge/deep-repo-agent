import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    ".turbo",
    "target",
    ".idea",
    ".vscode",
    ".claude",
}

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".tar",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
    ".mp3",
    ".mp4",
    ".mov",
    ".pyc",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".bin",
    ".lock",
    ".sqlite",
    ".db",
}

MAX_TREE_ENTRIES = 400


@dataclass
class Repo:
    root: Path
    name: str
    cloned: bool


def load_repo(source: str) -> Repo:
    if source.startswith(("http://", "https://", "git@")):
        name = _repo_name(source)
        target = Path(tempfile.mkdtemp(prefix="deep-repo-agent-")) / name
        subprocess.run(
            ["git", "clone", "--depth", "1", source, str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
        return Repo(root=target, name=name, cloned=True)
    path = Path(source).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"{source} is not a local directory or a git URL")
    return Repo(root=path, name=path.name, cloned=False)


def _repo_name(url: str) -> str:
    return url.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1]


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if path.suffix.lower() in BINARY_EXTENSIONS:
                continue
            yield path


def build_tree(root: Path, limit: int = MAX_TREE_ENTRIES) -> str:
    lines: list[str] = []
    for path in iter_files(root):
        lines.append(str(path.relative_to(root)))
        if len(lines) >= limit:
            lines.append(f"... truncated at {limit} files")
            break
    return "\n".join(lines)
