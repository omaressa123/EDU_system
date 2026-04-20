# Configuration file for the EDU System

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Standard SQLite path that works inside the EDU_system package folder
    # This is more reliable for Docker volume mapping
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or \
'sqlite:///' + os.path.join(basedir, 'instance', 'edu_system.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-fallback-12345')