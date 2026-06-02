-- Daniel AI Suite — unified account memory (run after 001_suite_activity.sql)
-- Same suite_user_id in [suite_activity] secrets on phone, laptop, and every app.

-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
create table if not exists public.suite_users (
  id uuid primary key default gen_random_uuid(),
  external_id text not null unique,
  email text not null default '',
  display_name text not null default '',
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- app_activity (extends suite_activity_events)
-- ---------------------------------------------------------------------------
alter table public.suite_activity_events
  add column if not exists user_id uuid references public.suite_users (id);

create index if not exists idx_suite_events_user_ts
  on public.suite_activity_events (user_id, timestamp desc);

-- ---------------------------------------------------------------------------
-- app_state (extends suite_app_current_state) — per user + app
-- ---------------------------------------------------------------------------
alter table public.suite_app_current_state
  add column if not exists user_id uuid references public.suite_users (id);

-- Resume items: per-user continue cards
alter table public.suite_resume_items
  add column if not exists user_id uuid references public.suite_users (id);

-- ---------------------------------------------------------------------------
-- saved_items — songs, players, portfolios, simulations, etc.
-- ---------------------------------------------------------------------------
create table if not exists public.suite_saved_items (
  id bigint generated always as identity primary key,
  user_id uuid not null references public.suite_users (id) on delete cascade,
  app text not null,
  item_type text not null default 'item',
  item_key text not null,
  title text not null,
  payload jsonb not null default '{}'::jsonb,
  valid boolean not null default true,
  updated_at timestamptz not null default now(),
  unique (user_id, app, item_type, item_key)
);

create index if not exists idx_suite_saved_user_app
  on public.suite_saved_items (user_id, app, valid, updated_at desc);

-- ---------------------------------------------------------------------------
-- user_settings — per app or global (_global)
-- ---------------------------------------------------------------------------
create table if not exists public.suite_user_settings (
  user_id uuid not null references public.suite_users (id) on delete cascade,
  app text not null default '_global',
  settings jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (user_id, app)
);

-- ---------------------------------------------------------------------------
-- Backfill legacy rows (single personal account)
-- ---------------------------------------------------------------------------
insert into public.suite_users (external_id, email, display_name)
values ('default', '', 'Daniel AI Suite')
on conflict (external_id) do nothing;

update public.suite_activity_events
set user_id = (select id from public.suite_users where external_id = 'default' limit 1)
where user_id is null;

update public.suite_app_current_state
set user_id = (select id from public.suite_users where external_id = 'default' limit 1)
where user_id is null;

update public.suite_resume_items
set user_id = (select id from public.suite_users where external_id = 'default' limit 1)
where user_id is null;

-- Optional: tighten PK on app_state after backfill (run manually if you had only one user):
-- alter table public.suite_app_current_state drop constraint if exists suite_app_current_state_pkey;
-- alter table public.suite_app_current_state add primary key (user_id, app);

alter table public.suite_users disable row level security;
alter table public.suite_saved_items disable row level security;
alter table public.suite_user_settings disable row level security;
