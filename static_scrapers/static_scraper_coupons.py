from static_scraper import StaticPromoScraper
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import time

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CouponsComScraper(StaticPromoScraper):
    def __init__(self, base_url="https://www.coupons.com/top-offers"):
        super().__init__(base_url)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def setup(self):
        """Initialize Playwright browser and context"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            logger.info("Playwright setup completed")
        except Exception as e:
            logger.error(f"Failed to setup Playwright: {str(e)}")
            self.cleanup()
            raise

    def cleanup(self):
        """Clean up Playwright resources"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def fetch_coupons(self):
        """Main method to fetch all coupons"""
        try:
            self.setup()
            available_codes = []
            
            # Navigate to page and wait for load
            logger.info("Navigating to page...")
            self.page.goto(self.base_url)
            self.page.wait_for_load_state('networkidle')
            time.sleep(5)
            
            # Find all voucher containers and analyze them
            vouchers = self.page.evaluate("""
                () => {
                    const results = [];
                    // Find parent containers that have the _13wrug0 class
                    document.querySelectorAll('div[class*="_13wrug0"]').forEach(container => {
                        // Get the associated data-attribute div
                        const dataDiv = container.previousElementSibling;
                        if (dataDiv && dataDiv.getAttribute('data-attribute') === 'code') {
                            const seeButton = container.querySelector('div[class*="_1fgcb8yu"]');
                            if (seeButton && seeButton.textContent.includes('See coupon')) {
                                results.push({
                                    dataId: dataDiv.getAttribute('data-id'),
                                    title: container.querySelector('h3')?.textContent?.trim() || '',
                                    shopName: container.querySelector('img')?.alt || '',
                                    buttonSelector: `div[data-id="${dataDiv.getAttribute('data-id')}"] ~ div div[class*="_1fgcb8yu"]`
                                });
                            }
                        }
                    });
                    return results;
                }
            """)
            
            logger.info(f"Found {len(vouchers)} coupon vouchers with 'See coupon' buttons")
            
            # Process each coupon
            for voucher in vouchers:
                try:
                    logger.info(f"Processing coupon for {voucher['shopName']}: {voucher['title']}")
                    
                    # Click the button
                    button = self.page.query_selector(voucher['buttonSelector'])
                    if button:
                        logger.info("Found See coupon button, clicking...")
                        button.click()
                        time.sleep(2)
                        
                        # Try to find code in modal
                        try:
                            modal = self.page.wait_for_selector("div[role='dialog']", timeout=5000)
                            if modal:
                                code = modal.text_content("[data-testid='coupon-code']")
                                if code:
                                    available_codes.append({
                                        "code": code.strip(),
                                        "shop_name": voucher['shopName'],
                                        "title": voucher['title']
                                    })
                                    logger.info(f"Found code: {code.strip()}")
                        except Exception as e:
                            logger.info(f"No modal found: {str(e)}")
                    else:
                        logger.info("Button not found")
                    
                except Exception as e:
                    logger.error(f"Error processing voucher: {str(e)}")
                    continue
            
            return available_codes
            
        except Exception as e:
            logger.error(f"Error in fetch_coupons: {str(e)}")
            logger.error("Full error:", exc_info=True)
            return []
            
        finally:
            if hasattr(self, 'cleanup'):
                self.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup() 