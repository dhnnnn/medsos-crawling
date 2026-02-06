package models

// Comment represents a crawled comment
type Comment struct {
	CommentID       string                 `json:"comment_id"`
	Username        string                 `json:"username"`
	UserID          string                 `json:"user_id"`
	Text            string                 `json:"text"`
	Timestamp       *string                `json:"timestamp"`
	Likes           int                    `json:"likes"`
	RepliesCount    int                    `json:"replies_count"`
	Platform        string                 `json:"platform"`
	ParentCommentID *string                `json:"parent_comment_id,omitempty"`
	RawData         map[string]interface{} `json:"raw_data,omitempty"`
}

// ProcessRequest represents incoming data from crawler workers
type ProcessRequest struct {
	JobID    string    `json:"job_id" binding:"required"`
	Comments []Comment `json:"comments" binding:"required"`
}

// ProcessResponse represents the API response after processing
type ProcessResponse struct {
	Success    bool   `json:"success"`
	Processed  int    `json:"processed"`
	Duplicates int    `json:"duplicates"`
	Message    string `json:"message"`
}
