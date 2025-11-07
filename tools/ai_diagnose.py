#!/usr/bin/env python3
"""AI-assisted diagnostics workflow runner.

This utility prepares structured context (logs, code snippets, specification
extracts) and orchestrates a ReAct-style dialogue with an LLM to produce a
root-cause analysis report.  The resulting artefacts are persisted under
``reports/ai_diagnostics/`` so the CI pipeline can upload them for further
review.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import importlib
import importlib.util
import json
import platform
from pathlib import Path
from typing import Any, Callable, Optional, Protocol
from collections.abc import Iterable, Sequence

from src.diagnostics.logger_factory import configure_logging, get_logger


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENCODING = "utf-8"
MAX_SNIPPET_BYTES = 12_000
SYSTEM_PROMPT_PATH = (
    ROOT / "reports" / "ai_diagnostics" / "prompts" / "system_prompt.md"
)
HISTORY_DIR = ROOT / "reports" / "ai_diagnostics" / "history"
LATEST_REPORT = ROOT / "reports" / "ai_diagnostics" / "latest_report.md"
LATEST_PAYLOAD = ROOT / "reports" / "ai_diagnostics" / "latest_payload.json"

SYSTEM_PROMPT = """You are PneumoStabSim Professional's diagnostics co-pilot.
Follow the renovation programme guidelines, respect safety constraints, and
produce actionable debugging plans.  Summaries must reference collected data by
filename and line numbers whenever possible.  Prefer hypotheses ranked by
likelihood, supported by evidence, and counter-examples.  Recommend follow-up
experiments and test additions that validate the fix."""

DEFAULT_LOG_PATTERNS: tuple[str, ...] = (
    "reports/**/*.log",
    "reports/**/*.json",
    "logs/**/*.log",
)
DEFAULT_CODE_PATTERNS: tuple[str, ...] = (
    "src/**/*.py",
    "src/**/*.qml",
)
DEFAULT_SPEC_PATTERNS: tuple[str, ...] = (
    "docs/**/*.md",
    "docs/**/*.rst",
)


@dataclasses.dataclass(slots=True)
class Snippet:
    """A bounded text excerpt collected for the investigation."""

    path: Path
    category: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path.relative_to(ROOT)),
            "category": self.category,
            "content": self.content,
        }


class InputCollector:
    """Collect bounded snippets from the repository."""

    def __init__(
        self,
        *,
        base_dir: Path,
        max_bytes: int = MAX_SNIPPET_BYTES,
        encoding: str = DEFAULT_ENCODING,
    ) -> None:
        self._base_dir = base_dir
        self._max_bytes = max_bytes
        self._encoding = encoding
        self._log = get_logger("tools.ai_diagnose.collector")

    def collect(
        self, patterns: Sequence[str], category: str, limit: int
    ) -> list[Snippet]:
        seen: set[Path] = set()
        snippets: list[Snippet] = []
        for pattern in patterns:
            for path in sorted(self._base_dir.glob(pattern)):
                if not path.is_file():
                    continue
                if path in seen:
                    continue
                seen.add(path)
                snippets.append(self._build_snippet(path, category))
                if len(snippets) >= limit:
                    return snippets
        return snippets

    def _build_snippet(self, path: Path, category: str) -> Snippet:
        raw = path.read_text(encoding=self._encoding, errors="replace")
        if len(raw) > self._max_bytes:
            head = raw[: self._max_bytes - 2000]
            tail = raw[-2000:]
            raw = f"{head}\n…\n{tail}"
        self._log.debug(
            "collected-snippet",
            category=category,
            path=str(path.relative_to(self._base_dir)),
            size=len(raw),
        )
        return Snippet(path=path, category=category, content=raw)


@dataclasses.dataclass(slots=True)
class Tool:
    """Description of a callable tool available to the LLM."""

    name: str
    description: str
    parameters_json_schema: dict[str, Any]
    runner: Callable[[dict[str, Any]], str]

    def to_openai(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_json_schema,
            },
        }


@dataclasses.dataclass(slots=True)
class ToolInvocation:
    """Record of a tool call issued by the model."""

    name: str
    arguments: dict[str, Any]
    output: str

    def to_report_block(self) -> str:
        return (
            f"### Tool: {self.name}\n"
            f"Arguments::\n\n```json\n{json.dumps(self.arguments, indent=2, sort_keys=True)}\n```\n\n"
            f"Output::\n\n````text\n{self.output}\n````\n"
        )


@dataclasses.dataclass(slots=True)
class AgentMessage:
    """A single message exchanged during the ReAct loop."""

    role: str
    content: str


@dataclasses.dataclass(slots=True)
class AgentRun:
    """Completed agent execution."""

    final_message: str
    messages: list[AgentMessage]
    tool_invocations: list[ToolInvocation]


class ChatModel(Protocol):
    """Protocol expected from chat completion providers."""

    def generate(
        self,
        messages: Sequence[dict[str, str]],
        *,
        tools: Sequence[dict[str, Any]] = (),
    ) -> dict[str, Any]:
        """Return a dictionary describing the model response."""


class OpenAIChatModel:
    """Adapter around the ``openai`` client implementing :class:`ChatModel`."""

    def __init__(self, model: str) -> None:
        spec = importlib.util.find_spec("openai")
        if spec is None:
            raise RuntimeError(
                "openai package is not installed; install it or provide a custom ChatModel"
            )
        module = importlib.import_module("openai")
        client_class = getattr(module, "OpenAI", None)
        if client_class is None:
            raise RuntimeError(
                "openai.OpenAI client is unavailable; upgrade the openai package"
            )
        self._client = client_class()
        self._model = model

    def generate(
        self,
        messages: Sequence[dict[str, str]],
        *,
        tools: Sequence[dict[str, Any]] = (),
    ) -> dict[str, Any]:
        response = self._client.responses.create(
            model=self._model,
            input=[
                {"role": item["role"], "content": item["content"]} for item in messages
            ],
            tools=list(tools),
        )
        return response.model_dump()


class ReActAgent:
    """State machine implementing a lightweight ReAct loop."""

    def __init__(
        self,
        *,
        chat_model: ChatModel,
        tools: Sequence[Tool],
        max_turns: int,
    ) -> None:
        self._chat_model = chat_model
        self._tool_map = {tool.name: tool for tool in tools}
        self._tools = tools
        self._max_turns = max_turns
        self._log = get_logger("tools.ai_diagnose.agent")

    def run(self, prompt: list[dict[str, str]]) -> AgentRun:
        transcript: list[AgentMessage] = []
        invocations: list[ToolInvocation] = []
        messages = list(prompt)
        for turn in range(1, self._max_turns + 1):
            self._log.debug("agent-turn-start", turn=turn)
            payload = self._chat_model.generate(
                messages, tools=[tool.to_openai() for tool in self._tools]
            )
            result = payload.get("output", {})
            if isinstance(result, list) and result:
                top = result[0]
                if top.get("type") == "message":
                    content = top.get("content", "")
                    transcript.append(AgentMessage(role="assistant", content=content))
                    messages.append({"role": "assistant", "content": content})
                    return AgentRun(
                        final_message=content,
                        messages=transcript,
                        tool_invocations=invocations,
                    )
                if top.get("type") == "tool_call":
                    name = top.get("name")
                    arguments = json.loads(top.get("arguments", "{}"))
                    tool = self._tool_map.get(name)
                    if tool is None:
                        raise RuntimeError(f"Model requested unknown tool: {name}")
                    output = tool.runner(arguments)
                    invocations.append(
                        ToolInvocation(name=name, arguments=arguments, output=output)
                    )
                    messages.append(
                        {
                            "role": "assistant",
                            "content": json.dumps(
                                {"tool": name, "arguments": arguments}
                            ),
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "content": output,
                            "name": name,
                        }
                    )
                    transcript.append(
                        AgentMessage(role="assistant", content=f"TOOL_CALL {name}")
                    )
                    transcript.append(AgentMessage(role="tool", content=output))
                    continue
            raise RuntimeError(
                "Model response did not contain a supported message format"
            )
        raise RuntimeError(
            "Agent exceeded maximum number of turns without a conclusion"
        )


def build_default_tools(snippets: Sequence[Snippet]) -> list[Tool]:
    """Expose repository snippets to the LLM through searchable tools."""

    index = {snippet.path.as_posix(): snippet for snippet in snippets}

    def search_tool(arguments: dict[str, Any]) -> str:
        query = arguments.get("path")
        if not query:
            return "Missing 'path' argument"
        resolved = ROOT / query
        snippet = index.get(resolved.as_posix()) or index.get(query)
        if snippet is None:
            return f"No cached snippet for {query}"
        return snippet.content

    return [
        Tool(
            name="read_snippet",
            description="Return a cached snippet previously collected from the repository",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file relative to the repository root",
                    }
                },
                "required": ["path"],
            },
            runner=search_tool,
        )
    ]


def ensure_system_prompt() -> None:
    """Persist the default system prompt so teams can iterate on it."""

    SYSTEM_PROMPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SYSTEM_PROMPT_PATH.exists():
        SYSTEM_PROMPT_PATH.write_text(SYSTEM_PROMPT + "\n", encoding=DEFAULT_ENCODING)


def persist_payload(issue: str, snippets: Sequence[Snippet]) -> None:
    payload = {
        "issue": issue,
        "generated_at": _dt.datetime.utcnow().isoformat() + "Z",
        "snippets": [snippet.to_dict() for snippet in snippets],
    }
    LATEST_PAYLOAD.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding=DEFAULT_ENCODING
    )


def build_report(
    *,
    issue: str,
    snippets: Sequence[Snippet],
    agent_run: AgentRun | None,
    platform_name: str,
) -> str:
    timestamp = _dt.datetime.utcnow().isoformat() + "Z"
    lines: list[str] = [
        "# AI Diagnostics Report",
        "",
        f"- Generated at: {timestamp}",
        f"- Host platform: {platform_name}",
        f"- Issue summary: {issue or 'n/a'}",
        "",
        "## Collected Context",
    ]
    for snippet in snippets:
        lines.append(f"### {snippet.category}: {snippet.path.relative_to(ROOT)}")
        lines.append("````text")
        lines.append(snippet.content)
        lines.append("````")
        lines.append("")
    if agent_run is None:
        lines.extend(
            [
                "## Model Execution",
                "LLM execution was skipped (no chat model configured).",
            ]
        )
    else:
        lines.extend(
            [
                "## Model Execution",
                "",
                "### Final Response",
                agent_run.final_message,
                "",
            ]
        )
        if agent_run.tool_invocations:
            lines.append("## Tool Invocations")
            for invocation in agent_run.tool_invocations:
                lines.append(invocation.to_report_block())
        if agent_run.messages:
            lines.append("## Conversation Transcript")
            for message in agent_run.messages:
                lines.append(f"### {message.role.title()}")
                lines.append(message.content)
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def save_report(content: str) -> Path:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    destination = HISTORY_DIR / f"report_{timestamp}.md"
    destination.write_text(content, encoding=DEFAULT_ENCODING)
    LATEST_REPORT.write_text(content, encoding=DEFAULT_ENCODING)
    return destination


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate AI-assisted diagnostics report"
    )
    parser.add_argument(
        "issue",
        nargs="?",
        default="",
        help="Short description of the incident under investigation",
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1",
        help="LLM model identifier for the OpenAI Responses API",
    )
    parser.add_argument(
        "--max-turns", type=int, default=8, help="Maximum number of ReAct iterations"
    )
    parser.add_argument(
        "--log-pattern", action="append", default=list(DEFAULT_LOG_PATTERNS)
    )
    parser.add_argument(
        "--code-pattern", action="append", default=list(DEFAULT_CODE_PATTERNS)
    )
    parser.add_argument(
        "--spec-pattern", action="append", default=list(DEFAULT_SPEC_PATTERNS)
    )
    parser.add_argument(
        "--per-category-limit",
        type=int,
        default=4,
        help="Maximum number of files per category",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Collect artefacts but skip model execution",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    ensure_system_prompt()
    configure_logging()
    log = get_logger("tools.ai_diagnose")
    platform_name = platform.system()
    log.info("environment", platform=platform_name)

    args = parse_args(argv)
    collector = InputCollector(base_dir=ROOT)
    snippets: list[Snippet] = []
    snippets.extend(collector.collect(args.log_pattern, "log", args.per_category_limit))
    snippets.extend(
        collector.collect(args.code_pattern, "code", args.per_category_limit)
    )
    snippets.extend(
        collector.collect(args.spec_pattern, "spec", args.per_category_limit)
    )
    persist_payload(args.issue, snippets)

    agent_run: AgentRun | None = None
    if not args.skip_llm:
        try:
            chat_model = OpenAIChatModel(args.model)
        except RuntimeError as error:
            log.warning("chat-model-unavailable", reason=str(error))
        else:
            context_messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_PATH.read_text(encoding=DEFAULT_ENCODING),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "issue": args.issue,
                            "platform": platform_name,
                            "snippets": [snippet.to_dict() for snippet in snippets],
                        },
                        indent=2,
                        ensure_ascii=False,
                    ),
                },
            ]
            tools = build_default_tools(snippets)
            agent = ReActAgent(
                chat_model=chat_model, tools=tools, max_turns=args.max_turns
            )
            try:
                agent_run = agent.run(context_messages)
            except RuntimeError as error:
                log.error("agent-failure", reason=str(error))
    report = build_report(
        issue=args.issue,
        snippets=snippets,
        agent_run=agent_run,
        platform_name=platform_name,
    )
    destination = save_report(report)
    log.info("report-generated", destination=str(destination.relative_to(ROOT)))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
