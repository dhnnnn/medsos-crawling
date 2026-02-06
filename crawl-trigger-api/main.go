package main

import (
	"crawl-trigger-api/database"
	"crawl-trigger-api/handlers"
	"crawl-trigger-api/queue"
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
		log.Println("Warning: .env file not found, using environment variables")
	}

	// Get configuration from environment
	redisHost := getEnv("REDIS_HOST", "localhost")
	redisPort := getEnv("REDIS_PORT", "6379")
	redisPassword := getEnv("REDIS_PASSWORD", "")
	apiPort := getEnv("CRAWL_API_PORT", "8080")

	// MySQL configuration
	dbHost := getEnv("DB_HOST", "localhost")
	dbPort := getEnv("DB_PORT", "3306")
	dbUser := getEnv("DB_USER", "root")
	dbPassword := getEnv("DB_PASSWORD", "")
	dbName := getEnv("DB_NAME", "social_crawler")

	// Initialize MySQL database
	db, err := database.NewMySQLDB(dbHost, dbPort, dbUser, dbPassword, dbName)
	if err != nil {
		log.Fatalf("Failed to connect to MySQL: %v", err)
	}
	defer db.Close()

	log.Println("✅ Connected to MySQL successfully")

	// Initialize Redis queue
	redisQueue, err := queue.NewRedisQueue(redisHost, redisPort, redisPassword)
	if err != nil {
		log.Fatalf("Failed to connect to Redis: %v", err)
	}
	defer redisQueue.Close()

	log.Println("✅ Connected to Redis successfully")

	// Initialize handlers
	crawlHandler := handlers.NewCrawlHandler(redisQueue, db)

	// Setup Gin router
	router := gin.Default()

	// Add CORS middleware
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
			"service": "crawl-trigger-api",
		})
	})

	// API routes
	api := router.Group("/api")
	{
		api.POST("/crawl", crawlHandler.CreateCrawlJob)
		api.GET("/crawl/:job_id/status", crawlHandler.GetJobStatus)
	}

	// Start server
	addr := fmt.Sprintf(":%s", apiPort)
	log.Printf("🚀 Crawl Trigger API starting on http://localhost%s", addr)
	log.Printf("📋 Endpoints:")
	log.Printf("   POST   http://localhost%s/api/crawl", addr)
	log.Printf("   GET    http://localhost%s/api/crawl/:job_id/status", addr)
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
