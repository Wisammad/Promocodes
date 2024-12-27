import requests
from datetime import datetime

class PromoCodePipeline:
    def process_item(self, item, spider):
        # Validate required fields
        required_fields = ['code', 'platform', 'discount_type', 'discount_value']
        if not all(item.get(field) for field in required_fields):
            spider.logger.error(f"Missing required fields in item: {item}")
            return item

        # Format data according to your API requirements
        try:
            response = requests.post(
                "http://localhost:5000/api/promo-codes",
                json={
                    "code": item['code'],
                    "platform": item['platform'],
                    "discount_type": item['discount_type'],
                    "discount_value": float(item['discount_value']),
                    "expiration_date": item['expiration_date'],
                    "usage_limit": item['usage_limit'],
                    "location_restriction": item['location_restriction'],
                    "user_profile_restriction": item['user_profile_restriction'],
                    "revenue_share": float(item['revenue_share'])
                }
            )
            if response.status_code == 201:
                spider.logger.info(f"Successfully added promo code: {item['code']}")
            else:
                spider.logger.error(f"Failed to add promo code: {response.json()}")
        except Exception as e:
            spider.logger.error(f"Error processing item: {str(e)}")
        return item