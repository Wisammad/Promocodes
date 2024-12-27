# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PromoCodeItem(scrapy.Item):
    code = scrapy.Field()
    platform = scrapy.Field()
    discount_type = scrapy.Field()
    discount_value = scrapy.Field()
    expiration_date = scrapy.Field()
    usage_limit = scrapy.Field()
    location_restriction = scrapy.Field()
    user_profile_restriction = scrapy.Field()
    revenue_share = scrapy.Field()
