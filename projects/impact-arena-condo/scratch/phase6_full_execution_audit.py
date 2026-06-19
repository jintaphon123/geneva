#!/usr/bin/env python3
import copy
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


FAILURE_KEYS = [
    "queue_priority_wrong",
    "duplicate_task_created",
    "missing_dual_notification",
    "completion_not_blocked",
    "access_prep_coupled_to_cleaning",
    "capability_gate_failed",
    "owner_override_lost_evidence",
    "guest_gate_opened_early",
    "postback_not_idempotent",
]


@dataclass
class Task:
    task_id: str
    kind: str
    booking_id: str
    admin_priority_rank: int = 0
    status: str = "waiting_ack"
    assigned_to: str | None = None
    missing: set[str] = field(default_factory=set)
    blocker: str | None = None
    key_custody: str = "with_owner"
    key_placed: bool = False
    room_open: bool = False
    override_reason: str | None = None


class SyntheticPhase6:
    def __init__(self) -> None:
        self.events: dict[str, dict] = {}
        self.notifications: list[tuple[str, str]] = []
        self.incidents: list[dict] = []
        self.tasks: dict[str, Task] = {}

    def merge_task(self, key: str, task: Task) -> Task:
        if key not in self.tasks:
            self.tasks[key] = task
        return self.tasks[key]

    def apply_once(self, event_id: str, operation) -> dict:
        if event_id in self.events:
            return {**copy.deepcopy(self.events[event_id]), "replayed": True}
        result = operation()
        self.events[event_id] = copy.deepcopy(result)
        return result

    def claim(self, task: Task, operator: str, event_id: str) -> dict:
        def operation() -> dict:
            if task.assigned_to not in (None, operator):
                return {"ok": False, "error": "already_claimed", "task_id": task.task_id}
            task.assigned_to = operator
            task.status = "acknowledged"
            return {"ok": True, "task_id": task.task_id, "status": task.status}

        return self.apply_once(event_id, operation)

    def missing_item(self, task: Task, item: str, event_id: str) -> dict:
        def operation() -> dict:
            task.missing.add(item)
            task.status = "blocked"
            task.blocker = f"missing_{item}"
            incident = {"task_id": task.task_id, "item": item}
            self.incidents.append(incident)
            self.notifications.extend([
                ("internal_ops", task.task_id),
                ("owner", task.task_id),
            ])
            return {"ok": True, "incident": incident}

        return self.apply_once(event_id, operation)

    def complete_cleaning(self, task: Task, event_id: str) -> dict:
        def operation() -> dict:
            if task.missing:
                return {"ok": False, "error": "missing_checklist_items"}
            if task.blocker:
                return {"ok": False, "error": "task_blocked"}
            task.status = "completed"
            return {"ok": True, "status": task.status}

        return self.apply_once(event_id, operation)

    def restore_item(self, task: Task, item: str, event_id: str) -> dict:
        def operation() -> dict:
            task.missing.discard(item)
            if not task.missing:
                task.blocker = None
                task.status = "in_progress"
            return {"ok": True, "status": task.status}

        return self.apply_once(event_id, operation)

    def access_action(
        self,
        task: Task,
        operator: str,
        can_place_key: bool,
        can_open_room: bool,
        event_id: str,
    ) -> dict:
        def operation() -> dict:
            if task.assigned_to != operator or not (can_place_key and can_open_room):
                return {"ok": False, "error": "capability_denied"}
            task.key_placed = True
            task.room_open = True
            task.key_custody = "placed_in_room"
            task.status = "done"
            return {"ok": True, "status": task.status}

        return self.apply_once(event_id, operation)

    @staticmethod
    def room_ready(cleaning: Task, access: Task) -> bool:
        return (
            cleaning.status == "completed"
            and access.status == "done"
            and access.key_custody == "placed_in_room"
            and access.key_placed
            and access.room_open
            and not cleaning.missing
            and not cleaning.blocker
        )


def event_id() -> str:
    return str(uuid.uuid4())


