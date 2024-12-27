from flask import Flask
from database import init_db
from routes.promo_code_routes import promo_bp
from routes.user_profile_routes import user_profile_bp
from routes.usage_log_routes import usage_log_bp
from routes.revenue_routes import revenue_bp
from routes.analytics_routes import analytics_bp
import os

app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/honey')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Register blueprints
app.register_blueprint(promo_bp, url_prefix='/api')
app.register_blueprint(user_profile_bp, url_prefix='/api')
app.register_blueprint(usage_log_bp, url_prefix='/api')
app.register_blueprint(revenue_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)