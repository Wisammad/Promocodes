import scrapy
from datetime import datetime, timedelta
from ..items import PromoCodeItem
import random
from scrapy_selenium import SeleniumRequest

class PromoCodesSpider(scrapy.Spider):
    name = "promo_codes"
    allowed_domains = ["retailmenot.com"]
    start_urls = [
        "https://www.retailmenot.com/deals/christmas/robots.txt"
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": random.uniform(2, 5),
        "CONCURRENT_REQUESTS": 1,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        },
        "COOKIES_ENABLED": True,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        "HTTPERROR_ALLOWED_CODES": [403]  # Allow 403 to be processed
    }

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse,
                wait_time=10,
                screenshot=True,
                dont_filter=True,
                meta={
                    'dont_redirect': True,
                    'handle_httpstatus_list': [403]
                }
            )

    def parse(self, response):
        if response.status == 403:
            self.logger.error("Access Denied (403) - Website blocking our requests")
            return
        
        for promo in response.css("div.coupon"):
            code = promo.css("span.code::text").get()
            if code:
                item = PromoCodeItem()
                item['code'] = code.strip()
                item['platform'] = promo.css("span.offer-title::text").get().strip() if promo.css("span.offer-title::text").get() else None
                item['discount_type'] = self.determine_discount_type(promo)
                item['discount_value'] = self.extract_discount_value(promo)
                item['expiration_date'] = self.parse_expiration_date(promo)
                item['usage_limit'] = 100
                item['location_restriction'] = None
                item['user_profile_restriction'] = None
                item['revenue_share'] = 0.00
                yield item

    def determine_discount_type(self, promo):
        discount_text = promo.css("span.offer-title::text").get()
        return "percentage" if "%" in discount_text else "fixed"

    def extract_discount_value(self, promo):
        discount_text = promo.css("span.offer-title::text").get()
        if discount_text:
            value = ''.join(filter(str.isdigit, discount_text))
            try:
                return float(value)
            except ValueError:
                return 0.00
        return 0.00

    def parse_expiration_date(self, promo):
        date_text = promo.css("span.expiration::text").get()
        if date_text:
            try:
                return datetime.strptime(date_text.strip(), "%m/%d/%Y").isoformat()
            except ValueError:
                pass
        return (datetime.utcnow() + timedelta(days=30)).isoformat()
