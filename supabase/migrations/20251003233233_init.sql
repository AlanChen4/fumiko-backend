create table if not exists public.users (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    email TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_premium BOOLEAN DEFAULT FALSE
);

create table if not exists public.sites (
  id uuid primary key default extensions.uuid_generate_v4(),
  name text not null,
  url text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.creators (
  id uuid primary key default extensions.uuid_generate_v4(),
  name text not null,
  image_url text,
  urls text[] not null default '{}',
  site_id uuid not null references public.sites(id) on delete cascade,
  follower_count integer,
  created_at timestamptz not null default now()
);

create index if not exists creators_site_id_idx on public.creators(site_id);

create table if not exists public.characters (
  id uuid primary key default extensions.uuid_generate_v4(),
  name text not null,
  description text not null,
  url text not null,
  image_url text not null,
  chat_count integer,
  message_count integer,
  like_count integer,
  token_count integer,
  creator_id uuid not null references public.creators(id) on delete cascade,
  created_at timestamptz not null default now()
);

create index if not exists characters_creator_id_idx on public.characters(creator_id);
create index if not exists characters_url_idx on public.characters(url);

-- Add unique constraint to character URL to support upserts
alter table public.characters add constraint characters_url_unique unique (url);

-- enable row level security
alter table public.sites enable row level security;
alter table public.creators enable row level security;
alter table public.characters enable row level security;

create policy "sites_allow_all" on public.sites
  for all using (true);

create policy "creators_allow_all" on public.creators
  for all using (true);

create policy "characters_allow_all" on public.characters
  for all using (true);

-- handle new user trigger
create function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
begin
  insert into public.users (id, email)
  values (new.id, new.email);
  return new;
end;
$$;
-- trigger the function every time a user is created
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();