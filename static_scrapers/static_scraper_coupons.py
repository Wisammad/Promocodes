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
            
            # Process each coupon
            for idx, voucher in enumerate(vouchers):
                try:
                    logger.info(f"\nProcessing coupon {idx + 1} of {len(vouchers)}")
                    logger.info(f"Processing coupon for {voucher['shopName']}: {voucher['title']}")
                    
                    # Bring original page to front and ensure it's active
                    self.page.bring_to_front()
                    time.sleep(1)
                    
                    # Click the button using JavaScript to ensure it works
                    logger.info("Clicking See coupon button...")
                    clicked = self.page.evaluate("""
                        (selector) => {
                            const button = document.querySelector(selector);
                            if (button) {
                                button.click();
                                return true;
                            }
                            return false;
                        }
                    """, voucher['buttonSelector'])
                    
                    if not clicked:
                        logger.error("Failed to click button")
                        continue
                    
                    # Wait for new page
                    try:
                        with self.context.expect_page(timeout=10000) as new_page_info:
                            new_page = new_page_info.value
                            new_page.wait_for_load_state('networkidle')
                            time.sleep(2)
                            
                            logger.info(f"New page URL: {new_page.url}")
                            
                            if "coupons.com" in new_page.url:
                                logger.info("Found coupons.com page, saving HTML...")
                                
                                # Save HTML to file
                                page_html = new_page.content()
                                with open(f'debug_page_{idx}.html', 'w', encoding='utf-8') as f:
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
                                    
                                    # Close only the modal using X button
                                    close_button = new_page.query_selector('button.snc0wg0.snc0wg3.snc0wg5._1s1ejtn3')
                                    if close_button:
                                        logger.info("Found close button, clicking...")
                                        close_button.click()
                                        time.sleep(2)
                                    else:
                                        logger.info("Close button not found with class selector")
                                        close_button = new_page.query_selector('button[aria-label="close"]')
                                        if close_button:
                                            logger.info("Found close button with aria-label, clicking...")
                                            close_button.click()
                                            time.sleep(2)
                                else:
                                    logger.info("No code found in modal")
                                    
                    except Exception as e:
                        logger.error(f"Error handling new page: {str(e)}")
                        
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