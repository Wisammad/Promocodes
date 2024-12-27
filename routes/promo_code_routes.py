from flask import Blueprint, request, jsonify
from models import PromoCode, db

promo_bp = Blueprint('promo', __name__)

@promo_bp.route('/promo-codes', methods=['GET'])
def get_promo_codes():
    promos = PromoCode.query.all()
    return jsonify([{
        'id': p.id,
        'code': p.code,
        'discount_percentage': p.discount_percentage,
        'valid_until': p.valid_until,
        'is_active': p.is_active
    } for p in promos])

@promo_bp.route('/promo-codes', methods=['POST'])
def create_promo_code():
    data = request.get_json()
    new_promo = PromoCode(**data)
    db.session.add(new_promo)
    db.session.commit()
    return jsonify({'message': 'Promo code created successfully'}), 201 