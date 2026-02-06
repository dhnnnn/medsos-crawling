package handlers

import (
	"crawl-trigger-api/database"
	"crawl-trigger-api/models"
	"crawl-trigger-api/queue"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type CrawlHandler struct {
	queue *queue.RedisQueue
	db    *database.MySQLDB
}

func NewCrawlHandler(q *queue.RedisQueue, d *database.MySQLDB) *CrawlHandler {
	return &CrawlHandler{
		queue: q,
		db:    d,
	}
}

// CreateCrawlJob handles POST /api/crawl
func (h *CrawlHandler) CreateCrawlJob(c *gin.Context) {
	var req models.CrawlRequest

	// Validate request body
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"details": err.Error(),
		})
		return
	}

	// Validate platform
	validPlatforms := map[string]bool{
		"instagram": true,
		"tiktok":    true,
		"facebook":  true,
	}

	if !validPlatforms[req.Platform] {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid platform. Must be one of: instagram, tiktok, facebook",
		})
		return
	}

	// Validate max_comments
	if req.MaxComments <= 0 || req.MaxComments > 10000 {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "max_comments must be between 1 and 10000",
		})
		return
	}

	// Generate unique job ID
	jobID := uuid.New().String()

	// Create job data
	now := time.Now()
	jobData := map[string]interface{}{
		"job_id":       jobID,
		"platform":     req.Platform,
		"target_url":   req.TargetURL,
		"max_comments": req.MaxComments,
		"status":       "queued",
		"created_at":   now.Format(time.RFC3339),
		"updated_at":   now.Format(time.RFC3339),
	}

	// Create job in MySQL database
	err := h.db.CreateJob(jobID, req.Platform, req.TargetURL, req.MaxComments)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to create job in database",
			"details": err.Error(),
		})
		return
	}

	// Store job data in Redis
	err = h.queue.StoreJobData(jobID, jobData)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to store job data",
			"details": err.Error(),
		})
		return
	}

	// Set initial job status
	err = h.queue.SetJobStatus(jobID, "queued")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to set job status",
			"details": err.Error(),
		})
		return
	}

	// Publish job to queue
	err = h.queue.PublishJob(jobData)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to queue job",
			"details": err.Error(),
		})
		return
	}

	// Return response
	c.JSON(http.StatusCreated, models.CrawlResponse{
		JobID:  jobID,
		Status: "queued",
	})
}

// GetJobStatus handles GET /api/crawl/:job_id/status
func (h *CrawlHandler) GetJobStatus(c *gin.Context) {
	jobID := c.Param("job_id")

	// Get job data from Redis
	jobData, err := h.queue.GetJobData(jobID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error":  "Job not found",
			"job_id": jobID,
		})
		return
	}

	// Get current status
	status, err := h.queue.GetJobStatus(jobID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to get job status",
			"details": err.Error(),
		})
		return
	}

	// Parse timestamps
	createdAt, _ := time.Parse(time.RFC3339, jobData["created_at"].(string))
	updatedAt, _ := time.Parse(time.RFC3339, jobData["updated_at"].(string))

	// Build response
	response := models.JobStatusResponse{
		JobID:     jobID,
		Platform:  jobData["platform"].(string),
		Status:    status,
		CreatedAt: createdAt,
		UpdatedAt: updatedAt,
	}

	if errorMsg, ok := jobData["error_message"].(string); ok {
		response.ErrorMessage = errorMsg
	}

	c.JSON(http.StatusOK, response)
}
