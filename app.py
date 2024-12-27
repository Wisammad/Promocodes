from flask import Flask
from database import init_db
from routes.promo_code_routes import promo_bp
from routes.application_routes import application_bp
from routes.revenue_routes import revenue_bp
import os

app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///honey.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Register blueprints
app.register_blueprint(promo_bp, url_prefix='/api')
app.register_blueprint(application_bp, url_prefix='/api')
app.register_blueprint(revenue_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True) 