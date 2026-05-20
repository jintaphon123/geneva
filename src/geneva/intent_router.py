"""R10.1 -- Semantic Intent Router (rule-based, Thai + English).

classify_intent(message) -> IntentResult
intent can be: create_project | attach_project | add_project_log | add_todo |
               create_skill | update_skill | deep_research | document_workflow |
               computer_use | normal_chat
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


IntentType = str  # one of the 10 intents above

_IntentStr = str

# Thai keyword patterns (substring match, case-sensitive for Thai)
_THAI: dict[_IntentStr, list[str]] = {
    "computer_use": ["ช่วยเปิดเว็บ", "ไปหน้า", "เปิด browser", "เปิดเว็บ", "เปิดแท็บ"],
    "document_workflow": ["ช่วยอ่าน pdf", "สรุปเอกสาร", "อ่านไฟล์", "อ่าน pdf", "อ่านเอกสาร"],
    "deep_research": ["ช่วย research", "หาข้อมูล", "research เรื่อง", "ค้นหาข้อมูล", "วิจัยเรื่อง"],
    "create_skill": ["สร้าง skill", "ทำ skill", "เพิ่ม skill", "build skill", "สร้างสกิล", "ทำสกิล"],
    "update_skill": ["แก้ skill", "ปรับ skill", "อัปเดต skill", "แก้ไข skill", "แก้สกิล"],
    "create_project": ["project ใหม่", "เริ่ม project", "นี่คือ project", "อันนี้คือ project", "สร้าง project"],
    "attach_project": ["เข้า project", "เป็นส่วนหนึ่งของ project", "link project", "ผูก project", "แนบ project"],
    "add_project_log": ["บันทึกว่า", "log ว่า", "จดไว้ว่า", "note ว่า", "บันทึก log"],
    "add_todo": ["อย่าลืม", "ต้องทำ", "todo:", "จำไว้ว่าต้อง", "อย่าลืมต้อง", "ต้องจำ"],
}

# English keyword patterns (regex, case-insensitive)
_EN_RAW: dict[_IntentStr, list[str]] = {
    "computer_use": [
        r"\bopen browser\b",
        r"\bnavigate to\b",
        r"\bgo to website\b",
        r"\bopen (a |the )?tab\b",
        r"\bopen (a |the )?page\b",
    ],
    "document_workflow": [
        r"\bpdf\b",
        r"\bsummarize (the |this )?document\b",
        r"\bread (this |the )?file\b",
        r"\bsummarize (the |this )?file\b",
    ],
    "deep_research": [
        r"\bresearch about\b",
        r"\bfind information about\b",
        r"\blook up\b",
        r"\bfind info about\b",
    ],
    "create_skill": [
        r"\bcreate (a )?skill\b",
        r"\bbuild (a )?skill\b",
        r"\bmake (a )?skill\b",
        r"\badd (a )?skill\b",
    ],
    "update_skill": [r"\bupdate skill\b", r"\bedit skill\b", r"\bmodify skill\b", r"\bchange skill\b"],
    "create_project": [
        r"\bnew project\b",
        r"\bcreate project\b",
        r"\bstart (a )?new project\b",
        r"\bstart project\b",
    ],
    "attach_project": [
        r"\badd (this |the )(chat|session|conversation) to project\b",
        r"\blink (this |the )(chat|session) to project\b",
        r"\bpart of project\b",
        r"\blink to project\b",
    ],
    "add_project_log": [r"\blog that\b", r"\brecord that\b", r"\bnote that\b", r"\bdocument that\b"],
    "add_todo": [r"\bdon'?t forget\b", r"\bneed to\b", r"\btodo:\b", r"\btask:\b", r"\bremember to\b"],
}

# Compile English patterns once
_EN: dict[_IntentStr, list[re.Pattern[str]]] = {
    intent: [re.compile(p, re.IGNORECASE) for p in patterns]
    for intent, patterns in _EN_RAW.items()
}

# Priority order (most specific first to avoid false matches)
_PRIORITY: list[_IntentStr] = [
    "computer_use",
    "document_workflow",
    "deep_research",
    "create_skill",
    "update_skill",
    "create_project",
    "attach_project",
    "add_project_log",
    "add_todo",
]

# Regex patterns for extracting project name
_PROJECT_NAME_PATTERNS: list[str] = [
    r"project\s+(?:เรื่อง|ชื่อ|เกี่ยวกับ|สำหรับ)\s+([\w฀-๿][\w฀-๿\s]{1,49}?)(?:\s*$|\s+(?:ได้เลย|หน่อย|นะ|ครับ|ค่ะ))",
    r"project\s*:\s*(.+?)(?:\s*$|\.)",
    r"project\s+(?:named?|about|for|called)\s+(.+?)(?:\s*$|\.|\s+(?:now|please|ok))",
    r"project\s+([\w฀-๿]{2,30}(?:\s+[\w฀-๿]{2,20})?)",
]
_PROJECT_NAME_STOP = {"new", "a", "the", "ใหม่", "create", "start", "this", "that"}


@dataclass
class IntentResult:
    intent: IntentType
    confidence: float
    params: dict = field(default_factory=dict)


def _extract_project_name(message: str) -> str | None:
    """Extract project name from a create_project message."""
    for pat in _PROJECT_NAME_PATTERNS:
        m = re.search(pat, message, re.IGNORECASE)
        if m:
            name = m.group(1).strip()[:50]
            if name.lower() not in _PROJECT_NAME_STOP:
                return name
    return None


def classify_intent(message: str) -> IntentResult:
    """Classify message intent using keyword rules (Thai + English).

    Returns IntentResult with:
      - intent: matched intent name or "normal_chat"
      - confidence: 0.9 for rule match, 1.0 for normal_chat fallback
      - params: {"project_name": ...} for create_project if name extracted
    """
    lower = message.lower()

    for intent in _PRIORITY:
        # Check Thai keywords
        for kw in _THAI.get(intent, []):
            if kw in message:  # Thai is case-sensitive; use original message
                params: dict = {}
                if intent == "create_project":
                    name = _extract_project_name(message)
                    if name:
                        params["project_name"] = name
                elif intent == "attach_project":
                    name = _extract_project_name(message)
                    if name:
                        params["project_name"] = name
                return IntentResult(intent=intent, confidence=0.9, params=params)

        # Check English patterns
        for pat in _EN.get(intent, []):
            if pat.search(lower):
                params = {}
                if intent == "create_project":
                    name = _extract_project_name(message)
                    if name:
                        params["project_name"] = name
                elif intent == "attach_project":
                    name = _extract_project_name(message)
                    if name:
                        params["project_name"] = name
                return IntentResult(intent=intent, confidence=0.9, params=params)

    return IntentResult(intent="normal_chat", confidence=1.0)
