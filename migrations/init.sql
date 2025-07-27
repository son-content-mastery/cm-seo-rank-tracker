-- SEO Rank Tracker Database Schema
-- This file initializes the database with all required tables

-- Create the keywords table
CREATE TABLE IF NOT EXISTS keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Add indexes for better performance
    UNIQUE(keyword, domain)
);

-- Create index on keywords table
CREATE INDEX IF NOT EXISTS idx_keywords_active ON keywords(is_active);
CREATE INDEX IF NOT EXISTS idx_keywords_domain ON keywords(domain);

-- Create the rankings table
CREATE TABLE IF NOT EXISTS rankings (
    id SERIAL PRIMARY KEY,
    keyword_id INTEGER REFERENCES keywords(id) ON DELETE CASCADE,
    position INTEGER,
    url TEXT,
    title TEXT,
    found_in_top_100 BOOLEAN DEFAULT false,
    serp_features JSONB,
    check_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT positive_position CHECK (position > 0 OR position IS NULL),
    CONSTRAINT valid_check_date CHECK (check_date <= CURRENT_DATE)
);

-- Create indexes on rankings table
CREATE INDEX IF NOT EXISTS idx_rankings_keyword_id ON rankings(keyword_id);
CREATE INDEX IF NOT EXISTS idx_rankings_check_date ON rankings(check_date);
CREATE INDEX IF NOT EXISTS idx_rankings_position ON rankings(position);
CREATE INDEX IF NOT EXISTS idx_rankings_keyword_date ON rankings(keyword_id, check_date);

-- Create the ranking_changes table
CREATE TABLE IF NOT EXISTS ranking_changes (
    id SERIAL PRIMARY KEY,
    keyword_id INTEGER REFERENCES keywords(id) ON DELETE CASCADE,
    previous_position INTEGER,
    current_position INTEGER,
    position_change INTEGER,
    change_direction VARCHAR(50),
    change_magnitude VARCHAR(50),
    change_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_change_direction CHECK (change_direction IN ('up', 'down', 'new', 'lost', 'same')),
    CONSTRAINT valid_change_magnitude CHECK (change_magnitude IN ('major', 'moderate', 'minor', 'none')),
    CONSTRAINT valid_change_date CHECK (change_date <= CURRENT_DATE)
);

-- Create indexes on ranking_changes table
CREATE INDEX IF NOT EXISTS idx_ranking_changes_keyword_id ON ranking_changes(keyword_id);
CREATE INDEX IF NOT EXISTS idx_ranking_changes_date ON ranking_changes(change_date);
CREATE INDEX IF NOT EXISTS idx_ranking_changes_direction ON ranking_changes(change_direction);

-- Insert some default keywords if none exist
INSERT INTO keywords (keyword, domain, is_active) VALUES
    ('make.com คือ', 'contentmastery.io', true),
    ('favicon คือ', 'contentmastery.io', true),
    ('make.com', 'contentmastery.io', true),
    ('content mastery', 'contentmastery.io', true),
    ('เรียน seo ได้ใบ เซอร์ ฟรี', 'contentmastery.io', true),
    ('semrush คือ', 'contentmastery.io', true),
    ('คอร์สเรียน seo ฟรี', 'contentmastery.io', true),
    ('ไอคอน fav', 'contentmastery.io', true),
    ('make automation', 'contentmastery.io', true),
    ('seo news', 'contentmastery.io', true),
    ('semrush', 'contentmastery.io', true),
    ('make com', 'contentmastery.io', true),
    ('seo tools', 'contentmastery.io', true),
    ('make.com คืออะไร', 'contentmastery.io', true),
    ('make.com ราคา', 'contentmastery.io', true),
    ('noindex tag', 'contentmastery.io', true),
    ('seo', 'contentmastery.io', true),
    ('semantic html', 'contentmastery.io', true),
    ('favicon', 'contentmastery.io', true),
    ('technical seo', 'contentmastery.io', true)
ON CONFLICT (keyword, domain) DO NOTHING;

