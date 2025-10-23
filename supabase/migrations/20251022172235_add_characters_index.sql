-- Add indices for filtering on like_count and token_count
create index if not exists characters_like_count_idx on public.characters(like_count);
create index if not exists characters_token_count_idx on public.characters(token_count);

-- Enable pg_trgm extension for efficient ILIKE searches
create extension if not exists pg_trgm with schema public;

-- Trigram GIN index to accelerate ilike '%q%'
create index if not exists characters_name_trgm_idx on public.characters using gin (name gin_trgm_ops);
