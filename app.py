from flask import Flask, g, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate, MigrateCommand
# from flask_restless import APIManager
from config import Configuration 


app = Flask(__name__)
app.config.from_object(Configuration)
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)
migrate = Migrate(app,db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


login_manager = LoginManager(app)
login_manager.login_view = "login"

@app.before_request
def _before_request():
    # print(current_user.name)  
    g.user = current_user

@app.before_request
def _last_page_visited():
    if "current_page" in session:
        session["last_page"] = session["current_page"]
    session["current_page"] = request.path

