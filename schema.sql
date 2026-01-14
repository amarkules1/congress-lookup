CREATE TABLE IF NOT EXISTS congress_members_cache (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    data JSONB NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_congress_members_name ON congress_members_cache(name);
