-- Jobs table for tracking crawl requests
CREATE TABLE IF NOT EXISTS jobs (
    id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    target_url TEXT NOT NULL,
    max_comments INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    error_message TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Comments table for raw crawled data
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    job_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    comment_id VARCHAR(255),
    username VARCHAR(255),
    user_id VARCHAR(255),
    text TEXT,
    timestamp TIMESTAMP NULL,
    likes INTEGER DEFAULT 0,
    replies_count INTEGER DEFAULT 0,
    parent_comment_id VARCHAR(255),
    raw_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_comment (platform, comment_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    INDEX idx_job_id (job_id),
    INDEX idx_username (username),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Processed comments table for normalized/analyzed data
CREATE TABLE IF NOT EXISTS processed_comments (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    comment_id INTEGER NOT NULL,
    sentiment VARCHAR(50),
    keywords TEXT,
    language VARCHAR(10),
    is_spam BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_processed (comment_id),
    FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE,
    INDEX idx_sentiment (sentiment)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Additional indexes for jobs table
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
