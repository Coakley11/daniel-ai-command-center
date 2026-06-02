-- Paste this entire file into Supabase SQL Editor.
-- Run after 001_suite_activity.sql. Safe to re-run.

CREATE TABLE IF NOT EXISTS public.suite_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id text NOT NULL UNIQUE,
  email text NOT NULL DEFAULT '',
  display_name text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE public.suite_activity_events
  ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES public.suite_users (id);

CREATE INDEX IF NOT EXISTS idx_suite_events_user_ts
  ON public.suite_activity_events (user_id, timestamp DESC);

ALTER TABLE public.suite_app_current_state
  ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES public.suite_users (id);

ALTER TABLE public.suite_resume_items
  ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES public.suite_users (id);

CREATE TABLE IF NOT EXISTS public.suite_saved_items (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES public.suite_users (id) ON DELETE CASCADE,
  app text NOT NULL,
  item_type text NOT NULL DEFAULT 'item',
  item_key text NOT NULL,
  title text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  valid boolean NOT NULL DEFAULT true,
  updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, app, item_type, item_key)
);

CREATE INDEX IF NOT EXISTS idx_suite_saved_user_app
  ON public.suite_saved_items (user_id, app, valid, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.suite_user_settings (
  user_id uuid NOT NULL REFERENCES public.suite_users (id) ON DELETE CASCADE,
  app text NOT NULL DEFAULT '_global',
  settings jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, app)
);

INSERT INTO public.suite_users (external_id, email, display_name)
VALUES ('default', '', 'Daniel AI Suite')
ON CONFLICT (external_id) DO NOTHING;

UPDATE public.suite_activity_events
SET user_id = (SELECT id FROM public.suite_users WHERE external_id = 'default' LIMIT 1)
WHERE user_id IS NULL;

UPDATE public.suite_app_current_state
SET user_id = (SELECT id FROM public.suite_users WHERE external_id = 'default' LIMIT 1)
WHERE user_id IS NULL;

UPDATE public.suite_resume_items
SET user_id = (SELECT id FROM public.suite_users WHERE external_id = 'default' LIMIT 1)
WHERE user_id IS NULL;

ALTER TABLE public.suite_resume_items
  DROP CONSTRAINT IF EXISTS suite_resume_items_app_item_key_key;

CREATE UNIQUE INDEX IF NOT EXISTS idx_suite_resume_user_app_item_key
  ON public.suite_resume_items (user_id, app, item_key);

ALTER TABLE public.suite_users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.suite_saved_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.suite_user_settings DISABLE ROW LEVEL SECURITY;
