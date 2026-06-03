-- TatvaOps Omnichannel schema extensions (run in Supabase SQL editor)
-- Also create Storage bucket: enquiry-files (public read)

ALTER TABLE enquiries ADD COLUMN IF NOT EXISTS service_category TEXT;
ALTER TABLE enquiries ADD COLUMN IF NOT EXISTS lead_score INTEGER;
ALTER TABLE enquiries ADD COLUMN IF NOT EXISTS lead_tier TEXT;

ALTER TABLE project_summaries ADD COLUMN IF NOT EXISTS service_category TEXT;

ALTER TABLE sessions_log ADD COLUMN IF NOT EXISTS service_category TEXT;
ALTER TABLE sessions_log ADD COLUMN IF NOT EXISTS active_consultant TEXT;
ALTER TABLE sessions_log ADD COLUMN IF NOT EXISTS lead_score INTEGER;
ALTER TABLE sessions_log ADD COLUMN IF NOT EXISTS lead_tier TEXT;
ALTER TABLE sessions_log ADD COLUMN IF NOT EXISTS flow_state JSONB;

CREATE TABLE IF NOT EXISTS enquiry_attachments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    file_name TEXT,
    file_url TEXT,
    mime_type TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS enquiries_session_id_idx ON enquiries (session_id);
CREATE UNIQUE INDEX IF NOT EXISTS sessions_log_session_id_idx ON sessions_log (session_id);
