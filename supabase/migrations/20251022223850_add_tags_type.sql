-- Add type column to tags table
alter table public.tags add column type smallint not null;

-- Create index for efficient filtering by type
create index if not exists tags_type_idx on public.tags(type);
