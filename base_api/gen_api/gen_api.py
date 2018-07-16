from flask import Flask
from flask_login import LoginManager
from .models import User, AnonymousUser
from .reverseproxy import ReverseProxied

app = Flask(__name__, instance_relative_config=True)
app.wsgi_app = ReverseProxied(app.wsgi_app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@login_manager.user_loader
def load_user(userid):
    """callback to reload the user object"""
    return User(userid)

# Load the default configuration
app.config.from_object('config.default')
app.config.from_object('config.development')
# Load the configuration from the instance folder
app.config.from_pyfile('config.py')
