#!/usr/bin/env python3
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    for raw in (ROOT / "runtime/.env").read_text().splitlines():
        raw = raw.strip()
        if raw and not raw.startswith("#") and "=" in raw:
            key, value = raw.split("=", 1)
            os.environ.setdefault(key, value.strip().strip("\"'"))


load_env()
BASE = os.environ["SUPABASE_URL"] + "/rest/v1/"
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
WRITE_HEADERS = {**HEADERS, "Content-Type": "application/json", "Prefer": "return=representation"}


def request(method: str, path: str, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers=WRITE_HEADERS if body is not None else HEADERS,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        raise RuntimeError(f"{method} {path}: {exc.code} {raw}") from exc


def post(table: str, body: dict) -> dict:
    rows = request("POST", table, body)
    return rows[0]


def rpc(name: str, body: dict) -> dict:
    return request("POST", f"rpc/{name}", body)


def delete(table: str, column: str, value: str) -> None:
    request("DELETE", f"{table}?{column}=eq.{urllib.parse.quote(value, safe='')}")


def main() -> None:
    marker = uuid.uuid4().hex[:10]
    ids: dict[str, str] = {}
    try:
        room = post("rooms", {
            "room_code": f"P6-SMOKE-{marker}",
            "building": "P6TEST",
            "floor": 1,
            "room_number": marker,
            "portfolio": "bond",
            "listing_tier": "flex_popularcondo",
            "quality_tier": 3,
            "active": True,
        })
        ids["room"] = room["id"]
        post("room_status", {
            "room_id": ids["room"],
            "cleaning_status": "dirty",
            "occupancy_status": "vacant",
            "maintenance_status": "ok",
        })
        guest = post("guests", {
            "display_name": f"Phase6 Smoke {marker}",
            "primary_channel": "direct",
            "language_preference": "th",
        })
        ids["guest"] = guest["id"]
        booking = post("bookings", {
            "platform": "direct",
            "reservation_number": f"P6-SMOKE-{marker}",
            "guest_id": ids["guest"],
            "guest_name_snapshot": f"Phase6 Smoke {marker}",
            "check_in_date": str(date.today() + timedelta(days=1)),
            "check_out_date": str(date.today() + timedelta(days=2)),
            "room_id": ids["room"],
            "listing_tier": "flex_popularcondo",
            "booking_status": "confirmed",
        })
        ids["booking"] = booking["id"]
        post("guest_stay_states", {
            "booking_id": ids["booking"],
            "guest_id": ids["guest"],
            "room_id": ids["room"],
            "booking_verification_status": "confirmed",
        })
        for suffix in ("a", "b"):
            housekeeper = post("housekeepers", {
                "line_user_id": f"U_PHASE6_SMOKE_{marker}_{suffix}",
                "display_name": f"Phase6 Operator {suffix}",
                "status": "active",
                "role": "housekeeper",
                "active": True,
            })
            ids[f"hk_{suffix}"] = housekeeper["id"]
        cleaning = post("cleaning_tasks", {
            "task_key": f"phase6-smoke-cleaning-{marker}",
            "room_id": ids["room"],
            "booking_id": ids["booking"],
            "task_type": "turnover_cleaning",
            "priority": "urgent",
            "status": "waiting_ack",
            "dispatch_status": "sent",
            "due_at": f"{date.today() + timedelta(days=1)}T02:00:00Z",
        })
        ids["cleaning"] = cleaning["id"]
        for key, label in [
            ("room_cleaned", "ทำความสะอาด"),
            ("bedsheet", "ผ้าปูที่นอน"),
            ("towels", "ผ้าขนหนู"),
            ("water", "น้ำ"),
            ("tissue", "ทิชชู่"),
            ("soap", "สบู่"),
        ]:
            post("cleaning_task_checklist_items", {
                "cleaning_task_id": ids["cleaning"],
                "room_id": ids["room"],
                "item_key": key,
                "item_label": label,
                "status": "present",
            })
        access = post("access_prep_tasks", {
            "task_key": f"phase6-smoke-access-{marker}",
            "booking_id": ids["booking"],
            "room_id": ids["room"],
            "assigned_housekeeper_id": ids["hk_a"],
            "priority": "urgent",
            "status": "sent",
            "dispatch_status": "sent",
            "key_custody": "with_owner",
            "scheduled_for": f"{date.today()}T12:00:00Z",
            "due_at": f"{date.today() + timedelta(days=1)}T02:00:00Z",
        })
        ids["access"] = access["id"]
        asset = post("assets", {
            "asset_id": f"phase6-smoke-access-{marker}",
            "asset_type": "room_entry_infographic",
            "title": "Phase 6 smoke room access",
            "building": "P6TEST",
            "line_sendable": True,
            "usage_trigger": "phase6_access_smoke",
            "context_requirement": "isolated_fixture_only",
            "send_timing": "before_checkin",
            "status": "approved",
            "metadata": {"fixture": True, "marker": marker},
        })
        ids["asset"] = asset["id"]

        before = rpc("get_room_access_readiness", {"p_booking_id": ids["booking"]})
        assert before["ready"] is False
        assert "cleaning_incomplete" in before["blockers"]
        assert "access_prep_incomplete" in before["blockers"]

        first_claim = rpc("claim_housekeeping_task", {
            "p_task_kind": "cleaning",
            "p_task_id": ids["cleaning"],
            "p_housekeeper_id": ids["hk_a"],
            "p_source_event_id": str(uuid.uuid4()),
        })
        second_claim = rpc("claim_housekeeping_task", {
            "p_task_kind": "cleaning",
            "p_task_id": ids["cleaning"],
            "p_housekeeper_id": ids["hk_b"],
            "p_source_event_id": str(uuid.uuid4()),
        })
        assert first_claim["ok"] is True
        assert second_claim["error"] == "already_claimed"

        request("PATCH", f"cleaning_tasks?id=eq.{ids['cleaning']}", {
            "status": "completed",
            "checklist_status": "complete",
        })
        request("PATCH", f"room_status?room_id=eq.{ids['room']}", {
            "cleaning_status": "clean",
        })
        middle = rpc("get_room_access_readiness", {"p_booking_id": ids["booking"]})
        assert middle["cleaning_ready"] is True
        assert middle["access_prep_ready"] is False
        assert middle["ready"] is False

        request("PATCH", f"access_prep_tasks?id=eq.{ids['access']}", {
            "status": "done",
            "key_custody": "placed_in_room",
            "blocker_reason": None,
        })
        after = rpc("get_room_access_readiness", {"p_booking_id": ids["booking"]})
        assert after["ready"] is True, after
        print("PHASE 6 LIVE BACKEND SMOKE PASSED")
        print(json.dumps({
            "booking_id": ids["booking"],
            "cleaning_task_id": ids["cleaning"],
            "access_prep_task_id": ids["access"],
            "before_blockers": before["blockers"],
            "middle_blockers": middle["blockers"],
            "after_blockers": after["blockers"],
            "second_claim": second_claim["error"],
        }, indent=2))
    finally:
        if "cleaning" in ids:
            delete("housekeeper_task_focus", "focused_cleaning_task_id", ids["cleaning"])
        if "access" in ids:
            delete("housekeeper_task_focus", "focused_access_prep_task_id", ids["access"])
        if "access" in ids:
            delete("access_prep_tasks", "id", ids["access"])
        if "cleaning" in ids:
            delete("cleaning_tasks", "id", ids["cleaning"])
        if "booking" in ids:
            delete("bookings", "id", ids["booking"])
        if "asset" in ids:
            delete("assets", "id", ids["asset"])
        if "room" in ids:
            delete("rooms", "id", ids["room"])
        if "guest" in ids:
            delete("guests", "id", ids["guest"])
        for key in ("hk_a", "hk_b"):
            if key in ids:
                delete("housekeepers", "id", ids[key])


if __name__ == "__main__":
    main()
