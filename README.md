# deep-repo-agent

Chat with any GitHub repository from your terminal. A long-context codebase agent
built on [langchain-crusoe](https://github.com/acheamponge/langchain-crusoe) and
[Crusoe Managed Inference](https://docs.crusoecloud.com/managed-inference/overview),
featuring GLM-5.2 and its 256k context window.

Point it at a repo — a GitHub URL or a local path — and ask questions:
architecture explanations, "where is X handled?", change-impact analysis. The agent
explores the codebase with tools (file tree, file reads, regex search), cites file
paths and line numbers, and quotes the code it's talking about.

## Quickstart

```bash
pip install deep-repo-agent

export CRUSOE_API_KEY="your-key"   # https://console.crusoecloud.com/

deep-repo-agent https://github.com/pallets/flask
```

```
deep-repo-agent · flask · zai/GLM-5.2
Ask anything about the codebase. Type /exit to quit.

you> how does the routing system map a URL to a view function?
→ search_code(pattern='add_url_rule')
→ read_file(path='src/flask/app.py')
...
```

Or run it against the code you're sitting in:

```bash
deep-repo-agent .
```

## Structured summaries

Get a machine-readable overview of any repo — purpose, key components, entry
points, how to run it:

```bash
deep-repo-agent https://github.com/tiangolo/fastapi --summary
```

Summaries use structured output (a validated Pydantic schema), served by
`zai/GLM-5.2`.

## Models

Everything runs on Crusoe's OpenAI-compatible endpoint at
`https://api.inference.crusoecloud.com/v1`.

Everything — the agent loop, tool calling, and structured summaries — runs on
`zai/GLM-5.2`, whose 256k context window holds the file map and large source
files in one window.

Any other Crusoe-hosted model works too, via `--model`:

```bash
deep-repo-agent . --model nvidia/NVIDIA-Nemotron-3-Super-120B-A12B
```

The full catalog is in the
[Crusoe Managed Inference docs](https://docs.crusoecloud.com/managed-inference/overview).

## Configuration

| Variable | Required | Purpose |
|---|---|---|
| `CRUSOE_API_KEY` | yes | API key from the [Crusoe console](https://console.crusoecloud.com/) |
| `CRUSOE_API_BASE` | no | Override the API base URL (defaults to the canonical endpoint) |

## How it works

1. `loader.py` resolves the source — shallow-clones a git URL into a temp
   directory, or uses a local path directly — and builds a file map, skipping
   binaries and vendored directories.
2. `agent.py` creates a LangGraph ReAct agent (`create_react_agent`) over
   `ChatCrusoe` with three tools scoped to the repo root: `list_files`,
   `read_file`, and `search_code`. The file map is embedded in the system
   prompt so the model starts with a map of the territory.
3. `cli.py` runs the chat loop, rendering tool calls as they happen and answers
   as markdown.

## Development

```bash
git clone https://github.com/acheamponge/deep-repo-agent
cd deep-repo-agent
pip install -e .
```

## License

MIT
