from app import app, db
from models import Question
import json
import re

def clean_question_text(text):
    # Remove any X.Y. pattern from the start of the question
    text = re.sub(r'^\d+\.\d+\.?\s*', '', text)
    text = re.sub(r'^\d+\.\s*', '', text)
    return text

def seed_questions():
    questions = [
        # Fisika (5 soal)
        {
            'subject': 'Fisika',
            'question': 'Apa itu gaya?',
            'options': ['Kekuatan yang menyebabkan perubahan gerak', 'Suhu benda', 'Warna benda', 'Volume benda'],
            'answer': 'Kekuatan yang menyebabkan perubahan gerak'
        },
        {
            'subject': 'Fisika',
            'question': 'Satuan gaya dalam SI adalah?',
            'options': ['Newton', 'Joule', 'Watt', 'Pascal'],
            'answer': 'Newton'
        },
        {
            'subject': 'Fisika',
            'question': 'Apa hukum Newton pertama?',
            'options': ['Inersia', 'Aksi-reaksi', 'Percepatan', 'Gravitasi'],
            'answer': 'Inersia'
        },
        {
            'subject': 'Fisika',
            'question': 'Apa rumus kecepatan?',
            'options': ['Jarak / Waktu', 'Waktu / Jarak', 'Gaya / Massa', 'Massa / Gaya'],
            'answer': 'Jarak / Waktu'
        },
        {
            'subject': 'Fisika',
            'question': 'Apa itu energi kinetik?',
            'options': ['Energi gerak', 'Energi potensial', 'Energi panas', 'Energi listrik'],
            'answer': 'Energi gerak'
        },

        # Biologi (5 soal)
        {
            'subject': 'Biologi',
            'question': 'Apa fungsi akar pada tumbuhan?',
            'options': ['Menyerap air dan nutrisi', 'Tempat fotosintesis', 'Menangkap serangga', 'Menghasilkan bunga'],
            'answer': 'Menyerap air dan nutrisi'
        },
        {
            'subject': 'Biologi',
            'question': 'Organel yang berfungsi sebagai pusat pengendali sel adalah?',
            'options': ['Nukleus', 'Mitokondria', 'Ribosom', 'Kloroplas'],
            'answer': 'Nukleus'
        },
        {
            'subject': 'Biologi',
            'question': 'Proses fotosintesis terjadi di?',
            'options': ['Kloroplas', 'Mitokondria', 'Ribosom', 'Nukleus'],
            'answer': 'Kloroplas'
        },
        {
            'subject': 'Biologi',
            'question': 'Apa fungsi hemoglobin?',
            'options': ['Mengangkut oksigen', 'Menghasilkan energi', 'Mengatur suhu tubuh', 'Menghasilkan hormon'],
            'answer': 'Mengangkut oksigen'
        },
        {
            'subject': 'Biologi',
            'question': 'Unit struktural terkecil makhluk hidup adalah?',
            'options': ['Sel', 'Jaringan', 'Organ', 'Sistem organ'],
            'answer': 'Sel'
        },

        # Matematika (5 soal)
        {
            'subject': 'Matematika',
            'question': 'Berapakah hasil dari 2 + 3?',
            'options': ['4', '5', '6', '7'],
            'answer': '5'
        },
        {
            'subject': 'Matematika',
            'question': 'Berapakah hasil dari 6 × 7?',
            'options': ['42', '36', '48', '40'],
            'answer': '42'
        },
        {
            'subject': 'Matematika',
            'question': 'Apa itu bilangan prima?',
            'options': ['Bilangan yang hanya habis dibagi 1 dan dirinya sendiri', 'Bilangan genap', 'Bilangan ganjil', 'Bilangan negatif'],
            'answer': 'Bilangan yang hanya habis dibagi 1 dan dirinya sendiri'
        }
    ]

    # Hapus semua pertanyaan yang ada
    Question.query.delete()
    
    # Tambahkan pertanyaan baru
    for q in questions:
        question = Question(
            subject=q['subject'],
            question=clean_question_text(q['question']),
            options=json.dumps(q['options']),
            answer=q['answer']
        )
        db.session.add(question)
    
    db.session.commit()

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()

        # Seed questions
        questions = [
            # ... your questions ...
        ]
        
        # Add questions to database
        for q in questions:
            question = Question(
                subject=q['subject'],
                question=clean_question_text(q['question']),
                options=json.dumps(q['options']),
                answer=q['answer']
            )
            db.session.add(question)
        
        db.session.commit()
        print("Database initialized with sample questions!")

if __name__ == '__main__':
    with app.app_context():
        seed_questions() 