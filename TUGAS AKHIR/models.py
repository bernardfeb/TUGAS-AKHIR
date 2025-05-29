from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='student')  # 'student' atau 'teacher'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    quiz_histories = db.relationship('QuizHistory', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)  # JSON string
    answer = db.Column(db.String(200), nullable=False)
    explanation = db.Column(db.Text)  # Penjelasan jawaban
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuizHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    time_taken = db.Column(db.Integer)  # dalam detik
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.Column(db.Text)  # JSON string menyimpan jawaban user

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(50), nullable=False)
