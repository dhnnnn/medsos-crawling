import random
import time
from typing import List

# List of user agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_random_user_agent() -> str:
    """Returns a random user agent from the list"""
    return random.choice(USER_AGENTS)

def random_delay(min_ms: int = 1000, max_ms: int = 3000):
    """Sleep for a random duration between min_ms and max_ms milliseconds"""
    delay_seconds = random.uniform(min_ms / 1000, max_ms / 1000)
    time.sleep(delay_seconds)

def human_like_scroll(page, scroll_count: int = 3):
    """Simulate human-like scrolling behavior"""
    for _ in range(scroll_count):
        # Random scroll amount
        scroll_amount = random.randint(300, 800)
        page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        
        # Random delay between scrolls
        random_delay(500, 1500)

def get_stealth_config() -> dict:
    """Returns Playwright stealth configuration"""
    return {
        'user_agent': get_random_user_agent(),
        'viewport': {
            'width': random.choice([1920, 1366, 1536]),
            'height': random.choice([1080, 768, 864])
        },
        'locale': 'en-US',
        'timezone_id': 'America/New_York',
        'geolocation': None,
        'permissions': []
    }

def setup_stealth_page(page):
    """Apply stealth techniques to a Playwright page"""
    # Hide webdriver property
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    # Mock plugins
    page.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
    """)
    
    # Mock languages
    page.add_init_script("""
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """)
    
    return page

class ProxyRotator:
    """Simple proxy rotation manager"""
    
    def __init__(self, proxy_list: List[str] = None):
        self.proxies = proxy_list or []
        self.current_index = 0
    
    def get_next_proxy(self) -> str:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def add_proxy(self, proxy: str):
        """Add a new proxy to the rotation"""
        self.proxies.append(proxy)
