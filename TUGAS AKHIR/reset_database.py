from app import app, db, reset_db
import os

# Delete existing database
if os.path.exists('quiz.db'):
    os.remove('quiz.db')

# Create new database
with app.app_context():
    reset_db() 