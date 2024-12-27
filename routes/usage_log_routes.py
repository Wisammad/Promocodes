from flask import Blueprint, request, jsonify
from models import UsageLog, db

usage_log_bp = Blueprint('usage_log', __name__)

@usage_log_bp.route('/usage-logs', methods=['GET'])
def get_usage_logs():
    logs = UsageLog.query.all()
    return jsonify([{
        'id': str(l.id),
        'promo_code_id': str(l.promo_code_id),
        'user_profile_id': str(l.user_profile_id) if l.user_profile_id else None,
        'applied_at': l.applied_at.isoformat(),
        'status': l.status,
        'ip_address': l.ip_address,
        'device_id': l.device_id
    } for l in logs])

@usage_log_bp.route('/usage-logs', methods=['POST'])
def create_usage_log():
    data = request.get_json()
    new_log = UsageLog(**data)
    db.session.add(new_log)
    db.session.commit()
    return jsonify({'message': 'Usage log created successfully'}), 201 