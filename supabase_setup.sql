-- Run this in Supabase Dashboard → SQL Editor → New Query → Run

-- 1. Tweet queue (shared between users)
create table if not exists queue (
  id bigint generated always as identity primary key,
  headline text not null,
  tweet text,
  status text default 'pending' check (status in ('pending', 'generating', 'ready', 'posted', 'failed')),
  created_at timestamptz default now(),
  created_by text
);

-- 2. Post history (every tweet posted)
create table if not exists post_history (
  id bigint generated always as identity primary key,
  tweet text not null,
  headline text,
  source text,
  tweet_id text,
  posted_at timestamptz default now(),
  cost_estimate numeric(10,4) default 0.0130
);

-- 3. Usage tracking (balance)
create table if not exists usage (
  id bigint generated always as identity primary key,
  initial_balance numeric(10,4) default 5.0000,
  cost_per_post numeric(10,4) default 0.0130,
  updated_at timestamptz default now()
);

-- Insert default usage row
insert into usage (initial_balance, cost_per_post) values (5.0000, 0.0130);

-- 4. Enable Row Level Security but allow all for anon (internal dashboard)
alter table queue enable row level security;
alter table post_history enable row level security;
alter table usage enable row level security;

create policy "Allow all on queue" on queue for all using (true) with check (true);
create policy "Allow all on post_history" on post_history for all using (true) with check (true);
create policy "Allow all on usage" on usage for all using (true) with check (true);
