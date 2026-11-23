INSERT INTO profiles VALUES (%s, %s, %s)
ON CONFLICT (profile_id) DO NOTHING;
