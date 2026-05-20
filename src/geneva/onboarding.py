from __future__ import annotations
from pathlib import Path
from typing import Any

from src.memdir.paths import get_auto_mem_path, get_data_dir

ONBOARDING_SYSTEM_PROMPT = """You are Geneva's onboarding interviewer.
Your job is to learn about the user so Geneva can become their personal AI assistant.

Rules:
- Ask ONE section at a time. Wait for the user's response before continuing.
- Be conversational, not bureaucratic.
- If user says "skip" or doesn't answer → note as [not provided] and continue.
- If user is solo → skip deeper team questions.
- After all 6 sections → summarize what you learned and ask for confirmation.
- When user confirms → output the [ONBOARDING_COMPLETE] JSON block.

## Section 1: About You
Ask: What's your name? What do you do in one sentence? What timezone are you in?
What's the single most important thing you're working toward right now?

## Section 2: Work / Business
Ask: What's your business or work called?
What are your main products, services, or revenue streams? (list each briefly)
What tools or apps do you use daily?

## Section 3: Your Team
Ask: Do you work solo or do you have a team?
If team: who are 1-3 key people I should know? (name and role for each)

## Section 4: Priorities & Goals
Ask: What are the 3-5 things most on your mind right now?
Any hard deadlines I should know about?
What does success look like for you in the next 3 months?

## Section 5: How You Work
Ask: How do you like information presented? (bullets, paragraphs, tables, etc.)
Any pet peeves I should avoid? (e.g., no emojis, keep responses short, etc.)
Should I default to Thai or English in our conversations?

## Section 6: What You Want Help With
Ask: What recurring tasks eat the most of your time?
If you could hand one thing off to an AI assistant first, what would it be?

## Output (after user confirms)
Output this exact block with no extra text around it:

[ONBOARDING_COMPLETE]
{"name": "", "role": "", "timezone": "", "one_liner": "", "top_priority": "",
 "work_name": "", "revenue_streams": [], "tools": [],
 "team": [{"name": "", "role": ""}],
 "priorities": [], "goals_3mo": "", "deadlines": [],
 "communication_style": "", "language": "th",
 "pet_peeves": [], "help_wanted": [], "automations": []}
[/ONBOARDING_COMPLETE]

Fill in all fields from the interview. Use empty string "" or empty list [] for skipped fields.
Language field: "th" for Thai, "en" for English.
"""


