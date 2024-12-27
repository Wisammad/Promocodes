from flask import Blueprint, request, jsonify, abort
from models import PromoCode, UsageLog, db
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

@promo_bp.route('/promo-codes/<uuid:id>', methods=['GET'])
def get_promo_code(id):
    promo = PromoCode.query.get_or_404(id)
    return jsonify({
        'id': str(promo.id),
        'code': promo.code,
        'platform': promo.platform,
        'discount_type': promo.discount_type,
        'discount_value': float(promo.discount_value),
        'expiration_date': promo.expiration_date.isoformat(),
        'usage_limit': promo.usage_limit,
        'user_profile_restriction': promo.user_profile_restriction,
        'location_restriction': promo.location_restriction,
        'revenue_share': float(promo.revenue_share),
        'created_at': promo.created_at.isoformat(),
        'updated_at': promo.updated_at.isoformat()
    })

@promo_bp.route('/promo-codes/<uuid:id>', methods=['PUT'])
def update_promo_code(id):
    promo = PromoCode.query.get_or_404(id)
    data = request.get_json()
    
    for key, value in data.items():
        if hasattr(promo, key):
            setattr(promo, key, value)
    
    db.session.commit()
    return jsonify({'message': 'Promo code updated successfully'})

@promo_bp.route('/promo-codes/<uuid:id>', methods=['DELETE'])
def delete_promo_code(id):
    promo = PromoCode.query.get_or_404(id)
    db.session.delete(promo)
    db.session.commit()
    return jsonify({'message': 'Promo code deleted successfully'})

@promo_bp.route('/promo-codes', methods=['POST'])
def add_promo_code():
    data = request.get_json()

    # Validate required fields
    required_fields = ['code', 'platform', 'discount_type', 'discount_value', 'expiration_date', 'usage_limit']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check for duplicate promo code
    if PromoCode.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Promo code already exists'}), 400

    # Validate discount_value is numeric
    try:
        data['discount_value'] = float(data['discount_value'])
    except ValueError:
        return jsonify({'error': 'Invalid discount value'}), 400

    new_promo = PromoCode(**data)
    db.session.add(new_promo)
    db.session.commit()
    return jsonify({'message': 'Promo code added successfully'}), 201

@promo_bp.route('/apply-code', methods=['POST'])
def apply_promo_code():
    data = request.get_json()
    code = data.get('code')
    user_profile_id = data.get('user_profile_id')
    location = data.get('location')
    profile_type = data.get('profile_type')
    
    promo = PromoCode.query.filter_by(code=code).first()
    if not promo:
        return jsonify({'error': 'Invalid promo code'}), 404
        
    # Validate expiration
    if promo.expiration_date < datetime.utcnow():
        return jsonify({'error': 'Promo code has expired'}), 400
        
    # Validate usage limit
    if len(promo.usage_logs) >= promo.usage_limit:
        return jsonify({'error': 'Usage limit exceeded'}), 400
        
    # Validate location restriction
    if promo.location_restriction and location not in promo.location_restriction:
        return jsonify({'error': 'Location not eligible'}), 400

    # Validate profile restriction
    if promo.user_profile_restriction and profile_type not in promo.user_profile_restriction:
        return jsonify({'error': 'Profile type not eligible'}), 400
    
    # Create usage log
    new_log = UsageLog(
        promo_code_id=promo.id,
        user_profile_id=user_profile_id,
        status='success',
        ip_address=request.remote_addr
    )
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify({
        'message': 'Promo code applied successfully',
        'discount_type': promo.discount_type,
        'discount_value': float(promo.discount_value)
    }) 