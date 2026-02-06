package main

import (
	"crawling/processing-api/database"
	"crawling/processing-api/handlers"
	"fmt"
	"log"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
)

func main() {
	// Load environment variables
	err := godotenv.Load("../.env")
	if err != nil {
		// Try loading from current directory
		err = godotenv.Load(".env")
	}
	if err != nil {
		log.Println("Warning: .env file not found, using environment variables")
	}

	// Get database configuration
	dbHost := getEnv("DB_HOST", "localhost")
	dbPort := getEnv("DB_PORT", "3306")
	dbUser := getEnv("DB_USER", "root")
	dbPassword := getEnv("DB_PASSWORD", "")
	dbName := getEnv("DB_NAME", "social_crawler")
	apiPort := getEnv("PROCESSING_API_PORT", "8081")

	// Initialize MySQL connection
	db, err := database.NewMySQLDB(dbHost, dbPort, dbUser, dbPassword, dbName)
	if err != nil {
		log.Fatalf("Failed to connect to MySQL: %v", err)
	}
	defer db.Close()

	log.Println("✅ Connected to MySQL successfully")

	// Initialize handlers
	dataHandler := handlers.NewDataHandler(db)

	// Setup Gin router
	router := gin.Default()

	// CORS middleware
	router.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	})

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status":  "healthy",
			"service": "processing-api",
		})
	})

	// API routes
	api := router.Group("/api")
	{
		api.POST("/process", dataHandler.ProcessData)
		api.GET("/comments/:job_id", dataHandler.GetComments)
	}

	// Start server
	addr := fmt.Sprintf(":%s", apiPort)
	log.Printf("🚀 Processing API starting on http://localhost%s", addr)
	log.Printf("📋 Endpoints:")
	log.Printf("   POST   http://localhost%s/api/process", addr)
	log.Printf("   GET    http://localhost%s/api/comments/:job_id", addr)
	log.Printf("   GET    http://localhost%s/health", addr)

	if err := router.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}
