CREATE TABLE IF NOT EXISTS personal_access (
    profile_id text PRIMARY KEY REFERENCES profiles(profile_id) ON DELETE CASCADE,
    code_hash text NOT NULL CHECK (code_hash ~ '^[a-f0-9]{64}$'),
    graph_pending boolean NOT NULL DEFAULT true
);
