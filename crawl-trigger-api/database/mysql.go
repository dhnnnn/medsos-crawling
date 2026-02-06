package database

import (
	"database/sql"
	"fmt"
	"time"

	_ "github.com/go-sql-driver/mysql"
)

type MySQLDB struct {
	db *sql.DB
}

// NewMySQLDB creates a new MySQL database connection
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
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %v", err)
	}

	// Set connection pool settings
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	return &MySQLDB{db: db}, nil
}

// Close closes the database connection
func (m *MySQLDB) Close() error {
	return m.db.Close()
}

// CreateJob inserts a new job record into the jobs table
func (m *MySQLDB) CreateJob(jobID, platform, targetURL string, maxComments int) error {
	query := `
		INSERT INTO jobs (id, platform, target_url, max_comments, status, created_at, updated_at)
		VALUES (?, ?, ?, ?, 'queued', NOW(), NOW())
	`

	_, err := m.db.Exec(query, jobID, platform, targetURL, maxComments)
	if err != nil {
		return fmt.Errorf("failed to create job: %v", err)
	}

	return nil
}

// UpdateJobStatus updates the status of a job
func (m *MySQLDB) UpdateJobStatus(jobID, status string, errorMessage *string) error {
	var query string
	var args []interface{}

	if errorMessage != nil {
		query = `
			UPDATE jobs 
			SET status = ?, error_message = ?, updated_at = NOW()
			WHERE id = ?
		`
		args = []interface{}{status, *errorMessage, jobID}
	} else {
		query = `
			UPDATE jobs 
			SET status = ?, updated_at = NOW()
			WHERE id = ?
		`
		args = []interface{}{status, jobID}
	}

	_, err := m.db.Exec(query, args...)
	if err != nil {
		return fmt.Errorf("failed to update job status: %v", err)
	}

	return nil
}
