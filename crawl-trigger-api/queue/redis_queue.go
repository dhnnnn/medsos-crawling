package queue

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
)

type RedisQueue struct {
	client *redis.Client
	ctx    context.Context
}

// NewRedisQueue creates a new Redis queue client
func NewRedisQueue(host string, port string, password string) (*RedisQueue, error) {
	client := redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%s", host, port),
		Password: password,
		DB:       0,
	})

	ctx := context.Background()

	// Test connection
	_, err := client.Ping(ctx).Result()
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %v", err)
	}

	return &RedisQueue{
		client: client,
		ctx:    ctx,
	}, nil
}

// PublishJob publishes a crawl job to the queue
func (q *RedisQueue) PublishJob(jobData map[string]interface{}) error {
	jsonData, err := json.Marshal(jobData)
	if err != nil {
		return fmt.Errorf("failed to marshal job data: %v", err)
	}

	err = q.client.LPush(q.ctx, "crawl_jobs", jsonData).Err()
	if err != nil {
		return fmt.Errorf("failed to push job to queue: %v", err)
	}

	return nil
}

// SetJobStatus updates job status in Redis
func (q *RedisQueue) SetJobStatus(jobID string, status string) error {
	key := fmt.Sprintf("job_status:%s", jobID)
	err := q.client.Set(q.ctx, key, status, 24*time.Hour).Err()
	if err != nil {
		return fmt.Errorf("failed to set job status: %v", err)
	}
	return nil
}

// GetJobStatus retrieves job status from Redis
func (q *RedisQueue) GetJobStatus(jobID string) (string, error) {
	key := fmt.Sprintf("job_status:%s", jobID)
	status, err := q.client.Get(q.ctx, key).Result()
	if err == redis.Nil {
		return "not_found", nil
	} else if err != nil {
		return "", fmt.Errorf("failed to get job status: %v", err)
	}
	return status, nil
}

// StoreJobData stores complete job information
func (q *RedisQueue) StoreJobData(jobID string, jobData map[string]interface{}) error {
	key := fmt.Sprintf("job_data:%s", jobID)
	jsonData, err := json.Marshal(jobData)
	if err != nil {
		return fmt.Errorf("failed to marshal job data: %v", err)
	}

	err = q.client.Set(q.ctx, key, jsonData, 24*time.Hour).Err()
	if err != nil {
		return fmt.Errorf("failed to store job data: %v", err)
	}
	return nil
}

// GetJobData retrieves complete job information
func (q *RedisQueue) GetJobData(jobID string) (map[string]interface{}, error) {
	key := fmt.Sprintf("job_data:%s", jobID)
	data, err := q.client.Get(q.ctx, key).Result()
	if err == redis.Nil {
		return nil, fmt.Errorf("job not found")
	} else if err != nil {
		return nil, fmt.Errorf("failed to get job data: %v", err)
	}

	var jobData map[string]interface{}
	err = json.Unmarshal([]byte(data), &jobData)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal job data: %v", err)
	}

	return jobData, nil
}

// Close closes the Redis connection
func (q *RedisQueue) Close() error {
	return q.client.Close()
}
