from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'df9d9b8a053375dbae2758d00192748b77c1208ddd6e478c65b35e982c3c633b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    complete_lectures_ids = db.Column(db.Text, default="")
    complete_tests_ids = db.Column(db.Text, default="")
    tests_results = db.Column(db.Text, default="")
    user_lvl = db.Column(db.Integer(), default=0)
    role = db.Column(db.String(255), nullable=False, default="user")
    current_test_id = db.Column(db.Integer())
    current_question_id = db.Column(db.Integer())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"user {self.username}"


class Test(db.Model):
    __tablename__ = "test"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    lvl = db.Column(db.Integer(), default=0)
    true_answers_count = db.Column(db.Integer(), default=0)
    attempts_count = db.Column(db.Integer(), default=1)
    complete_questions_count = db.Column(db.Integer(), default=0)
    questions = db.relationship('Question', backref='author', lazy='dynamic')


class Question(db.Model):
    __tablename__ = "question"
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    possible_answers = db.Column(db.Text, default="")
    true_answer = db.Column(db.Text, default="")
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'))


class Lecture(db.Model):
    __tablename__ = "lecture"
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.Text)
    lvl = db.Column(db.Integer(), default=0)

