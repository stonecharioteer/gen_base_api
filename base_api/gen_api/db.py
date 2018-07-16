"""
db.py
This file contains all the database relevant methods and objects.

"""
import os
from flask_sqlalchemy import SQLAlchemy
from .gen_api import app

db = SQLAlchemy(app)


class User(db.Model):
    """Class for the users table."""
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(255), unique=True, nullable=False)
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    type = db.column(db.String(255))
    groups = db.relationship(
        "Groups_User", primaryjoin="Groups_User.user_id == User.id")

    def __repr__(self):
        return "<User : {}, {} [{}:{}]>".format(self.lastname, self.firstname, self.id, self.login)

    def get_time_entries(self):
        return db.session.query(TimeEntry).filter(TimeEntry.user_id == self.id).all()
    
    def get_svn_password(self):
        """This is probably unsafe."""
        return db.session.query(CustomValue).filter(
            CustomValue.customized_type == "Principal").filter(
                CustomValue.custom_field_id == get_svn_password_field_id()).filter(
                    CustomValue.customized_id == self.id).first().value

    def get_groups(self):
        return [group.group for group in self.groups]


class Groups_User(db.Model):
    __tablename__ = "groups_users"
    group_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    group = db.relationship("User", foreign_keys=group_id)
    user = db.relationship("User", foreign_keys=user_id)

    def __repr__(self):
        return "<Groups_User : {} : {}>".format(self.group.lastname, self.user.login)

class CustomField(db.Model):
    __tablename__ = "custom_fields"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    def __repr__(self):
        return "<CustomField {} : {}: [{}]>".format(self.type, self.name, self.id)

class CustomValue(db.Model):
    __tablename__ = "custom_values"
    id = db.Column(db.Integer, primary_key=True)
    customized_type = db.Column(db.String(30), nullable=False)
    # key of the project / Issue etc
    customized_id = db.Column(db.Integer, nullable=False)
    custom_field_id = db.Column(db.Integer, db.ForeignKey("custom_fields.id"))
    custom_field = db.relationship("CustomField")
    value = db.Column(db.Text)

    def __repr__(self):
        return "<Custom Value : {}: {} : [{}]>".format(
            self.custom_field.name, repr(self.value), self.id)

class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    easy_is_easy_template = db.Column(db.Integer)
    children = db.relationship("Project", 
                backref=db.backref('parent', remote_side=[id]))
    issues = db.relationship(
        "Issue", primaryjoin="Issue.project_id == Project.id")
    
    def __repr__(self):
        return '<Project : {} : [{}]>'.format(self.name, self.id)

    def get_custom_mappings(self):
        return db.session.query(CustomValue).filter(
            CustomValue.customized_type == "Project",
            CustomValue.customized_id == self.id).all()

    def get_time_entries(self):
        return db.session.query(TimeEntry).filter(TimeEntry.project_id == self.id).all()
    
    def get_local_mapping(self):
        local_mapping_field_id = get_project_mapping_field_id()
        mappings = db.session.query(CustomValue).filter(
            CustomValue.custom_field_id == local_mapping_field_id,
            CustomValue.customized_id == self.id).all()
        if len(mappings) == 0:
            mappings = []
        else:
            # mappings = ",".join([custom_value_mapping.value.replace("\r\n",",") for custom_value_mapping in mappings])
            mappings = [custom_value_mapping.value.split(
                "\r\n") for custom_value_mapping in mappings]
            mappings = [
                mapping for mappings_list in mappings for mapping in mappings_list if mapping != ""]
        # TODO: Instead of a list, return an SQL Alchemy object and have the app do the splitting however.
        return mappings
    
    def get_repositories(self):
        repositories = db.session.query(Repository).filter(
            Repository.project_id == self.id).all()
        repositories = [repo.url for repo in repositories]
        return repositories


class Issue(db.Model):
    __tablename__ = "issues"
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    project = db.relationship("Project")
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    assignee = db.relationship("User", foreign_keys=assigned_to_id)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = db.relationship("User", foreign_keys=author_id)
    created_on = db.Column(db.DateTime)
    updated_on = db.Column(db.DateTime)
    start_date = db.Column(db.Date)
    parent_id = db.Column(db.Integer, db.ForeignKey("issues.id"))
    children = db.relationship("Issue",
                                backref=db.backref('parent', remote_side=[id])
                                )

    def __repr__(self):
        return "<Issue/Task : {} : [{}]>".format(self.id, self.subject)

    def get_custom_mappings(self):
        return db.session.query(CustomValue).filter(
            CustomValue.customized_type == "Issue", CustomValue.customized_id == self.id).all()

    def get_time_entries(self):
        return db.session.query(TimeEntry).filter(TimeEntry.issue_id == self.id).all()


class TimeEntry(db.Model):
    __tablename__ = "time_entries"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey(
        "projects.id"), nullable=False)
    project = db.relationship("Project", foreign_keys=project_id)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", foreign_keys=user_id)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"))
    issue = db.relationship("Issue", foreign_keys=issue_id)
    hours = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text)
    spent_on = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return ("<Time Entry : {} : {} "
            ": {} : {} : {}>").format(self.project_id,
                self.spent_on, self.user.login,
                self.project.name,
                self.issue.subject if self.issue is not None else None)

class Repository(db.Model):
    __tablename__ = "repositories"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    login = db.Column(db.String(60))
    password = db.Column(db.String(255))
    type = db.Column(db.String(255))
    is_default = db.Column(db.Integer, nullable=False, default=0)
    identifier = db.Column(db.String(255), nullable=False, default="svn")
    root_url = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return "<Repository : {} : {}>".format(self.project_id, self.url)

def get_project_mapping_field_id():
    custom_field = db.session.query(CustomField).filter(
        CustomField.type == "ProjectCustomField",
        CustomField.name == "Local Project Mapping").first()
    return custom_field.id

def get_svn_password_field_id():
    """Returns the ID of the field that corresponds to the SVN Password."""
    custom_field = db.session.query(CustomField).filter(
        CustomField.type == "UserCustomField", 
        CustomField.name == "SVN Password").first()
    return custom_field.id
