package models

import "time"

// CrawlRequest represents an incoming crawl job request
type CrawlRequest struct {
	Platform    string `json:"platform" binding:"required"`
	TargetURL   string `json:"target_url" binding:"required"`
	MaxComments int    `json:"max_comments" binding:"required"`
}

// CrawlJob represents a job in the queue
type CrawlJob struct {
	ID           string    `json:"job_id"`
	Platform     string    `json:"platform"`
	TargetURL    string    `json:"target_url"`
	MaxComments  int       `json:"max_comments"`
	Status       string    `json:"status"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
	ErrorMessage string    `json:"error_message,omitempty"`
}

// CrawlResponse represents the API response for a new crawl job
type CrawlResponse struct {
	JobID  string `json:"job_id"`
	Status string `json:"status"`
}

// JobStatusResponse represents the API response for job status check
type JobStatusResponse struct {
	JobID        string    `json:"job_id"`
	Platform     string    `json:"platform"`
	Status       string    `json:"status"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
	ErrorMessage string    `json:"error_message,omitempty"`
}
