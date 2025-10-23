-- Create tags table
create table if not exists public.tags (
  id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
  name TEXT NOT NULL UNIQUE
);

-- Create character_tags junction table
create table if not exists public.character_tags (
  character_id UUID NOT NULL REFERENCES public.characters(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES public.tags(id) ON DELETE CASCADE,
  PRIMARY KEY (character_id, tag_id)
);

-- Add indexes for efficient lookups
create index if not exists character_tags_character_id_idx on public.character_tags(character_id);
create index if not exists character_tags_tag_id_idx on public.character_tags(tag_id);

-- Enable row level security
alter table public.tags enable row level security;
alter table public.character_tags enable row level security;

-- RLS policies for tags (read-only for all users)
create policy "tags_allow_select" on public.tags
  for select using (true);

-- RLS policies for character_tags (read-only for all users)
create policy "character_tags_allow_select" on public.character_tags
  for select using (true);
