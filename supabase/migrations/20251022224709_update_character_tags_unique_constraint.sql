-- Update unique constraint on tags to be (name, type)

-- Drop existing unique constraint on name if it exists
do $$
begin
  if exists (
    select 1
    from pg_constraint c
    join pg_class t on t.oid = c.conrelid
    join pg_namespace n on n.oid = t.relnamespace
    where c.contype = 'u'
      and c.conname = 'tags_name_key'
      and t.relname = 'tags'
      and n.nspname = 'public'
  ) then
    alter table public.tags drop constraint tags_name_key;
  end if;
end$$;

-- Add composite unique constraint on (name, type)
alter table public.tags add constraint tags_name_type_unique unique (name, type);

