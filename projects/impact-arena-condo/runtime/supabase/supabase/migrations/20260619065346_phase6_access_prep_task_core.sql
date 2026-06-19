-- Migration: Phase 6 Task 1 Access Prep Task Core Schema
-- Created on: 2026-06-19

-- 1. access_prep_tasks table
CREATE TABLE IF NOT EXISTS public.access_prep_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_key TEXT NOT NULL UNIQUE,
  booking_id UUID NOT NULL REFERENCES public.bookings(id) ON DELETE CASCADE,
  room_id UUID REFERENCES public.rooms(id) ON DELETE SET NULL,
  internal_ops_case_id UUID REFERENCES public.internal_ops_cases(id) ON DELETE SET NULL,
  assigned_housekeeper_id UUID REFERENCES public.housekeepers(id) ON DELETE SET NULL,
  owner_admin_user_id UUID REFERENCES public.admin_users(id) ON DELETE SET NULL,
  priority TEXT NOT NULL DEFAULT 'normal'
    CONSTRAINT access_prep_tasks_priority_check CHECK (priority IN ('urgent', 'high', 'normal')),
  status TEXT NOT NULL DEFAULT 'new'
    CONSTRAINT access_prep_tasks_status_check CHECK (status IN (
      'new','sent','acknowledged','in_progress','blocked','done',
      'no_ack','canceled','delivery_failed'
    )),
  dispatch_status TEXT NOT NULL DEFAULT 'pending'
    CONSTRAINT access_prep_tasks_dispatch_status_check CHECK (dispatch_status IN ('pending','sent','failed')),
  key_custody TEXT NOT NULL DEFAULT 'unknown'
    CONSTRAINT access_prep_tasks_key_custody_check CHECK (key_custody IN ('with_owner','with_operator','placed_in_room','unknown')),
  capabilities_required JSONB NOT NULL DEFAULT
    '{"can_place_key":true,"can_open_room":true}'::JSONB,
  scheduled_for TIMESTAMPTZ NOT NULL,
  due_at TIMESTAMPTZ,
  ack_due_at TIMESTAMPTZ,
  acknowledged_at TIMESTAMPTZ,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  blocker_reason TEXT,
  instructions TEXT,
  notes TEXT,
  override_reason TEXT,
  overridden_by UUID REFERENCES public.admin_users(id) ON DELETE SET NULL,
  overridden_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Unique index for active booking to ensure only one active task exists per booking
CREATE UNIQUE INDEX IF NOT EXISTS access_prep_tasks_active_booking_unique
  ON public.access_prep_tasks(booking_id)
  WHERE status NOT IN ('done','canceled','delivery_failed');

-- 2. access_prep_task_events table
CREATE TABLE IF NOT EXISTS public.access_prep_task_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  access_prep_task_id UUID NOT NULL
    REFERENCES public.access_prep_tasks(id) ON DELETE CASCADE,
  housekeeper_id UUID REFERENCES public.housekeepers(id) ON DELETE SET NULL,
  admin_user_id UUID REFERENCES public.admin_users(id) ON DELETE SET NULL,
  event_type TEXT NOT NULL,
  previous_state TEXT,
  new_state TEXT,
  source_event_id UUID,
  payload JSONB NOT NULL DEFAULT '{}'::JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Unique index for source event idempotency on events table
CREATE UNIQUE INDEX IF NOT EXISTS access_prep_task_events_source_event_unique
  ON public.access_prep_task_events(source_event_id)
  WHERE source_event_id IS NOT NULL;

-- 3. Extend housekeeper_task_focus table
ALTER TABLE public.housekeeper_task_focus
  ADD COLUMN IF NOT EXISTS focused_access_prep_task_id UUID
    REFERENCES public.access_prep_tasks(id) ON DELETE SET NULL;

ALTER TABLE public.housekeeper_task_focus
  DROP CONSTRAINT IF EXISTS housekeeper_task_focus_type_check;

ALTER TABLE public.housekeeper_task_focus
  ADD CONSTRAINT housekeeper_task_focus_type_check
  CHECK (focus_type IN ('cleaning','access_prep','field_assistance'));

-- --- Enable RLS ---
ALTER TABLE public.access_prep_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.access_prep_task_events ENABLE ROW LEVEL SECURITY;

-- --- Revoke Access from Public, Anon, Authenticated ---
REVOKE ALL ON TABLE public.access_prep_tasks FROM public, anon, authenticated;
REVOKE ALL ON TABLE public.access_prep_task_events FROM public, anon, authenticated;

-- --- Grant Access to service_role and postgres ---
GRANT ALL ON TABLE public.access_prep_tasks TO postgres, service_role;
GRANT ALL ON TABLE public.access_prep_task_events TO postgres, service_role;

-- --- Create Indexes ---
-- Open assigned tasks
CREATE INDEX IF NOT EXISTS idx_access_prep_tasks_assigned_status
  ON public.access_prep_tasks(assigned_housekeeper_id, status);

-- Acknowledgement deadlines
CREATE INDEX IF NOT EXISTS idx_access_prep_tasks_ack_due
  ON public.access_prep_tasks(ack_due_at)
  WHERE status = 'sent';

-- Due work
CREATE INDEX IF NOT EXISTS idx_access_prep_tasks_due_at
  ON public.access_prep_tasks(due_at);
