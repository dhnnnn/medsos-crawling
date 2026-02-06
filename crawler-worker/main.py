import redis
import json
import logging
import os
import sys
import requests
from dotenv import load_dotenv
from crawlers.instagram_crawler import InstagramCrawler
from crawlers.tiktok_crawler import TikTokCrawler
from crawlers.facebook_crawler import FacebookCrawler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('../.env')

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
PROCESSING_API_URL = f"http://localhost:{os.getenv('PROCESSING_API_PORT', '8081')}/api/process"

# Initialize Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD if REDIS_PASSWORD else None,
    decode_responses=True
)

def update_job_status(job_id: str, status: str, error_message: str = None):
    """Update job status in Redis"""
    try:
        redis_client.set(f"job_status:{job_id}", status, ex=86400)  # 24 hours
        
        if error_message:
            job_data = redis_client.get(f"job_data:{job_id}")
            if job_data:
                job_dict = json.loads(job_data)
                job_dict['error_message'] = error_message
                job_dict['status'] = status
                redis_client.set(f"job_data:{job_id}", json.dumps(job_dict), ex=86400)
        
        logger.info(f"Updated job {job_id} status to: {status}")
    except Exception as e:
        logger.error(f"Failed to update job status: {e}")

def send_to_processing_api(job_id: str, comments: list):
    """Send crawled comments to Processing API"""
    try:
        payload = {
            'job_id': job_id,
            'comments': comments
        }
        
        response = requests.post(PROCESSING_API_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"Successfully sent {len(comments)} comments to Processing API")
            return True
        else:
            logger.error(f"Processing API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send data to Processing API: {e}")
        return False

def process_crawl_job(job_data: dict):
    """Process a single crawl job"""
    job_id = job_data.get('job_id')
    platform = job_data.get('platform')
    target_url = job_data.get('target_url')
    max_comments = job_data.get('max_comments', 100)
    
    logger.info(f"Processing job {job_id}: {platform} - {target_url}")
    
    # Update status to processing
    update_job_status(job_id, 'processing')
    
    try:
        # Select appropriate crawler
        crawler = None
        if platform == 'instagram':
            crawler = InstagramCrawler(headless=False)  # Visual debugging
        elif platform == 'tiktok':
            crawler = TikTokCrawler(headless=False)  # Visual debugging enabled
        elif platform == 'facebook':
            crawler = FacebookCrawler(headless=False)  # Visual debugging
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Perform crawl
        logger.info(f"Starting crawl with {crawler.__class__.__name__}")
        comments = crawler.crawl(target_url, max_comments)
        
        if not comments:
            logger.warning(f"No comments found for job {job_id}")
            update_job_status(job_id, 'completed')
            return
        
        # Send to Processing API
        success = send_to_processing_api(job_id, comments)
        
        if success:
            update_job_status(job_id, 'completed')
            logger.info(f"Job {job_id} completed successfully with {len(comments)} comments")
        else:
            update_job_status(job_id, 'failed', 'Failed to send data to Processing API')
    
    except Exception as e:
        error_msg = f"Crawl failed: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_msg}")
        update_job_status(job_id, 'failed', error_msg)

def main():
    """Main worker loop - listens to Redis queue and processes jobs"""
    logger.info("🚀 Crawler Worker started")
    logger.info(f"📡 Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    logger.info("⏳ Waiting for jobs...")
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        sys.exit(1)
    
    # Main worker loop
    while True:
        try:
            # Block and wait for job from queue (BRPOP for blocking right pop)
            result = redis_client.brpop('crawl_jobs', timeout=5)
            
            if result:
                queue_name, job_json = result
                job_data = json.loads(job_json)
                
                logger.info(f"📥 Received new job: {job_data.get('job_id')}")
                
                # Process the job
                process_crawl_job(job_data)
            
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            continue

if __name__ == "__main__":
    main()
