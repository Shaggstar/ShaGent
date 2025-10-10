-- Enable UUID generation
create extension if not exists "pgcrypto";

-- Temporal Models
create table temporal_models (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  name text not null,
  description text,
  core_values jsonb default '[]'::jsonb,
  energy_profile jsonb default '{}'::jsonb,
  active_times text[],
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Goals
create table goals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  temporal_model text not null,
  domain text not null,
  objective text not null,
  key_results jsonb default '[]'::jsonb,
  current_skill int default 1 check (current_skill between 1 and 10),
  target_skill int default 10 check (target_skill between 1 and 10),
  status text default 'active' check (status in ('active', 'paused', 'completed', 'archived')),
  deadline date,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Tasks
create table tasks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  goal_id uuid references goals (id) on delete cascade,
  title text not null,
  description text,
  minutes int not null default 30,
  energy text not null default 'medium' check (energy in ('low', 'medium', 'high')),
  priority int default 3 check (priority between 1 and 5),
  skill_requirement int check (skill_requirement between 1 and 10),
  scheduled_for timestamptz,
  completed_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Focus Sessions
create table focus_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  task_id uuid references tasks (id) on delete set null,
  session_type text not null check (session_type in ('pomodoro', 'deep', 'interview', 'learning')),
  started_at timestamptz not null,
  ended_at timestamptz,
  duration_seconds int,
  focus_scores jsonb default '[]'::jsonb,
  average_focus int,
  notes text,
  created_at timestamptz default now()
);

-- Interview Sessions
create table interview_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  question text not null,
  recording_url text,
  transcription text,
  analysis jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

-- Daily Logs
create table daily_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  date date not null unique,
  temporal_model text,
  energy int check (energy between 1 and 5),
  mood text,
  coherence int check (coherence between 1 and 10),
  reflection text,
  gratitude text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Flashcards
create table flashcards (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  goal_id uuid references goals (id) on delete cascade,
  front text not null,
  back text not null,
  ease_factor float default 2.5,
  interval_days int default 1,
  next_review date not null,
  times_reviewed int default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Indexes
create index idx_goals_user_id on goals (user_id);
create index idx_goals_temporal_model on goals (temporal_model);
create index idx_tasks_user_id on tasks (user_id);
create index idx_tasks_scheduled_for on tasks (scheduled_for);
create index idx_focus_sessions_user_id on focus_sessions (user_id);
create index idx_daily_logs_user_date on daily_logs (user_id, date);
create index idx_flashcards_next_review on flashcards (next_review);
