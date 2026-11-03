-- Run once in Supabase Dashboard → SQL Editor.
-- Account rows are reachable only by CoachBot's trusted server using its
-- private Supabase secret key. The browser receives neither this key nor SQL access.

create table if not exists public.coachbot_account_store (
    account_key text primary key
        check (account_key ~ '^[0-9a-f]{64}$'),
    payload jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

alter table public.coachbot_account_store enable row level security;

revoke all on table public.coachbot_account_store from public, anon, authenticated;
grant usage on schema public to service_role;
grant select, insert, update, delete on table public.coachbot_account_store to service_role;
