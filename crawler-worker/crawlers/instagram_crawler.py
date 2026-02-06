import logging
import os
from crawlers.base_crawler import BaseCrawler
from utils.anti_ban import random_delay, human_like_scroll

logger = logging.getLogger(__name__)

class InstagramCrawler(BaseCrawler):
    """Instagram-specific crawler implementation"""
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.instagram_username = os.getenv('INSTAGRAM_USERNAME', '')
        self.instagram_password = os.getenv('INSTAGRAM_PASSWORD', '')
    
    def _login_instagram(self):
        """Auto-login to Instagram to avoid popups and CAPTCHA"""
        if not self.instagram_username or not self.instagram_password:
            logger.info("No Instagram credentials in .env - skipping auto-login")
            return False
        
        try:
            logger.info(f"Attempting Instagram login for user: {self.instagram_username}")
            
            # Navigate to login page
            self.page.goto('https://www.instagram.com/accounts/login/', wait_until='domcontentloaded', timeout=30000)
            random_delay(3000, 5000)
            
            # Fill username
            username_input = self.page.wait_for_selector('input[name="username"]', timeout=10000)
            username_input.fill(self.instagram_username)
            random_delay(1000, 2000)
            
            # Fill password
            password_input = self.page.query_selector('input[name="password"]')
            if password_input:
                password_input.fill(self.instagram_password)
                random_delay(1000, 2000)
            
            # Click login button
            login_button = self.page.query_selector('button[type="submit"]')
            if login_button:
                login_button.click()
                logger.info("Login button clicked, waiting for redirect...")
                random_delay(5000, 8000)
            
            # Handle "Save Your Login Info" popup
            try:
                self.page.click('button:has-text("Not Now")', timeout=5000)
                random_delay(1000, 2000)
            except:
                pass
            
            # Handle "Turn on Notifications" popup
            try:
                self.page.click('button:has-text("Not Now")', timeout=5000)
            except:
                pass
            
            logger.info("✅ Instagram login successful!")
            return True
                
        except Exception as e:
            logger.error(f"Instagram login failed: {e}")
            return False
    
    def crawl(self, url: str, max_comments: int) -> list:
        """
        Crawl comments from an Instagram post
        
        Args:
            url: Instagram post URL
            max_comments: Maximum number of comments to collect
            
        Returns:
            list: List of comment dictionaries
        """
        comments = []
        
        try:
            self.initialize_browser()
            logger.info(f"Starting Instagram crawl for {url}")
            
            # Auto-login if credentials provided
            if self.instagram_username and self.instagram_password:
                self._login_instagram()
            
            # Navigate to post
            self.page.goto(url, wait_until='networkidle', timeout=30000)
            random_delay(2000, 4000)
            
            # Try to close any popups
            try:
                self.page.click('button:has-text("Not Now")', timeout=3000)
            except:
                pass
            
            # Scroll to load comments
            logger.info("Loading comments...")
            self._load_all_comments(max_comments)
            
            # Extract comments
            comment_elements = self.page.query_selector_all('ul ul li')
            logger.info(f"Found {len(comment_elements)} comment elements")
            
            for idx, element in enumerate(comment_elements[:max_comments]):
                if idx >= max_comments:
                    break
                
                try:
                    comment_data = self._extract_instagram_comment(element, idx)
                    if comment_data:
                        comments.append(comment_data)
                        logger.info(f"Extracted comment {idx + 1}/{max_comments}")
                except Exception as e:
                    logger.warning(f"Failed to extract comment {idx}: {e}")
                    continue
            
            logger.info(f"Successfully crawled {len(comments)} comments from Instagram")
            
        except Exception as e:
            logger.error(f"Instagram crawl failed: {e}")
            raise
        finally:
            self.close_browser()
        
        return comments
    
    def _load_all_comments(self, max_comments: int):
        """Scroll and click 'View more comments' to load all comments"""
        scroll_attempts = 0
        max_scrolls = min(max_comments // 10, 20)  # Adjust based on comments needed
        
        while scroll_attempts < max_scrolls:
            # Scroll down
            human_like_scroll(self.page, scroll_count=2)
            
            # Try to click "View more comments" button
            try:
                view_more = self.page.query_selector('button:has-text("View")')
                if view_more:
                    view_more.click()
                    random_delay(1500, 2500)
            except:
                pass
            
            scroll_attempts += 1
            random_delay(1000, 2000)
    
    def _extract_instagram_comment(self, element, index: int) -> dict:
        """Extract comment data from Instagram comment element"""
        try:
            # Extract username
            username_elem = element.query_selector('a[href*="/"]')
            username = username_elem.inner_text() if username_elem else f"user_{index}"
            
            # Extract comment text
            text_elem = element.query_selector('span')
            text = text_elem.inner_text() if text_elem else ""
            
            # Extract timestamp (if available)
            time_elem = element.query_selector('time')
            timestamp = time_elem.get_attribute('datetime') if time_elem else None
            
            return {
                'comment_id': f"ig_{index}_{hash(text)}",
                'username': username,
                'user_id': username,  # Instagram doesn't expose user ID easily
                'text': text,
                'timestamp': timestamp,
                'likes': 0,  # Would need additional API calls
                'replies_count': 0,
                'platform': 'instagram'
            }
        except Exception as e:
            logger.error(f"Failed to parse Instagram comment: {e}")
            return None
