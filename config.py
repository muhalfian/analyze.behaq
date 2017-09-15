import os
import psycopg2

class Configuration(object):
    APPLICATION_DIR = os.path.dirname(os.path.realpath(__file__))
    DEBUG = True
    SECRET_KEY = 'flask is fun !'
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin_admin:action@144.217.163.204/admin_analyze'
    SQLALCHEMY_DATABASE_URI = 'postgres://ntmatfodfjdvba:4e8f3e8e656ffb6d1aff1c1e8ffc22f51ffd626c942fd49032348f7439eeb78c@ec2-54-225-88-199.compute-1.amazonaws.com/debh4u6n4ucgbi'
    # SQLALCHEMY_DATABASE_URI = 'postgres://admin_admin:admin@localhost/behaq'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    STATIC_DIR = os.path.join(APPLICATION_DIR, 'static')
    IMAGES_DIR = os.path.join(STATIC_DIR, 'images')
    