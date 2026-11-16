create table scene_steps (id integer primary key,
  attempt_id integer not null references attempts(id) on delete cascade,
  node_id text not null, started_at text not null, answered_at text, choice_id text, grade text,
  points integer, timed_out integer not null default 0,
  unique(attempt_id, node_id));
