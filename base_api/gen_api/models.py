from flask_login import UserMixin, AnonymousUserMixin, login_user, logout_user

class User(UserMixin):
    """Default class for the User class object required by flask_login.
    Read the flask_login docs for more info."""
    def __init__(self, username, *args, **kwargs):
        self.id = username
        if "." in username:
            self.name = username.replace("."," ").title()
        else:
            self.name = username


class AnonymousUser(AnonymousUserMixin):
    def __init__(self, *args, **kwargs):
        super(AnonymousUser, self).__init__(*args, **kwargs)
