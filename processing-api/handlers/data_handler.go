package handlers

import (
	"crawling/processing-api/database"
	"crawling/processing-api/models"
	"net/http"

	"github.com/gin-gonic/gin"
)

type DataHandler struct {
	db *database.MySQLDB
}

func NewDataHandler(db *database.MySQLDB) *DataHandler {
	return &DataHandler{db: db}
}

// ProcessData handles POST /api/process
func (h *DataHandler) ProcessData(c *gin.Context) {
	var req models.ProcessRequest

	// Validate request body
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"details": err.Error(),
		})
		return
	}

	// Validate we have comments
	if len(req.Comments) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "No comments provided",
		})
		return
	}

	// Save comments to database
	processed, duplicates, err := h.db.SaveComments(req.JobID, req.Comments)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to save comments",
			"details": err.Error(),
		})
		return
	}

	// Update job status to completed
	err = h.db.UpdateJobStatus(req.JobID, "stored")
	if err != nil {
		// Log error but don't fail the request
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to update job status",
			"details": err.Error(),
		})
		return
	}

	// Return success response
	c.JSON(http.StatusOK, models.ProcessResponse{
		Success:    true,
		Processed:  processed,
		Duplicates: duplicates,
		Message:    "Comments processed successfully",
	})
}

// GetComments handles GET /api/comments/:job_id
func (h *DataHandler) GetComments(c *gin.Context) {
	jobID := c.Param("job_id")

	comments, err := h.db.GetCommentsByJobID(jobID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to retrieve comments",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"job_id":   jobID,
		"count":    len(comments),
		"comments": comments,
	})
}
