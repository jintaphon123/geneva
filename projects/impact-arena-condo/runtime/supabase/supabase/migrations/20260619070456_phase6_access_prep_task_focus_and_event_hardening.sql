-- Migration: Phase 6 Task 1 Hardening housekeeper_task_focus and event source_event_id
-- Created on: 2026-06-19

-- 1. Harden access_prep_task_events.source_event_id to NOT NULL
ALTER TABLE public.access_prep_task_events
  ALTER COLUMN source_event_id SET NOT NULL;

DROP INDEX IF EXISTS public.access_prep_task_events_source_event_unique;

CREATE UNIQUE INDEX access_prep_task_events_source_event_unique
  ON public.access_prep_task_events(source_event_id);

-- 2. Drop and recreate housekeeper_task_focus_valid_focus_check constraint
ALTER TABLE public.housekeeper_task_focus
  DROP CONSTRAINT IF EXISTS housekeeper_task_focus_valid_focus_check;

ALTER TABLE public.housekeeper_task_focus
  ADD CONSTRAINT housekeeper_task_focus_valid_focus_check
  CHECK (
    ((focus_type IS NULL) AND (focused_cleaning_task_id IS NULL) AND (focused_field_assistance_task_id IS NULL) AND (focused_access_prep_task_id IS NULL)) OR
    ((focus_type = 'cleaning') AND (focused_cleaning_task_id IS NOT NULL) AND (focused_field_assistance_task_id IS NULL) AND (focused_access_prep_task_id IS NULL)) OR
    ((focus_type = 'field_assistance') AND (focused_cleaning_task_id IS NULL) AND (focused_field_assistance_task_id IS NOT NULL) AND (focused_access_prep_task_id IS NULL)) OR
    ((focus_type = 'access_prep') AND (focused_cleaning_task_id IS NULL) AND (focused_field_assistance_task_id IS NULL) AND (focused_access_prep_task_id IS NOT NULL))
  );
