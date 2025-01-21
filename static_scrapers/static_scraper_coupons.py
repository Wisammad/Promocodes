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
            
            # Click first coupon and get the coupons.com page
            if vouchers:
                logger.info("\nProcessing first coupon to get coupons.com page")
                with self.context.expect_page() as new_page_info:
                    button = self.page.query_selector(vouchers[0]['buttonSelector'])
                    if button:
                        button.click()
                        
                new_page = new_page_info.value
                new_page.wait_for_load_state('networkidle')
                time.sleep(2)
                
                if "coupons.com" in new_page.url:
                    logger.info("Found coupons.com page, closing original page...")
                    self.page.close()  # Close the original page (now advertiser)
                    coupons_page = new_page  # This is our main page now
                    
                    # Save initial coupons.com page HTML for debugging
                    page_html = coupons_page.content()
                    with open('debug_coupons_initial_page.html', 'w', encoding='utf-8') as f:
                        f.write(page_html)
                    
                    # Process all vouchers on the coupons.com page
                    for idx, voucher in enumerate(vouchers):
                        try:
                            logger.info(f"\nProcessing coupon {idx + 1} of {len(vouchers)}")
                            logger.info(f"Processing coupon for {voucher['shopName']}: {voucher['title']}")
                            
                            if idx > 0:  # Skip first voucher as we already processed it
                                # Save HTML before clicking for debugging
                                before_click_html = coupons_page.content()
                                with open(f'debug_before_click_{idx}.html', 'w', encoding='utf-8') as f:
                                    f.write(before_click_html)
                                
                                # Get fresh buttons from current page
                                buttons = coupons_page.evaluate("""
                                    () => {
                                        const buttons = [];
                                        document.querySelectorAll('div[class*="_1fgcb8yu"]').forEach(button => {
                                            if (button.textContent.includes('See coupon')) {
                                                buttons.push(button.outerHTML);
                                            }
                                        });
                                        return buttons;
                                    }
                                """)
                                logger.info(f"Found {len(buttons)} 'See coupon' buttons on current page")
                                
                                # Click the button using JavaScript
                                logger.info("Clicking See coupon button...")
                                clicked = coupons_page.evaluate("""
                                    () => {
                                        const buttons = document.querySelectorAll('div[class*="_1fgcb8yu"]');
                                        for (const button of buttons) {
                                            if (button.textContent.includes('See coupon')) {
                                                button.click();
                                                return true;
                                            }
                                        }
                                        return false;
                                    }
                                """)
                                
                                if not clicked:
                                    logger.error("Failed to click button")
                                    continue
                                
                                time.sleep(2)  # Wait for modal
                                
                                # Save HTML after clicking for debugging
                                after_click_html = coupons_page.content()
                                with open(f'debug_after_click_{idx}.html', 'w', encoding='utf-8') as f:
                                    f.write(after_click_html)
                            
                            # Look for code in the modal
                            code = coupons_page.evaluate("""
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
                                close_button = coupons_page.query_selector('button.snc0wg0.snc0wg3.snc0wg5._1s1ejtn3')
                                if close_button:
                                    logger.info("Found close button, clicking...")
                                    close_button.click()
                                    time.sleep(2)
                                else:
                                    logger.info("Close button not found with class selector")
                                    close_button = coupons_page.query_selector('button[aria-label="close"]')
                                    if close_button:
                                        logger.info("Found close button with aria-label, clicking...")
                                        close_button.click()
                                        time.sleep(2)
                            else:
                                logger.info("No code found in modal")
                                
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