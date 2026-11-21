CREATE TABLE IF NOT EXISTS demo_sessions (
    token_hash text PRIMARY KEY CHECK (length(token_hash) = 64),
    profile_id text NOT NULL REFERENCES profiles(profile_id) ON DELETE CASCADE,
    expires_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS demo_sessions_expiry_idx ON demo_sessions(expires_at);
