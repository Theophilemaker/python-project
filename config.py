import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'theophile_pos'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Company defaults
    COMPANY_NAME = 'Theophile POS'
    COMPANY_TAGLINE = 'Complete Point of Sale Solution'
    COMPANY_ADDRESS = 'KG 123 St, Kigali, Rwanda'
    COMPANY_PHONE = '+250 788 123 456'
    COMPANY_EMAIL = 'info@theophile.com'
    COMPANY_WEBSITE = 'www.theophile.com'
    COMPANY_TAX_NUMBER = 'TAX123456789'
    
    # Tax settings
    DEFAULT_TAX_RATE = 18.00
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Session timeout (in seconds)
    SESSION_TIMEOUT = 3600  # 1 hour