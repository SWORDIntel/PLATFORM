# Repository Guidelines

Contributor notes for the SWORD Coder MoE Router and self-coding agent stack.

## Project Structure & Module Organization
- `src/`: router (`generic_router.py`), codebreaker, `self_coder.py`, `ide_interface.py`, and helpers (`code_tools.py`, `quantization_pipeline.py`, `mcp_router.py`).
- `scripts/`: CLI utilities for benchmarks, quantization, setup, and model URL helpers.
- `config/`: YAML for models, hardware, context, and MCP servers—edit here instead of hardcoding.
- `IntelStack/` and `NUC2.1/`: platform-specific drivers, Rust workspace, and Docker assets; keep changes scoped to the relevant platform.
- Docs: `README.md` for quick start; `SELF_CODING.md` and `GEMINI.md` for workflows and reference.

## Build, Test, and Development Commands
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Router: `python main.py` (use `--host/--port`); MCP smoke test: `python main.py --mcp-test`.
- IDE & self-coding: `python main.py --ide` or `./sword_launcher.sh`; interactive agent: `python main.py --self-code`.
- Codebreaker: `python main.py --codebreaker --payload "<base64_or_hex>" --devices npu,movidius --crypto-bench` (payload defaults to bundled sample).
- Bench/perf: `python scripts/benchmark_router.py`, `python scripts/benchmark_movidius.py`, and `python scripts/run_quantization.py --help` for compression flows.

## Coding Style & Naming Conventions
- Python 3 with PEP8, type hints, dataclasses, and module docstrings; prefer `Path`/`pathlib` and f-strings.
- Naming: `snake_case` for files/functions, `CamelCase` for classes, `SCREAMING_SNAKE_CASE` for constants; align CLI flags with argparse help text.
- Scripts stay thin wrappers around shared logic in `src/`; configuration comes from YAML or environment variables, not embedded secrets or machine paths.

## Testing Guidelines
- Quick checks: `python main.py --mcp-test`, `python main.py --benchmark`, and a short IDE launch to confirm TUI rendering.
- Codebreaker changes: run the default payload and at least one explicit `--devices` set (`all` is valid); note when hardware is unavailable.
- Performance/quantization changes: run `python scripts/benchmark_router.py` and cite `scripts/run_quantization.py` results; new automated tests should live under `tests/` with scenario-based names.

## Commit & Pull Request Guidelines
- Use short, imperative subjects consistent with history; avoid noisy prefixes.
- PRs should state behavior changes, configs touched, commands run, and hardware context (NPU/Movidius/iGPU). Add screenshots or CLI snippets for TUI or benchmark output.
- Link issues for model/hardware/policy changes; keep commits scoped to router, agent, or platform layers without mixing unrelated edits.

## Security & Configuration Tips
- Keep API keys (Anthropic, etc.) in environment variables or a local `.env` kept out of version control.
- Scrub `config/*.yaml` for hostnames/paths before pushing; prefer placeholders and documentation over committing live endpoints.
