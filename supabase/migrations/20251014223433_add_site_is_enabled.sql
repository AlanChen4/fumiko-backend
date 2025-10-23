-- Add is_enabled column to sites table
alter table public.sites add column is_enabled boolean not null default true;

-- Create index for better query performance when filtering by is_enabled
create index if not exists sites_is_enabled_idx on public.sites(is_enabled);
