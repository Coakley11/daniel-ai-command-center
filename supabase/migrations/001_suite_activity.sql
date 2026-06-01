-- Daniel AI Suite — shared activity store (Supabase)
-- Run in Supabase SQL Editor for a new project, then add URL + service_role key to Streamlit secrets.

create table if not exists public.suite_activity_events (
  id bigint generated always as identity primary key,
  app text not null,
  event text not null,
  page text not null default '',
  timestamp timestamptz not null default now(),
  metrics jsonb not null default '{}'::jsonb
);

create index if not exists idx_suite_events_app_ts
  on public.suite_activity_events (app, timestamp desc);

create table if not exists public.suite_app_current_state (
  app text primary key,
  page text not null default '',
  summary text not null default '',
  metrics jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists public.suite_resume_items (
  id bigint generated always as identity primary key,
  app text not null,
  item_key text not null,
  title text not null,
  subtitle text not null default '',
  action_url text not null default '',
  valid boolean not null default true,
  updated_at timestamptz not null default now(),
  unique (app, item_key)
);

create index if not exists idx_suite_resume_valid
  on public.suite_resume_items (valid, updated_at desc);

-- Access control: store service_role key only in Streamlit Cloud secrets (server-side).
-- Do not embed the key in client-side code. RLS stays off for this personal backend.
alter table public.suite_activity_events disable row level security;
alter table public.suite_app_current_state disable row level security;
alter table public.suite_resume_items disable row level security;
