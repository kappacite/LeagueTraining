create table users (id integer primary key, discord_id text unique not null, name text not null,
  avatar text, created_at text not null);
create table allowlist (discord_id text primary key, added_at text not null);
create table sessions (token_hash text primary key,
  user_id integer not null references users(id) on delete cascade, expires_at text not null);
create table attempts (id integer primary key,
  user_id integer not null references users(id) on delete cascade,
  puzzle_id text not null, mode text not null check (mode in ('normal','chrono')),
  started_at text not null, answered_at text, answered_day text, choice_id text, grade text,
  points integer, timed_out integer not null default 0, scored integer not null);
create unique index attempts_one_scored on attempts(user_id, puzzle_id) where scored = 1;
create index attempts_puzzle on attempts(puzzle_id);
create index attempts_user on attempts(user_id);
create table daily (date text primary key, puzzle_id text not null);
