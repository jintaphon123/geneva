from __future__ import annotations

import re as _re
from dataclasses import dataclass
from typing import Iterable, Literal


ToolCategory = Literal["read", "write", "destructive"]


@dataclass(frozen=True)
class ToolPermissionEntry:
    tool_name: str
    category: ToolCategory
    path_scope: bool
    approval_required: bool
    network_allowed: bool
    secret_risk: bool


WEB_SAFE_TOOLS = frozenset(
    {
        "SendUserMessage",
        "WebFetch",
        "WebSearch",
        "DocumentParse",
        "DocumentVerify",
        "PluginList",
        "Sleep",
        "ListMcpResourcesTool",
        "ReadMcpResourceTool",
        "Skill",
        "BriefPreview",
        "TodoWrite",
        "TaskCreate",
        "TaskGet",
        "TaskList",
        "TaskUpdate",
        "TaskOutput",
        "StructuredOutput",
        "SkillSave",
        "ToolSearch",
    }
)

RESEARCH_TOOLS = frozenset(
    {
        "SendUserMessage",
        "WebFetch",
        "WebSearch",
        "DocumentParse",
        "DocumentVerify",
        "PluginList",
        "Sleep",
        "ListMcpResourcesTool",
        "ReadMcpResourceTool",
        "Skill",
        "BriefPreview",
        "StructuredOutput",
        "ToolSearch",
    }
)

DEVELOPER_TOOLS = frozenset(
    {
        *WEB_SAFE_TOOLS,
        "Config",
        "Read",
        "Glob",
        "Grep",
        "LSP",
        "Bash",
        "Edit",
        "Write",
        "DocumentGenerate",
        "ComputerUse",
        "EnterPlanMode",
        "ExitPlanMode",
        "EnterWorktree",
        "ExitWorktree",
        "MCP",
        "McpAuthTool",
        "TeamCreate",
        "TeamDelete",
        "CronCreate",
        "CronList",
        "CronDelete",
        "SendMessage",
        "TaskStop",
        "Agent",
    }
)


@dataclass(frozen=True)
class ToolProfile:
    name: str
    description: str
    allowed_tools: frozenset[str] | None
    include_user_tools: bool


TOOL_PROFILES: dict[str, ToolProfile] = {
    "web_safe": ToolProfile(
        name="web_safe",
        description="Default web chat profile. Allows user-facing research, memory, task, and skill tools without local automation side effects.",
        allowed_tools=WEB_SAFE_TOOLS,
        include_user_tools=False,
    ),
    "research": ToolProfile(
        name="research",
        description="External/source-gathering profile for research turns. Excludes mutation-heavy task and automation tools.",
        allowed_tools=RESEARCH_TOOLS,
        include_user_tools=False,
    ),
    "developer": ToolProfile(
        name="developer",
        description="Trusted local development profile with agent/team/MCP controls, but no arbitrary user tool loading.",
        allowed_tools=DEVELOPER_TOOLS,
        include_user_tools=False,
    ),
    "power_harness": ToolProfile(
        name="power_harness",
        description="Full internal harness profile. Includes all bundled tools and user-installed tools.",
        allowed_tools=None,
        include_user_tools=True,
    ),
}