-- Create a view for latest rankings with changes
CREATE OR REPLACE VIEW latest_rankings_with_changes AS
SELECT 
    k.id as keyword_id,
    k.keyword,
    k.domain,
    k.is_active,
    r.position,
    r.url,
    r.title,
    r.found_in_top_100,
    r.check_date,
    rc.previous_position,
    rc.position_change,
    rc.change_direction,
    rc.change_magnitude
FROM keywords k
LEFT JOIN LATERAL (
    SELECT * FROM rankings 
    WHERE keyword_id = k.id 
    ORDER BY check_date DESC 
    LIMIT 1
) r ON true
LEFT JOIN LATERAL (
    SELECT * FROM ranking_changes 
    WHERE keyword_id = k.id 
    ORDER BY change_date DESC 
    LIMIT 1
) rc ON true
WHERE k.is_active = true;

-- Create a function to get ranking history for a keyword
CREATE OR REPLACE FUNCTION get_keyword_history(
    keyword_id_param INTEGER,
    days_param INTEGER DEFAULT 30
)
RETURNS TABLE (
    check_date DATE,
    position INTEGER,
    found_in_top_100 BOOLEAN,
    url TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.check_date,
        r.position,
        r.found_in_top_100,
        r.url
    FROM rankings r
    WHERE r.keyword_id = keyword_id_param
        AND r.check_date >= CURRENT_DATE - INTERVAL '%s days' % days_param
    ORDER BY r.check_date ASC;
END;
$$ LANGUAGE plpgsql;

-- Create a function to calculate weekly summary statistics
CREATE OR REPLACE FUNCTION get_weekly_stats()
RETURNS TABLE (
    total_keywords BIGINT,
    ranked_keywords BIGINT,
    top_10_count BIGINT,
    top_3_count BIGINT,
    improvements BIGINT,
    declines BIGINT,
    new_rankings BIGINT,
    lost_rankings BIGINT,
    avg_position NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH latest_data AS (
        SELECT * FROM latest_rankings_with_changes
    )
    SELECT 
        COUNT(*) as total_keywords,
        COUNT(CASE WHEN found_in_top_100 = true THEN 1 END) as ranked_keywords,
        COUNT(CASE WHEN position <= 10 THEN 1 END) as top_10_count,
        COUNT(CASE WHEN position <= 3 THEN 1 END) as top_3_count,
        COUNT(CASE WHEN change_direction = 'up' THEN 1 END) as improvements,
        COUNT(CASE WHEN change_direction = 'down' THEN 1 END) as declines,
        COUNT(CASE WHEN change_direction = 'new' THEN 1 END) as new_rankings,
        COUNT(CASE WHEN change_direction = 'lost' THEN 1 END) as lost_rankings,
        AVG(CASE WHEN position IS NOT NULL THEN position END) as avg_position
    FROM latest_data;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to automatically update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.created_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add comments to tables for documentation
COMMENT ON TABLE keywords IS 'Stores the list of keywords to track rankings for';
COMMENT ON TABLE rankings IS 'Stores daily ranking data for each keyword';
COMMENT ON TABLE ranking_changes IS 'Tracks position changes between ranking checks';

COMMENT ON COLUMN keywords.keyword IS 'The search term to track rankings for';
COMMENT ON COLUMN keywords.domain IS 'The domain to check rankings for';
COMMENT ON COLUMN keywords.is_active IS 'Whether this keyword should be included in checks';

COMMENT ON COLUMN rankings.position IS 'Position in search results (1-100), NULL if not found';
COMMENT ON COLUMN rankings.found_in_top_100 IS 'Whether the domain was found in top 100 results';
COMMENT ON COLUMN rankings.serp_features IS 'JSON data containing additional SERP information';

COMMENT ON COLUMN ranking_changes.position_change IS 'Positive number = improvement (moved up), negative = decline';
COMMENT ON COLUMN ranking_changes.change_direction IS 'Direction of change: up, down, new, lost, same';
COMMENT ON COLUMN ranking_changes.change_magnitude IS 'Magnitude of change: major, moderate, minor, none';