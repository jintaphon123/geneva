from __future__ import annotations

from pathlib import Path

from .loader import load_tools_from_dir
from .profiles import filtered_tools, resolve_tool_profile
from .registry import ToolRegistry
from .tools import (
    AskUserQuestionTool,
    BashTool,
    BriefTool,
    WrapUpTool,
    ConfigTool,
    ComputerUseTool,
    CronCreateTool,
    CronDeleteTool,
    CronListTool,
    DocumentGenerateTool,
    DocumentParseTool,
    DocumentVerifyTool,
    EnterPlanModeTool,
    EnterWorktreeTool,
    ExitPlanModeTool,
    ExitWorktreeTool,
    FileEditTool,
    FileReadTool,
    FileWriteTool,
    GlobTool,
    GrepTool,
    ListMcpResourcesTool,
    MCPTool,
    McpAuthTool,
    NotebookEditTool,
    PowerShellTool,
    PluginListTool,
    ReadMcpResourceTool,
    REPLTool,
    RemoteTriggerTool,
    SendMessageTool,
    SendUserMessageTool,
    SkillSaveTool,
    SkillTool,
    SleepTool,
    StructuredOutputTool,
    TeamCreateTool,
    TeamDeleteTool,
    TaskCreateTool,
    TaskGetTool,
    TaskListTool,
    TaskOutputTool,
    TaskStopTool,
    TaskUpdateTool,
    TestingPermissionTool,
    TodoWriteTool,
    WebFetchTool,
    WebSearchTool,
)
from .tools.agent import AgentTool
from .tools.tool_search import ToolSearchTool


def build_default_registry(
    *,
    include_user_tools: bool | None = None,
    profile: str | None = None,
) -> ToolRegistry:
    tool_profile = resolve_tool_profile(profile or "power_harness")
    bundled_tools = [
        SendUserMessageTool(),
        WebFetchTool(),
        WebSearchTool(),
        DocumentParseTool(),
        DocumentVerifyTool(),
        PluginListTool(),
        SleepTool(),
        FileReadTool(),
        GlobTool(),
        GrepTool(),
        BashTool(),
        FileEditTool(),
        FileWriteTool(),
        DocumentGenerateTool(),
        ComputerUseTool(),
        NotebookEditTool(),
        PowerShellTool(),
        REPLTool(),
        TestingPermissionTool(),
        EnterPlanModeTool(),
        ExitPlanModeTool(),
        EnterWorktreeTool(),
        ExitWorktreeTool(),
        TaskStopTool(),
        ConfigTool(),
        MCPTool(),
        McpAuthTool(),
        ListMcpResourcesTool(),
        ReadMcpResourceTool(),
        SkillTool(),
        SkillSaveTool(),
        BriefTool(),
        WrapUpTool(),
        AskUserQuestionTool(),
        TodoWriteTool(),
        TaskCreateTool(),
        TaskGetTool(),
        TaskListTool(),
        TaskUpdateTool(),
        TaskOutputTool(),
        TeamCreateTool(),
        TeamDeleteTool(),
        CronCreateTool(),
        CronListTool(),
        CronDeleteTool(),
        SendMessageTool(),
        StructuredOutputTool(),
        RemoteTriggerTool(),
    ]
    registry = ToolRegistry(tools=filtered_tools(bundled_tools, tool_profile))
    if tool_profile.allowed_tools is None or "Agent" in tool_profile.allowed_tools:
        registry.register(AgentTool(registry))
    if tool_profile.allowed_tools is None or "ToolSearch" in tool_profile.allowed_tools:
        registry.register(ToolSearchTool(registry))

    should_include_user_tools = tool_profile.include_user_tools if include_user_tools is None else include_user_tools
    if should_include_user_tools:
        user_dir = Path.home() / ".geneva" / "tools"
        for tool in load_tools_from_dir(user_dir):
            registry.register(tool)

    return registry