class OnboardingManager:
    def __init__(
        self,
        memory_root: Path,
        *,
        soul_root: Path | None = None,
        completion_root: Path | None = None,
        legacy_roots: tuple[Path, ...] = (),
    ) -> None:
        self.memory_root = Path(memory_root)
        self.soul_root = Path(soul_root) if soul_root is not None else self.memory_root
        self.completion_root = Path(completion_root) if completion_root is not None else self.soul_root
        self.legacy_roots = tuple(Path(root) for root in legacy_roots)

    def needs_onboarding(self) -> bool:
        for root in (self.memory_root, *self.legacy_roots):
            me_file = root / "me.md"
            if not me_file.exists():
                continue
            try:
                lines = [line for line in me_file.read_text(encoding="utf-8").splitlines() if line.strip()]
            except OSError:
                continue
            if len(lines) >= 10:
                return False
        return True

    def get_system_prompt(self) -> str:
        return ONBOARDING_SYSTEM_PROMPT

    def write_dna_files(self, context: dict[str, Any], *, overwrite: bool = False) -> None:
        self.memory_root.mkdir(parents=True, exist_ok=True)
        self.soul_root.mkdir(parents=True, exist_ok=True)
        self._write_dna_file("me.md", self._build_me_markdown(context), overwrite=overwrite)
        self._write_dna_file("work.md", self._build_work_markdown(context), overwrite=overwrite)
        self._write_dna_file("team.md", self._build_team_markdown(context), overwrite=overwrite)
        self._write_dna_file(
            "current-priorities.md",
            self._build_priorities_markdown(context),
            overwrite=overwrite,
        )
        self._write_dna_file("goals.md", self._build_goals_markdown(context), overwrite=overwrite)
        soul_content = self._build_soul_markdown(context)
        self._write_file(self.soul_root / "soul.md", soul_content, overwrite=overwrite)

        decisions_dir = self.completion_root / "decisions"
        decisions_dir.mkdir(parents=True, exist_ok=True)
        log_file = decisions_dir / "log.md"
        if not log_file.exists():
            from datetime import date

            log_file.write_text(
                f"# Decision Log\n\nCreated: {date.today().isoformat()}\n\n"
                "## Format\n`[YYYY-MM-DD] DECISION: ...`\n`REASONING: ...`\n\n",
                encoding="utf-8",
            )

    def _write_dna_file(self, filename: str, content: str, *, overwrite: bool) -> None:
        self._write_file(self.memory_root / filename, content, overwrite=overwrite)

    def _write_file(self, path: Path, content: str, *, overwrite: bool) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not overwrite:
            return
        path.write_text(content, encoding="utf-8")

    def mark_complete(self) -> None:
        self.completion_root.mkdir(parents=True, exist_ok=True)
        (self.completion_root / ".onboarding_complete").touch(exist_ok=True)

    def _build_me_markdown(self, context: dict[str, Any]) -> str:
        me = context.get("me") if isinstance(context.get("me"), dict) else context
        return (
            "# me\n\n"
            f"name: {self._extract_first(me, 'name')}\n"
            f"role: {self._extract_first(me, 'role')}\n"
            f"timezone: {self._extract_first(me, 'timezone')}\n"
            f"one_liner: {self._extract_first(me, 'one_liner', 'one-liner', 'one line', default='')}\n"
            f"top_priority: {self._extract_first(me, 'top_priority', 'top-priority', 'priority', default='')}\n"
            f"communication_style: {self._extract_first(me, 'communication_style', 'communication', default='')}\n"
        ) + "\n"

    def _build_work_markdown(self, context: dict[str, Any]) -> str:
        work = context.get("work") if isinstance(context.get("work"), dict) else context
        lines = [
            "# work",
            "",
            "## business",
            self._extract_first(work, "business"),
            "",
            "## revenue streams",
        ]
        revenues = self._to_lines(self._pick(context, "work", "revenue_streams", "revenues", "revenue"))
        if revenues:
            lines.extend(f"- {item}" for item in revenues)
        else:
            lines.append("- unknown")
        lines.extend(["", "## tools"])
        tools = self._to_lines(self._pick(context, "work", "tools"))
        if tools:
            lines.extend(f"- {tool}" for tool in tools)
        else:
            lines.append("- unknown")
        return "\n".join(lines) + "\n"

    def _build_team_markdown(self, context: dict[str, Any]) -> str:
        team = self._pick(context, "team", "key_people")
        people = self._to_people(team)
        lines = ["# team", "", "## key people"]
        if people:
            lines.extend(f"- {name} - {role}" for name, role in people)
        else:
            lines.append("- not provided")
        return "\n".join(lines) + "\n"

    def _build_priorities_markdown(self, context: dict[str, Any]) -> str:
        priorities = self._to_items(self._pick(context, "priorities", "current_priorities"))
        lines = ["# current-priorities", ""]
        if not priorities:
            lines.append("- not provided")
            return "\n".join(lines) + "\n"
        for index, priority in enumerate(priorities[:5], start=1):
            if isinstance(priority, dict):
                title = str(priority.get("area") or priority.get("title") or "").strip()
                deadline = str(priority.get("deadline") or "").strip()
                lines.append(f"{index}. {title} {f'({deadline})' if deadline else ''}".strip())
            else:
                lines.append(f"{index}. {str(priority).strip()}")
        return "\n".join(lines) + "\n"

    def _build_goals_markdown(self, context: dict[str, Any]) -> str:
        lines = ["# goals", "", "## 3_month_goals"]
        goals = self._pick(context, "goals")
        milestones = self._pick(context, "milestones")
        goal_lines = self._to_lines(goals)
        if goal_lines:
            lines.extend(f"- {goal}" for goal in goal_lines)
        else:
            lines.append("- not provided")
        lines.extend(["", "## milestones"])
        milestone_lines = self._to_lines(milestones)
        if milestone_lines:
            lines.extend(f"- {milestone}" for milestone in milestone_lines)
        else:
            lines.append("- not provided")
        return "\n".join(lines) + "\n"

    def _build_soul_markdown(self, context: dict[str, Any]) -> str:
        from datetime import date

        name = self._extract_first(context, "name")
        role = self._extract_first(context, "role", default="")
        timezone = self._extract_first(context, "timezone", default="")
        one_liner = self._extract_first(context, "one_liner", "one-liner", default="")
        language = self._extract_first(context, "language", default="th")
        pet_peeves = self._to_lines(context.get("pet_peeves"))
        comm_style = self._extract_first(context, "communication_style", "communication", default="")
        top_priority = self._extract_first(context, "top_priority", "priority", default="")
        goals_3mo = self._extract_first(context, "goals_3mo", "goals", default="")

        lines = [
            "---",
            "version: 1",
            f"updated: {date.today().isoformat()}",
            "---",
            "",
            "# Soul — Geneva's Identity Contract",
            "",
            "## Who I Am",
            f"Name: {name}",
            f"Role: {role}",
            f"Timezone: {timezone}",
            f"One-liner: {one_liner}",
            "",
            "## Current Focus",
            f"Top priority: {top_priority}",
            f"3-month goal: {goals_3mo}",
            "",
            "## Voice — How to Talk to Me",
            f"Language: {'Thai for fast brainstorm; English for formal output' if language == 'th' else 'English'}",
            f"Style: {comm_style}",
        ]
        if pet_peeves:
            lines.extend(["", "## Hard Nos"])
            lines.extend(f"- {p}" for p in pet_peeves)
        lines.append("")
        return "\n".join(lines)

    def _pick(self, context: dict[str, Any], *keys: str) -> Any:
        nested = context.get("work") if isinstance(context.get("work"), dict) else None
        if nested is not None:
            for key in keys:
                if isinstance(nested, dict) and key in nested:
                    return nested[key]
        for key in keys:
            if key in context:
                return context[key]
        return None

    def _extract_first(self, context: dict[str, Any], *keys: str, default: str = "unknown") -> str:
        value = self._pick(context, *keys)
        if isinstance(value, str):
            text = value.strip()
            return text or default
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, dict):
            for key in keys:
                nested = value.get(key)
                if isinstance(nested, str):
                    text = nested.strip()
                    return text or default
        return default

    def _to_lines(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [line.strip() for line in value.splitlines() if line.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()] if str(value).strip() else []

    def _to_items(self, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]

    def _to_people(self, value: Any) -> list[tuple[str, str]]:
        people: list[tuple[str, str]] = []
        for person in self._to_items(value):
            if isinstance(person, dict):
                name = str(person.get("name") or "unknown").strip()
                role = str(person.get("role") or "member").strip()
                people.append((name, role))
            elif isinstance(person, str):
                raw = person.strip()
                if not raw:
                    continue
                if " - " in raw:
                    name, role = raw.split(" - ", 1)
                    people.append((name.strip() or "unknown", role.strip() or "member"))
                else:
                    people.append((raw, "member"))
        return people


def current_memory_root() -> Path:
    return get_data_dir() / "context"


def current_onboarding_manager() -> OnboardingManager:
    data_dir = get_data_dir()
    legacy_roots = (get_auto_mem_path(Path.cwd()), data_dir)
    return OnboardingManager(
        data_dir / "context",
        soul_root=data_dir,
        completion_root=data_dir,
        legacy_roots=legacy_roots,
    )


def manager_from_tmp(tmp_dir: str | Path) -> OnboardingManager:
    return OnboardingManager(Path(tmp_dir))