TOOL_PERMISSION_MANIFEST: dict[str, ToolPermissionEntry] = {
    "Bash":            ToolPermissionEntry("Bash",            "destructive", True,  True,  True,  False),
    "Edit":            ToolPermissionEntry("Edit",            "write",       True,  False, False, False),
    "Write":           ToolPermissionEntry("Write",           "write",       True,  False, False, False),
    "Read":            ToolPermissionEntry("Read",            "read",        True,  False, False, False),
    "Glob":            ToolPermissionEntry("Glob",            "read",        True,  False, False, False),
    "Grep":            ToolPermissionEntry("Grep",            "read",        True,  False, False, False),
    "WebFetch":        ToolPermissionEntry("WebFetch",        "read",        False, False, True,  False),
    "WebSearch":       ToolPermissionEntry("WebSearch",       "read",        False, False, True,  False),
    "DocumentParse":   ToolPermissionEntry("DocumentParse",   "read",        True,  False, False, False),
    "DocumentVerify":  ToolPermissionEntry("DocumentVerify",  "read",        True,  False, False, False),
    "DocumentGenerate": ToolPermissionEntry("DocumentGenerate", "write",     True,  True,  False, False),
    "ComputerUse":     ToolPermissionEntry("ComputerUse",     "write",       False, True,  True,  True),
    "PluginList":      ToolPermissionEntry("PluginList",      "read",        False, False, False, False),
    "Config":          ToolPermissionEntry("Config",          "write",       False, False, False, True),
    "SkillSave":       ToolPermissionEntry("SkillSave",       "write",       True,  False, False, False),
    "SendUserMessage": ToolPermissionEntry("SendUserMessage", "write",       False, False, False, False),
    "WrapUp":          ToolPermissionEntry("WrapUp",          "write",       False, False, False, False),
    "TodoWrite":       ToolPermissionEntry("TodoWrite",       "write",       False, False, False, False),
    "Sleep":           ToolPermissionEntry("Sleep",           "read",        False, False, False, False),
    "ListMcpResourcesTool": ToolPermissionEntry("ListMcpResourcesTool", "read",  False, False, True,  False),
    "ReadMcpResourceTool":  ToolPermissionEntry("ReadMcpResourceTool",  "read",  False, False, True,  False),
    "Skill":                ToolPermissionEntry("Skill",                "read",  False, False, False, False),
    "BriefPreview":         ToolPermissionEntry("BriefPreview",         "read",  False, False, False, False),
    "TaskCreate":           ToolPermissionEntry("TaskCreate",           "write", False, False, False, False),
    "TaskGet":              ToolPermissionEntry("TaskGet",              "read",  False, False, False, False),
    "TaskList":             ToolPermissionEntry("TaskList",             "read",  False, False, False, False),
    "TaskUpdate":           ToolPermissionEntry("TaskUpdate",           "write", False, False, False, False),
    "TaskOutput":           ToolPermissionEntry("TaskOutput",           "read",  False, False, False, False),
    "StructuredOutput":     ToolPermissionEntry("StructuredOutput",     "write", False, False, False, False),
    "ToolSearch":           ToolPermissionEntry("ToolSearch",           "read",  False, False, False, False),
    "MCP":                  ToolPermissionEntry("MCP",                  "read",  False, False, True,  False),
    "ComputerUseScreenshot":ToolPermissionEntry("ComputerUseScreenshot","read",  False, False, False, False),
    "BigSearch":            ToolPermissionEntry("BigSearch",            "read",  False, False, False, False),
    "SlowTool":             ToolPermissionEntry("SlowTool",             "read",  False, False, False, False),
    "HelloWorld":           ToolPermissionEntry("HelloWorld",           "read",  False, False, False, False),
}

_DANGEROUS_PATTERNS: list = [
    _re.compile(r"\bsudo\b", _re.IGNORECASE),
    _re.compile(r"\bshutdown\b", _re.IGNORECASE),
    _re.compile(r"\breboot\b", _re.IGNORECASE),
    _re.compile(r"\bmkfs\b", _re.IGNORECASE),
    _re.compile(r"\bdd\b\s+if=", _re.IGNORECASE),
    _re.compile(r"\brm\b.*\s+-rf\s+/\s*$", _re.IGNORECASE),
    _re.compile(r"\brm\b.*\s+-rf\s+/\s+"),
    _re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", _re.IGNORECASE),
]


def get_manifest_entry(tool_name: str) -> ToolPermissionEntry | None:
    return TOOL_PERMISSION_MANIFEST.get(tool_name)


def is_dangerous_command(command: str) -> bool:
    return any(pat.search(command) for pat in _DANGEROUS_PATTERNS)


def resolve_tool_profile(name: str | None) -> ToolProfile:
    key = (name or "web_safe").strip().lower().replace("-", "_")
    return TOOL_PROFILES.get(key, TOOL_PROFILES["web_safe"])


def profile_allows(profile: ToolProfile, tool_name: str) -> bool:
    return profile.allowed_tools is None or tool_name in profile.allowed_tools


def profile_catalog() -> list[dict[str, object]]:
    return [
        {
            "name": profile.name,
            "description": profile.description,
            "tool_count": None if profile.allowed_tools is None else len(profile.allowed_tools),
            "include_user_tools": profile.include_user_tools,
        }
        for profile in TOOL_PROFILES.values()
    ]


def filtered_tools(tools: Iterable[object], profile: ToolProfile) -> list[object]:
    selected = []
    for tool in tools:
        spec = tool.spec()  # type: ignore[attr-defined]
        if profile_allows(profile, spec.name):
            selected.append(tool)
    return selected
