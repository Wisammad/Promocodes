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
                    document.querySelectorAll('div[class*="_13wrug0"]').forEach(container => {
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
            
            # Process all vouchers
            for idx, voucher in enumerate(vouchers):
                try:
                    logger.info(f"\nProcessing coupon {idx + 1} of {len(vouchers)}")
                    logger.info(f"Processing coupon for {voucher['shopName']}: {voucher['title']}")
                    
                    # Track original page before opening new tab
                    original_page = self.page
                    
                    # Click the voucher button
                    with self.context.expect_page() as new_page_info:
                        button = self.page.query_selector(voucher['buttonSelector'])
                        if button:
                            button.click()
                    
                    # Get the newly opened page
                    new_page = new_page_info.value
                    new_page.wait_for_load_state('networkidle')
                    time.sleep(2)
                    
                    # Close the original page (now advertiser page)
                    logger.info("Closing advertiser page...")
                    original_page.close()
                    
                    # Check if the new page is the coupons.com page
                    if "coupons.com" in new_page.url:
                        logger.info("Found coupons.com page, closing original page...")
                        self.page.close()
                        self.page = new_page  # Update the page reference
                        coupons_page = new_page
                        
                        # Save initial coupons.com page HTML for debugging
                        page_html = new_page.content()
                        with open(f'debug_coupons_initial_page_{idx}.html', 'w', encoding='utf-8') as f:
                            f.write(page_html)
                        
                        # Look for code in the modal
                        code = new_page.evaluate("""
                            () => {
                                const codeSelectors = [
                                    '.b8qpi79',
                                    'div[role="dialog"] .az57m46',
                                    'span[class*="b8qpi77"] h4'
                                ];
                                
                                for (const selector of codeSelectors) {
                                    const element = document.querySelector(selector);
                                    if (element && element.textContent.trim()) {
                                        return element.textContent.trim();
                                    }
                                }
                                return null;
                            }
                        """)
                        
                        if code:
                            logger.info(f"Found code: {code}")
                            available_codes.append({
                                "code": code,
                                "shop_name": voucher['shopName'],
                                "title": voucher['title']
                            })
                            
                            # Close modal using X button
                            close_button = new_page.query_selector('button.snc0wg0.snc0wg3.snc0wg5._1s1ejtn3')
                            if close_button:
                                logger.info("Found close button, clicking...")
                                try:
                                    close_button.click()
                                    logger.info("Close button clicked successfully")
                                    time.sleep(2)
                                    
                                    # Verify page state after modal close
                                    logger.info("Checking page state after modal close...")
                                    logger.info(f"Current URL: {new_page.url}")
                                    
                                    # Check if page is still active
                                    try:
                                        is_closed = new_page.evaluate("() => document.hidden")
                                        logger.info(f"Page hidden state: {is_closed}")
                                    except Exception as e:
                                        logger.error(f"Error checking page state: {str(e)}")
                                    
                                    # Try to find main page elements
                                    try:
                                        buttons = new_page.query_selector_all('div[class*="_1fgcb8yu"]')
                                        logger.info(f"Found {len(buttons)} voucher buttons after modal close")
                                    except Exception as e:
                                        logger.error(f"Error finding voucher buttons: {str(e)}")
                                        
                                    # Wait for any animations
                                    time.sleep(2)
                                    logger.info("Completed waiting after modal close")
                                    
                                except Exception as e:
                                    logger.error(f"Error during modal close: {str(e)}")
                                    logger.info("Attempting to use Escape key as fallback")
                                    try:
                                        new_page.keyboard.press('Escape')
                                        time.sleep(2)
                                        logger.info("Escape key pressed successfully")
                                    except Exception as e:
                                        logger.error(f"Error pressing Escape key: {str(e)}")
                            else:
                                logger.info("Close button not found, trying Escape key")
                                try:
                                    new_page.keyboard.press('Escape')
                                    time.sleep(2)
                                    logger.info("Escape key pressed successfully")
                                except Exception as e:
                                    logger.error(f"Error pressing Escape key: {str(e)}")
                            
                            # Ensure voucher buttons are visible again
                            new_page.wait_for_selector('div[class*="_1fgcb8yu"]', timeout=5000)
                        else:
                            logger.error("New page does not contain coupons.com URL, skipping")
                        
                        new_page.close()  # Close the new page after processing
                    else:
                        logger.error("New page is not the expected coupons.com page; skipping")
                        new_page.close()
                    
                except Exception as e:
                    logger.error(f"Error processing voucher: {str(e)}")
                    logger.error("Full error details:", exc_info=True)
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