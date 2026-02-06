from crawlers.base_crawler import BaseCrawler
from utils.anti_ban import random_delay, human_like_scroll
import logging

logger = logging.getLogger(__name__)

class FacebookCrawler(BaseCrawler):
    """Facebook-specific crawler implementation"""
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
    
    def crawl(self, url: str, max_comments: int) -> list:
        """
        Crawl comments from a Facebook post
        
        Args:
            url: Facebook post URL
            max_comments: Maximum number of comments to collect
            
        Returns:
            list: List of comment dictionaries
        """
        comments = []
        
        try:
            self.initialize_browser()
            logger.info(f"Starting Facebook crawl for {url}")
            
            # Navigate to post
            self.page.goto(url, wait_until='networkidle', timeout=30000)
            random_delay(3000, 5000)
            
            # Handle cookie consent
            try:
                cookie_button = self.page.query_selector('[data-cookiebanner="accept_button"]')
                if cookie_button:
                    cookie_button.click()
                    random_delay(1000, 2000)
            except:
                pass
            
            # Scroll to load comments
            logger.info("Loading comments...")
            self._load_facebook_comments(max_comments)
            
            # Extract comments
            comment_selectors = [
                '[data-ad-preview="message"]',
                '.comment-content',
                '[role="article"] [dir="auto"]'
            ]
            
            comment_elements = []
            for selector in comment_selectors:
                elements = self.page.query_selector_all(selector)
                if elements:
                    comment_elements = elements
                    break
            
            logger.info(f"Found {len(comment_elements)} comment elements")
            
            for idx, element in enumerate(comment_elements[:max_comments]):
                if idx >= max_comments:
                    break
                
                try:
                    comment_data = self._extract_facebook_comment(element, idx)
                    if comment_data:
                        comments.append(comment_data)
                        logger.info(f"Extracted comment {idx + 1}/{max_comments}")
                except Exception as e:
                    logger.warning(f"Failed to extract comment {idx}: {e}")
                    continue
            
            logger.info(f"Successfully crawled {len(comments)} comments from Facebook")
            
        except Exception as e:
            logger.error(f"Facebook crawl failed: {e}")
            raise
        finally:
            self.close_browser()
        
        return comments
    
    def _load_facebook_comments(self, max_comments: int):
        """Scroll and expand comment threads"""
        scroll_attempts = 0
        max_scrolls = min(max_comments // 10, 15)
        
        while scroll_attempts < max_scrolls:
            # Scroll down
            human_like_scroll(self.page, scroll_count=3)
            
            # Try to click "View more comments" or similar
            try:
                view_more_selectors = [
                    '[role="button"]:has-text("View more comments")',
                    '[role="button"]:has-text("See more")',
                    'span:has-text("View more")'
                ]
                
                for selector in view_more_selectors:
                    try:
                        button = self.page.query_selector(selector)
                        if button:
                            button.click()
                            random_delay(2000, 3000)
                            break
                    except:
                        continue
            except:
                pass
            
            scroll_attempts += 1
            random_delay(1500, 2500)
    
    def _extract_facebook_comment(self, element, index: int) -> dict:
        """Extract comment data from Facebook comment element"""
        try:
            # Get comment text
            text = element.inner_text() or ""
            
            # Try to find username (parent element usually contains it)
            username = f"user_{index}"
            try:
                parent = element.query_selector('..')
                if parent:
                    username_elem = parent.query_selector('a[role="link"]')
                    if username_elem:
                        username = username_elem.inner_text()
            except:
                pass
            
            # Extract timestamp if available
            timestamp = None
            try:
                time_elem = element.query_selector('abbr')
                if time_elem:
                    timestamp = time_elem.get_attribute('data-utime')
            except:
                pass
            
            return {
                'comment_id': f"fb_{index}_{hash(text)}",
                'username': username,
                'user_id': username,
                'text': text,
                'timestamp': timestamp,
                'likes': 0,
                'replies_count': 0,
                'platform': 'facebook'
            }
        except Exception as e:
            logger.error(f"Failed to parse Facebook comment: {e}")
            return None
