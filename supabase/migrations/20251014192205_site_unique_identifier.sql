-- Add site_unique_identifier column to creators table
alter table public.creators add column site_unique_identifier text not null;

-- Add unique constraint to ensure site_unique_identifier is unique per site
create unique index if not exists creators_site_unique_identifier_site_id_unique_idx 
  on public.creators(site_unique_identifier, site_id);

