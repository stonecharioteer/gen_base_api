from flask import (request, 
                session, abort, flash, jsonify)
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename
from expiringdict import ExpiringDict
import svnlib
from .models import User, login_user, logout_user
from .db import db as database
from .db import (app, Project, CustomField,
                CustomValue, Issue, TimeEntry, Groups_User,
                Repository, get_project_mapping_field_id)
from .db import User as dbUser

@app.route("/login", "POST")
def login():
    """Login Method."""
    username = request.form["username"]
    password = request.form["password"]
    if request.form.get("rememberme") is not None:
        rememberme = request.form.get("rememberme") == "on"
    else:
        rememberme = False
    # use svn to perform the validation
    errors = svnlib.check_svn_credentials(username, password)
    if errors.hostname_is_valid:
        if errors.username_is_valid and errors.password_is_valid:
            user = User(username)
            user_obj = database.session.query(
                dbUser).filter(dbUser.login == user.id).first()
            # check the groups.
            if user_obj is None:
                message = (
                    "There is no such user in Easy Redmine. Contact your site "
                    "administrator for assistance.")
                flash(message, "error")
                abort(401)
            else:
                user_groups = [
                    group.lastname for group in user_obj.get_groups()]
                if "Project_Admin" in user_groups:
                    login_user(user, remember=rememberme)
                    if request.args.get("next") is not None:
                        return redirect(request.args.get("next"))
                    else:
                        return redirect(url_for("index"))
                else:
                    message = (
                        "You do not have permissions to view this page. "
                        "Ask a Redmine Administrator to add you to the Project_Admin "
                        "group if you wish to use this tool.")
                    flash(message, "error")
                    abort(401)
        else:
            abort(401)
    else:
        flash("The SVN host cannot be reached. This tool uses SVN for authentication. Please contact the admin!", "error")
        abort(401)
