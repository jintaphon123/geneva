"""R10.2 -- Intent router accuracy eval (Thai + English).

No live API -- tests keyword classifier only.
Target: >=90% accuracy on 40 labeled phrases (20 Thai + 20 English).
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.benchmarks.runner import BenchmarkCase, BenchmarkRunner


# 20 Thai phrases with correct labels
THAI_CASES: list[tuple[str, str]] = [
    ("อันนี้คือ project ใหม่เรื่อง Geneva", "create_project"),
    ("เริ่ม project เรื่อง AI Router ได้เลย", "create_project"),
    ("สร้าง project ชื่อ Second Brain", "create_project"),
    ("เอาแชตนี้เข้า project Geneva หน่อย", "attach_project"),
    ("นี่เป็นส่วนหนึ่งของ project ที่ทำอยู่", "attach_project"),
    ("บันทึกว่าวันนี้ทำ API design เสร็จแล้ว", "add_project_log"),
    ("log ว่าตัดสินใจใช้ SQLite แล้ว", "add_project_log"),
    ("จดไว้ว่า architecture เปลี่ยนเป็น microservices แล้ว", "add_project_log"),
    ("อย่าลืม deploy version ใหม่ด้วย", "add_todo"),
    ("ต้องทำ unit test ก่อน merge", "add_todo"),
    ("สร้าง skill สำหรับ deep research", "create_skill"),
    ("ทำ skill ให้ช่วย summarize ได้", "create_skill"),
    ("แก้ skill consult ให้ดีขึ้น", "update_skill"),
    ("ปรับ skill นั้นให้รองรับ Thai ด้วย", "update_skill"),
    ("ช่วย research เรื่อง vector database", "deep_research"),
    ("หาข้อมูล Claude API ให้หน่อย", "deep_research"),
    ("ช่วยอ่าน pdf นี้และสรุปให้", "document_workflow"),
    ("สรุปเอกสาร proposal ที่แนบมา", "document_workflow"),
    ("ช่วยเปิดเว็บ GitHub แล้วหา repo", "computer_use"),
    ("ไปหน้า settings ของ app ให้หน่อย", "computer_use"),
]

# 20 English phrases with correct labels
EN_CASES: list[tuple[str, str]] = [
    ("new project: Geneva Memory Engine", "create_project"),
    ("let's start a new project about the intent router", "create_project"),
    ("create project for the rental automation system", "create_project"),
    ("link this chat to project Geneva", "attach_project"),
    ("this is part of project Second Brain", "attach_project"),
    ("log that we finished the artifact store today", "add_project_log"),
    ("record that we decided to use SQLite for storage", "add_project_log"),
    ("don't forget to add unit tests for the router", "add_todo"),
    ("todo: write documentation for the API endpoints", "add_todo"),
    ("need to implement the skill autopilot before shipping", "add_todo"),
    ("create a skill for summarizing research papers", "create_skill"),
    ("build a skill to help with code reviews", "create_skill"),
    ("update skill consult to handle edge cases better", "update_skill"),
    ("edit skill researcher to use better prompts", "update_skill"),
    ("research about the latest vector database options", "deep_research"),
    ("find information about Claude API pricing", "deep_research"),
    ("read this pdf and give me a summary", "document_workflow"),
    ("summarize the document attached here", "document_workflow"),
    ("open browser and go to GitHub", "computer_use"),
    ("navigate to the settings page of the application", "computer_use"),
]

ALL_CASES = THAI_CASES + EN_CASES


class TestIntentRouterEval(unittest.TestCase):
    """R10.2: 40-phrase intent classification accuracy >=90%."""

    def test_accuracy_geq_90_on_40_phrases(self) -> None:
        from src.geneva.intent_router import classify_intent

        correct = 0
        wrong: list[str] = []
        for phrase, expected in ALL_CASES:
            actual = classify_intent(phrase).intent
            if actual == expected:
                correct += 1
            else:
                wrong.append(f"  '{phrase[:60]}' expected={expected} got={actual}")

        accuracy = correct / len(ALL_CASES)
        runner = BenchmarkRunner("intent-router", threshold=0.9)
        cases = [
            BenchmarkCase(
                id=f"c{i}",
                prompt=p,
                score_fn=BenchmarkRunner.exact_match_scorer(e),
            )
            for i, (p, e) in enumerate(ALL_CASES)
        ]
        outputs = [classify_intent(p).intent for p, _ in ALL_CASES]
        report = runner.run(cases, outputs)
        with tempfile.TemporaryDirectory() as tmp:
            report.save(Path(tmp))

        self.assertGreaterEqual(
            accuracy,
            0.90,
            f"Accuracy {accuracy:.2f} ({correct}/{len(ALL_CASES)}) < 0.90\n" + "\n".join(wrong),
        )

    def test_thai_accuracy_geq_90(self) -> None:
        from src.geneva.intent_router import classify_intent

        correct = sum(1 for p, e in THAI_CASES if classify_intent(p).intent == e)
        self.assertGreaterEqual(
            correct / len(THAI_CASES),
            0.90,
            f"Thai accuracy {correct}/{len(THAI_CASES)} < 90%",
        )

    def test_english_accuracy_geq_90(self) -> None:
        from src.geneva.intent_router import classify_intent

        correct = sum(1 for p, e in EN_CASES if classify_intent(p).intent == e)
        self.assertGreaterEqual(
            correct / len(EN_CASES),
            0.90,
            f"English accuracy {correct}/{len(EN_CASES)} < 90%",
        )

    def test_normal_chat_fallback(self) -> None:
        from src.geneva.intent_router import IntentResult, classify_intent

        result = classify_intent("what's 2 + 2?")
        self.assertEqual(result.intent, "normal_chat")
        result2 = classify_intent("สวัสดีครับ เป็นยังไงบ้าง")
        self.assertEqual(result2.intent, "normal_chat")

    def test_confidence_rule_match(self) -> None:
        from src.geneva.intent_router import classify_intent

        result = classify_intent("create project for testing")
        self.assertEqual(result.confidence, 0.9)

    def test_confidence_normal_chat(self) -> None:
        from src.geneva.intent_router import classify_intent

        result = classify_intent("tell me a joke")
        self.assertEqual(result.intent, "normal_chat")
        self.assertEqual(result.confidence, 1.0)

    def test_extract_project_name_thai(self) -> None:
        from src.geneva.intent_router import classify_intent

        result = classify_intent("อันนี้คือ project ใหม่เรื่อง Geneva Runtime")
        self.assertEqual(result.intent, "create_project")
        self.assertIn("project_name", result.params)

    def test_extract_project_name_english(self) -> None:
        from src.geneva.intent_router import classify_intent

        result = classify_intent("new project: Second Brain")
        self.assertEqual(result.intent, "create_project")
        self.assertIn("project_name", result.params)
        self.assertIn("Second Brain", result.params["project_name"])

    def test_intent_result_params_default_empty(self) -> None:
        from src.geneva.intent_router import classify_intent

        result = classify_intent("don't forget to write tests")
        self.assertEqual(result.intent, "add_todo")
        # add_todo has no special params extraction
        self.assertIsInstance(result.params, dict)
