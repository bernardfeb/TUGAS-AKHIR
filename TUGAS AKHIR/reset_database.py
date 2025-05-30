from app import app, db, reset_db
import os
if os.path.exists('quiz.db'):
    os.remove('quiz.db')

with app.app_context():
    reset_db() 