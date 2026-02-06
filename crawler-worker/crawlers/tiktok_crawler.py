import logging
import os
from typing import List
from crawlers.base_crawler import BaseCrawler
from utils.anti_ban import random_delay, human_like_scroll

logger = logging.getLogger(__name__)

class TikTokCrawler(BaseCrawler):
    """Crawler for TikTok comments"""
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.platform = 'tiktok'
        self.tiktok_username = os.getenv('TIKTOK_USERNAME', '')
        self.tiktok_password = os.getenv('TIKTOK_PASSWORD', '')
    
    def _login_tiktok(self):
        """Auto-login to TikTok to avoid CAPTCHA and popups"""
        if not self.tiktok_username or not self.tiktok_password:
            logger.info("No TikTok credentials in .env - skipping auto-login")
            return False
        
        try:
            logger.info(f"Attempting TikTok login for user: {self.tiktok_username}")
            
            # Navigate to login page
            self.page.goto('https://www.tiktok.com/login/phone-or-email/email', wait_until='domcontentloaded', timeout=30000)
            random_delay(3000, 5000)
            
            # Fill username/email
            username_input = self.page.wait_for_selector('input[name="username"]', timeout=10000)
            username_input.fill(self.tiktok_username)
            random_delay(1000, 2000)
            
            # Fill password
            password_input = self.page.query_selector('input[type="password"]')
            if password_input:
                password_input.fill(self.tiktok_password)
                random_delay(1000, 2000)
            
            # Click login button
            login_button = self.page.query_selector('button[type="submit"]')
            if login_button:
                login_button.click()
                logger.info("Login button clicked, waiting for redirect...")
                random_delay(5000, 8000)  # Wait for login to complete
            
            # Check if login successful (redirect to homepage)
            if 'foryou' in self.page.url or 'following' in self.page.url:
                logger.info("✅ TikTok login successful!")
                return True
            else:
                logger.warning("⚠️ Login may have failed or requires 2FA/CAPTCHA")
                return False
                
        except Exception as e:
            logger.error(f"TikTok login failed: {e}")
            return False
    
    def crawl(self, url: str, max_comments: int) -> list:
        """
        Crawl comments from a TikTok video
        
        Args:
            url: TikTok video URL
            max_comments: Maximum number of comments to collect
            
        Returns:
            list: List of comment dictionaries
        """
        comments = []
        
        try:
            self.initialize_browser()
            logger.info(f"Starting TikTok crawl for {url}")
            
            # Auto-login if credentials provided (avoids CAPTCHA & popups)
            if self.tiktok_username and self.tiktok_password:
                self._login_tiktok()  # Login first, then navigate to video
            
            # Navigate to TikTok video (TikTok loads slowly due to heavy JS)
            # Use domcontentloaded instead of networkidle for faster initial load
            try:
                self.page.goto(url, wait_until='domcontentloaded', timeout=90000)
                # Wait for page to stabilize
                self.page.wait_for_timeout(3000)
                # Wait for video player to ensure page is loaded
                self.page.wait_for_selector('video, [data-e2e="browse-video"]', timeout=30000, state='visible')
            except Exception as e:
                logger.warning(f"Initial page load issue: {e}. Retrying with longer timeout...")
                # Retry with even longer timeout
                self.page.goto(url, wait_until='load', timeout=120000)
            
            # Give more time for TikTok to fully load
            logger.info("Waiting for TikTok page to stabilize...")
            random_delay(20000, 30000)  # Increased to 20-30s for very slow loading
            
            # Check for CAPTCHA
            try:
                captcha_selectors = [
                    'iframe[title*="CAPTCHA"]',
                    'div[id*="captcha"]',
                    '[class*="captcha"]',
                    'div:has-text("Verify you are human")',
                ]
                captcha_found = False
                for sel in captcha_selectors:
                    if self.page.query_selector(sel):
                        captcha_found = True
                        break
                
                if captcha_found:
                    logger.warning("⚠️ CAPTCHA DETECTED! Please solve it manually in the browser window.")
                    logger.warning("Waiting 60 seconds for manual CAPTCHA solve...")
                    self.page.wait_for_timeout(60000)  # Wait 60s for user to solve
                    logger.info("Continuing after CAPTCHA wait...")
            except:
                pass  # No CAPTCHA, continue
            
            # Close any login popups or region blocks
            try:
                # Try multiple selectors for close buttons
                close_selectors = [
                    '[aria-label="Close"]',
                    'button[data-e2e="modal-close-inner-button"]',
                    'div[role="button"]:has-text("Close")',
                    'svg[fill="currentColor"]'
                ]
                for selector in close_selectors:
                    close_button = self.page.query_selector(selector)
                    if close_button:
                        close_button.click()
                        random_delay(1000, 2000)
                        break
            except:
                pass
            
            # Scroll to comments section
            logger.info("Scrolling to comments section...")
            self._scroll_to_comments()
            
            # Click on Comments tab (TikTok sometimes defaults to "You may like" tab)
            logger.info("Looking for Comments tab to click...")
            try:
                # Try to find and click Comments tab/button
                comments_tab_selectors = [
                    'button:has-text("Comments")',
                    'div:has-text("Comments")',
                    '[data-e2e="comment-panel"]',
                    'span:has-text("评论")',  # Chinese
                    'span:has-text("Komentar")',  # Indonesian
                ]
                
                for selector in comments_tab_selectors:
                    try:
                        tab = self.page.query_selector(selector)
                        if tab:
                            logger.info(f"Found Comments tab with selector: {selector}")
                            tab.click()
                            random_delay(2000, 3000)
                            logger.info("Clicked on Comments tab")
                            break
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Could not find/click Comments tab: {e}")
            
            # Scroll more to ensure we're in comments section
            logger.info("Scrolling further down to comments...")
            for _ in range(3):
                self.page.evaluate("window.scrollBy(0, 600)")
                random_delay(1000, 2000)
            
            # Wait after scrolling for comments to load
            logger.info("Waiting for comments to render after scroll...")
            random_delay(15000, 20000)  # Increased to 15-20s for very slow networks
            
            # Load more comments
            self._load_more_comments(max_comments)
            
            # Wait for comments to load
            logger.info("Waiting for comment elements to load...")
            try:
                self.page.wait_for_selector('[data-e2e="comment-item"]', timeout=30000, state='visible')  # Increased to 30s
                logger.info("Comment selector found!")
            except Exception as e:
                logger.warning(f"Comment selector not found with data-e2e. Trying alternative selectors...")
                # Try alternative selectors
                try:
                    self.page.wait_for_selector('div[class*="comment"]', timeout=5000, state='visible')
                    logger.info("Alternative comment selector found!")
                except:
                    logger.error("No comment selectors found. Taking screenshot for debugging...")
                    self.page.screenshot(path='tiktok_debug.png')
                    logger.error("Screenshot saved as tiktok_debug.png")
            
            # Extract comments with retry logic - try multiple selectors
            comment_elements = []
            max_retries = 3
            
            # Multiple selector strategies for TikTok (they change frequently)
            selector_strategies = [
                'div[class*="DivVirtualItemContainer"]',  # NEW: Based on HTML inspection (2024)
                'div[class*="DivCommentListContainer"] > div',  # Container > direct children
                '[data-e2e="comment-item"]',  # Original selector
                'div[data-e2e="comment-level-1"]',  # Updated 2024 selector
                'div[class*="CommentItem"]',  # Class-based
                'div[class*="comment-item"]',  # Lowercase class
                'div[class*="DivCommentItemContainer"]',  # Container class
                '[data-testid="comment-item"]',  # Test ID based
                'div.comment',  # Simple class selector
            ]
            
            for attempt in range(max_retries):
                logger.info(f"Attempt {attempt + 1}/{max_retries} to find comments...")
                
                # Try each selector strategy
                for idx, selector in enumerate(selector_strategies):
                    elements = self.page.query_selector_all(selector)
                    if elements:
                        comment_elements = elements
                        logger.info(f"Found {len(comment_elements)} comments using selector #{idx + 1}: {selector}")
                        break
                
                if comment_elements:
                    break
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"No comments found on attempt {attempt + 1}, waiting and retrying...")
                        random_delay(3000, 5000)
                        # Try scrolling again to trigger lazy loading
                        self.page.evaluate("window.scrollBy(0, 200)")
                        random_delay(2000, 3000)
            
            if not comment_elements:
                logger.error(f"No comment elements found after {max_retries} attempts with {len(selector_strategies)} different selectors")
                logger.error("Check tiktok_debug.png to inspect page structure")
            else:
                # Save HTML for manual inspection
                try:
                    html_content = self.page.content()
                    with open('tiktok_page_source.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info("✅ Saved page HTML to tiktok_page_source.html for manual inspection")
                except Exception as e:
                    logger.warning(f"Failed to save HTML: {e}")
            
            for idx, element in enumerate(comment_elements[:max_comments]):
                if idx >= max_comments:
                    break
                
                try:
                    comment_data = self._extract_tiktok_comment(element, idx)
                    if comment_data:
                        username = comment_data.get('username', 'unknown')
                        text = comment_data.get('text', '')
                        logger.info(f"Extracted comment {idx + 1}/{max_comments}: @{username} - '{text[:50]}...' ({len(text)} chars)")
                        comments.append(comment_data)
                    else:
                        logger.warning(f"Failed to extract data from comment element {idx + 1}")
                except Exception as e:
                    logger.warning(f"Failed to extract comment {idx}: {e}")
                    continue
            
            logger.info(f"Successfully crawled {len(comments)} comments from TikTok")
            
        except Exception as e:
            logger.error(f"TikTok crawl failed: {e}")
            raise
        finally:
            self.close_browser()
        
        return comments
    
    def _scroll_to_comments(self):
        """Scroll page to reveal comments section"""
        # Slower, more human-like scrolling for TikTok
        for _ in range(4):
            self.page.evaluate("window.scrollBy(0, 400)")
            random_delay(1500, 2500)  # Slower delays to avoid detection
    
    def _load_more_comments(self, max_comments: int):
        """Click 'View more comments' buttons to load additional comments"""
        attempts = 0
        max_attempts = min(max_comments // 20, 10)
        
        while attempts < max_attempts:
            try:
                # Look for "View more comments" button
                view_more = self.page.query_selector('button:has-text("View more")')
                if view_more:
                    view_more.click()
                    random_delay(2000, 3000)
                else:
                    break
            except:
                break
            
            attempts += 1
            human_like_scroll(self.page, scroll_count=2)
    
    def _extract_tiktok_comment(self, element, index: int) -> dict:
        """Extract comment data from TikTok comment element"""
        try:
            # Extract username - try multiple selectors
            username = None
            
            # First try: Extract from link href (most reliable)
            username_link = element.query_selector('[data-e2e="comment-username-1"] a, div[class*="UsernameContent"] a')
            if username_link:
                href = username_link.get_attribute('href')
                if href and href.startswith('/@'):
                    username = href[2:]  # Remove /@ prefix
            
            # Fallback: Try text-based selectors
            if not username:
                username_selectors = [
                    '[data-e2e="comment-username-1"]',
                    '[data-e2e="comment-username"]',
                    'a[data-e2e="comment-username-1"]',
                    'span[data-e2e="comment-username"]',
                    'div[class*="UsernameContent"] p',
                    'a.link-a11y-focus',
                    'span[class*="UserName"]',
                    'span[class*="username"]',
                ]
                for sel in username_selectors:
                    username_elem = element.query_selector(sel)
                    if username_elem:
                        username = username_elem.inner_text().strip()
                        if username:
                            break
            
            if not username:
                username = f"user_{index}"
            
            # Extract comment text - try multiple selectors
            text = ""
            text_selectors = [
                'span[data-e2e="comment-level-1"]',  # CORRECT: Based on HTML inspection
                'span[data-e2e="comment-level-1"] span',  # Nested span with actual text
                'span[class*="TUXText"]',  # TikTok's text component
                'span[class*="StyledText"]',  # Alternative text component
                '[data-e2e="comment-text"]',
                'p[data-e2e="comment-level-2"]',
                'span[data-e2e="comment-text-content"]',
                'p[class*="CommentText"]',
                'span[class*="comment-text"]',
                'p.comment-text',
            ]
            for sel in text_selectors:
                text_elem = element.query_selector(sel)
                if text_elem:
                    text = text_elem.inner_text().strip()
                    if text:
                        break
            
            # Extract likes count
            likes_elem = element.query_selector('[data-e2e="comment-like-count"]')
            likes_text = likes_elem.inner_text() if likes_elem else "0"
            likes = self._parse_number(likes_text)
            
            # Extract timestamp
            time_elem = element.query_selector('[data-e2e="comment-time"]')
            timestamp = time_elem.inner_text() if time_elem else None
            
            return {
                'comment_id': f"tt_{index}_{hash(text)}",
                'username': username,
                'user_id': username,
                'text': text,
                'timestamp': timestamp,
                'likes': likes,
                'replies_count': 0,
                'platform': 'tiktok'
            }
        except Exception as e:
            logger.error(f"Failed to parse TikTok comment: {e}")
            return None
    
    def _parse_number(self, text: str) -> int:
        """Parse number from text (e.g., '1.2K' -> 1200)"""
        try:
            text = text.strip().upper()
            if 'K' in text:
                return int(float(text.replace('K', '')) * 1000)
            elif 'M' in text:
                return int(float(text.replace('M', '')) * 1000000)
            else:
                return int(text)
        except:
            return 0