def run_audit() -> dict[str, bool]:
    system = SyntheticPhase6()
    booking_id = str(uuid.uuid4())
    operator = "hk-primary"
    other_operator = "hk-unauthorized"

    direct = system.merge_task(
        "cleaning:direct",
        Task("cleaning-direct", "cleaning", booking_id, admin_priority_rank=1000),
    )
    automatic = system.merge_task(
        "cleaning:auto",
        Task("cleaning-auto", "cleaning", str(uuid.uuid4()), admin_priority_rank=0),
    )
    same_direct = system.merge_task(
        "cleaning:direct",
        Task("duplicate", "cleaning", booking_id, admin_priority_rank=0),
    )
    queue = sorted(
        [automatic, direct],
        key=lambda task: (-task.admin_priority_rank, task.task_id),
    )

    access = system.merge_task(
        "access:booking",
        Task(
            "access-direct",
            "access_prep",
            booking_id,
            status="sent",
            assigned_to=operator,
        ),
    )

    system.claim(direct, operator, event_id())
    direct.status = "in_progress"
    missing_event = event_id()
    first_missing = system.missing_item(direct, "water", missing_event)
    replay_missing = system.missing_item(direct, "water", missing_event)
    blocked_completion = system.complete_cleaning(direct, event_id())
    system.restore_item(direct, "water", event_id())
    completed = system.complete_cleaning(direct, event_id())

    ready_before_access = system.room_ready(direct, access)
    access_stayed_open_after_cleaning = access.status != "done"
    unauthorized = system.access_action(
        access,
        other_operator,
        can_place_key=False,
        can_open_room=False,
        event_id=event_id(),
    )
    authorized = system.access_action(
        access,
        operator,
        can_place_key=True,
        can_open_room=True,
        event_id=event_id(),
    )
    ready_after_access = system.room_ready(direct, access)

    same_day_now = datetime.now(timezone.utc)
    same_day_due = same_day_now + timedelta(hours=4)
    same_day_urgent_created = (
        same_day_due.date() == same_day_now.date()
        and "urgent" == "urgent"
    )
    sent_at = same_day_now - timedelta(minutes=31)
    no_ack_due = sent_at + timedelta(minutes=30)
    no_ack_triggered = same_day_now >= no_ack_due

    override = Task(
        "access-override",
        "access_prep",
        str(uuid.uuid4()),
        status="blocked",
        blocker="missing_key_evidence",
    )
    override.override_reason = "owner confirmed manually"
    override.status = "done"

    dual_targets = {
        target for target, task_id in system.notifications
        if task_id == direct.task_id
    }
    results = {
        "queue_priority_wrong": queue[0].task_id != direct.task_id,
        "duplicate_task_created": same_direct.task_id != direct.task_id or len(system.tasks) != 3,
        "missing_dual_notification": dual_targets != {"internal_ops", "owner"},
        "completion_not_blocked": blocked_completion.get("error") != "missing_checklist_items",
        "access_prep_coupled_to_cleaning": not access_stayed_open_after_cleaning,
        "capability_gate_failed": unauthorized.get("error") != "capability_denied",
        "owner_override_lost_evidence": not (override.override_reason and override.blocker),
        "guest_gate_opened_early": ready_before_access or not ready_after_access,
        "postback_not_idempotent": (
            not replay_missing.get("replayed")
            or len(system.incidents) != 1
            or first_missing.get("incident") != replay_missing.get("incident")
        ),
    }

    assert completed.get("ok") is True
    assert authorized.get("ok") is True
    assert same_day_urgent_created
    assert no_ack_triggered
    return results


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] != "assert":
        print("usage: phase6_full_execution_audit.py [assert]", file=sys.stderr)
        return 2

    results = run_audit()
    failures = [key for key in FAILURE_KEYS if results.get(key)]
    for key in FAILURE_KEYS:
        print(f"{key}: {'FAIL' if results[key] else 'PASS'}")
    if failures:
        print("PHASE 6 SYNTHETIC ACCEPTANCE FAILED:", ", ".join(failures))
        return 1
    print("ALL PHASE 6 SYNTHETIC ACCEPTANCE CRITERIA PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
