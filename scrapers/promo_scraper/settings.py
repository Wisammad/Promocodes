import random
BOT_NAME = 'promo_scraper'

SPIDER_MODULES = ['promo_scraper.spiders']
NEWSPIDER_MODULE = 'promo_scraper.spiders'

# Browser-like settings
COOKIES_ENABLED = True
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = random.uniform(2, 5)
RANDOMIZE_DOWNLOAD_DELAY = True

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 403, 429]

# Headers and middleware
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 500,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

# Modern browser User-Agent
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Configure item pipelines
ITEM_PIPELINES = {
    'promo_scraper.pipelines.PromoCodePipeline': 300,
}

SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = '/path/to/chromedriver'  # Update with your path
SELENIUM_DRIVER_ARGUMENTS = ['--headless']  # '--headless' if using headless mode