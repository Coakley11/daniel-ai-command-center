-- Run ONLY if 002 failed at suite_user_settings (partial apply).
-- Safe if 002 already completed fully (no-op via IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS public.suite_user_settings (
  user_id uuid NOT NULL REFERENCES public.suite_users (id) ON DELETE CASCADE,
  app text NOT NULL DEFAULT '_global',
  settings jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, app)
);

ALTER TABLE public.suite_user_settings DISABLE ROW LEVEL SECURITY;
