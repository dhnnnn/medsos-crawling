package database

import (
	"crawling/processing-api/models"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	_ "github.com/go-sql-driver/mysql"
)

type MySQLDB struct {
	db *sql.DB
}

// NewMySQLDB creates a new MySQL connection
func NewMySQLDB(host, port, user, password, dbname string) (*MySQLDB, error) {
	// MySQL DSN format: user:password@tcp(host:port)/dbname?parseTime=true
	// If password is empty: user@tcp(host:port)/dbname?parseTime=true
	var connStr string
	if password == "" {
		connStr = fmt.Sprintf("%s@tcp(%s:%s)/%s?parseTime=true&charset=utf8mb4",
			user, host, port, dbname)
	} else {
		connStr = fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true&charset=utf8mb4",
			user, password, host, port, dbname)
	}

	db, err := sql.Open("mysql", connStr)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %v", err)
	}

	// Test connection
	err = db.Ping()
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %v", err)
	}

	// Set connection pool settings
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	return &MySQLDB{db: db}, nil
}

// Close closes the database connection
func (db *MySQLDB) Close() error {
	return db.db.Close()
}

// SaveComments saves multiple comments to the database
func (db *MySQLDB) SaveComments(jobID string, comments []models.Comment) (int, int, error) {
	processed := 0
	duplicates := 0

	for _, comment := range comments {
		isDuplicate, err := db.SaveComment(jobID, comment)
		if err != nil {
			return processed, duplicates, fmt.Errorf("failed to save comment: %v", err)
		}

		if isDuplicate {
			duplicates++
		} else {
			processed++
		}
	}

	return processed, duplicates, nil
}

// SaveComment saves a single comment to the database
func (db *MySQLDB) SaveComment(jobID string, comment models.Comment) (bool, error) {
	// Convert raw_data to JSON
	var rawDataJSON []byte
	var err error
	if comment.RawData != nil {
		rawDataJSON, err = json.Marshal(comment.RawData)
		if err != nil {
			return false, fmt.Errorf("failed to marshal raw_data: %v", err)
		}
	}

	// MySQL: Use INSERT IGNORE to skip duplicates
	query := `
		INSERT INTO comments (
			job_id, platform, comment_id, username, user_id, 
			text, timestamp, likes, replies_count, parent_comment_id, raw_data
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON DUPLICATE KEY UPDATE id=id
	`

	result, err := db.db.Exec(
		query,
		jobID,
		comment.Platform,
		comment.CommentID,
		comment.Username,
		comment.UserID,
		comment.Text,
		comment.Timestamp,
		comment.Likes,
		comment.RepliesCount,
		comment.ParentCommentID,
		rawDataJSON,
	)

	if err != nil {
		return false, fmt.Errorf("failed to insert comment: %v", err)
	}

	// Check if row was actually inserted (not duplicate)
	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return true, nil // Duplicate
	}

	return false, nil // Successfully inserted
}

// UpdateJobStatus updates the job status in the database
func (db *MySQLDB) UpdateJobStatus(jobID string, status string) error {
	query := `
		INSERT INTO jobs (id, platform, target_url, max_comments, status)
		VALUES (?, 'unknown', 'unknown', 0, ?)
		ON DUPLICATE KEY UPDATE status = ?, updated_at = CURRENT_TIMESTAMP
	`

	_, err := db.db.Exec(query, jobID, status, status)
	if err != nil {
		return fmt.Errorf("failed to update job status: %v", err)
	}

	return nil
}

// GetCommentsByJobID retrieves all comments for a specific job
func (db *MySQLDB) GetCommentsByJobID(jobID string) ([]models.Comment, error) {
	query := `
		SELECT comment_id, username, user_id, text, timestamp, 
		       likes, replies_count, platform, parent_comment_id, raw_data
		FROM comments
		WHERE job_id = ?
		ORDER BY created_at DESC
	`

	rows, err := db.db.Query(query, jobID)
	if err != nil {
		return nil, fmt.Errorf("failed to query comments: %v", err)
	}
	defer rows.Close()

	var comments []models.Comment
	for rows.Next() {
		var comment models.Comment
		var rawDataJSON []byte

		err := rows.Scan(
			&comment.CommentID,
			&comment.Username,
			&comment.UserID,
			&comment.Text,
			&comment.Timestamp,
			&comment.Likes,
			&comment.RepliesCount,
			&comment.Platform,
			&comment.ParentCommentID,
			&rawDataJSON,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %v", err)
		}

		// Unmarshal raw_data if present
		if len(rawDataJSON) > 0 {
			err = json.Unmarshal(rawDataJSON, &comment.RawData)
			if err != nil {
				return nil, fmt.Errorf("failed to unmarshal raw_data: %v", err)
			}
		}

		comments = append(comments, comment)
	}

	return comments, nil
}
