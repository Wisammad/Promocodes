from flask import Blueprint, request, jsonify
from models import PromoCode, db
from datetime import datetime

promo_bp = Blueprint('promo', __name__)

@promo_bp.route('/promo-codes', methods=['GET'])
def get_promo_codes():
    promos = PromoCode.query.all()
    return jsonify([{
        'id': str(p.id),
        'code': p.code,
        'platform': p.platform,
        'discount_type': p.discount_type,
        'discount_value': float(p.discount_value),
        'expiration_date': p.expiration_date.isoformat(),
        'usage_limit': p.usage_limit,
        'user_profile_restriction': p.user_profile_restriction,
        'location_restriction': p.location_restriction,
        'revenue_share': float(p.revenue_share),
        'created_at': p.created_at.isoformat(),
        'updated_at': p.updated_at.isoformat()
    } for p in promos])

@promo_bp.route('/promo-codes', methods=['POST'])
def create_promo_code():
    data = request.get_json()
    new_promo = PromoCode(**data)
    db.session.add(new_promo)
    db.session.commit()
    return jsonify({'message': 'Promo code created successfully'}), 201 