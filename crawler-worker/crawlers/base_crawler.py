from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright, Browser, Page
from utils.anti_ban import get_stealth_config, setup_stealth_page, random_delay
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """Abstract base class for all platform-specific crawlers"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
    
    def initialize_browser(self):
        """Initialize Playwright browser with stealth configuration"""
        stealth_config = get_stealth_config()
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Create context with stealth settings
        context = self.browser.new_context(
            user_agent=stealth_config['user_agent'],
            viewport=stealth_config['viewport'],
            locale=stealth_config['locale'],
            timezone_id=stealth_config['timezone_id']
        )
        
        self.page = context.new_page()
        setup_stealth_page(self.page)
        
        logger.info(f"Browser initialized for {self.__class__.__name__}")
    
    def close_browser(self):
        """Close browser and cleanup"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")
    
    @abstractmethod
    def crawl(self, url: str, max_comments: int) -> list:
        """
        Abstract method to be implemented by platform-specific crawlers
        
        Args:
            url: Target URL to crawl
            max_comments: Maximum number of comments to collect
            
        Returns:
            list: List of comment dictionaries
        """
        pass
    
    def extract_comment_data(self, element) -> dict:
        """
        Extract comment data from a page element
        Override this in platform-specific implementations
        """
        return {}
    
    def wait_for_comments(self, timeout: int = 10000):
        """Wait for comment section to load"""
        random_delay(1000, 2000)
