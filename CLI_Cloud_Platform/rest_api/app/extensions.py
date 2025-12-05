from flask_cors import CORS
from flask import Flask

cors = CORS()

def init_extensions(app):
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])