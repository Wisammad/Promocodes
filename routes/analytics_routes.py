from flask import Blueprint, jsonify
from models import PromoCode, UsageLog, db
from sqlalchemy import func
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics/success-rate', methods=['GET'])
def get_success_rate():
    total_usage = UsageLog.query.count()
    successful_usage = UsageLog.query.filter_by(status='success').count()
    
    success_rate = (successful_usage / total_usage * 100) if total_usage > 0 else 0
    
    return jsonify({
        'total_usage': total_usage,
        'successful_usage': successful_usage,
        'success_rate': round(success_rate, 2)
    })

@analytics_bp.route('/analytics/trends', methods=['GET'])
def get_trends():
    # Get usage trends for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    daily_usage = db.session.query(
        func.date(UsageLog.applied_at).label('date'),
        func.count(UsageLog.id).label('count')
    ).filter(UsageLog.applied_at >= thirty_days_ago)\
     .group_by(func.date(UsageLog.applied_at))\
     .all()
    
    return jsonify([{
        'date': str(usage.date),
        'usage_count': usage.count
    } for usage in daily_usage]) 