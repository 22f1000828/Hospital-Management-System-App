import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
cache = Cache()

def create_app(config_class=Config):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_path = os.path.join(base_dir, 'static')
    app = Flask(__name__, static_folder=static_path, static_url_path='/static')
    app.config.from_object(config_class)
    
    if 'DATABASE_URL' not in os.environ:
        os.makedirs(app.instance_path, exist_ok=True)
        db_path = os.path.join(app.instance_path, 'hospital.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    return app

