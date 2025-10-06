-- enable row level security
alter table public.users enable row level security;

-- Users table: only owner can select and update (no insert/delete)
create policy "Users can view their own user row"
on public.users
for select
to authenticated
using (id = auth.uid());

create policy "Users can update their own user row"
on public.users
for update
to authenticated
using (id = auth.uid())
with check (id = auth.uid());