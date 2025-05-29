from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import re
from forms import LoginForm, RegisterForm
from models import db, User, Question, QuizHistory

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Ganti dengan secret key yang aman

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def clean_question_text(text):
    # Remove any X.Y. pattern from the start of the question
    text = re.sub(r'^\d+\.\d+\.?\s*', '', text)
    text = re.sub(r'^\d+\.\s*', '', text)
    return text

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('home'))
        flash('Username atau password salah', 'error')
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username sudah digunakan', 'error')
            return render_template('auth/register.html', form=form)
        
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Registrasi berhasil! Silakan login dengan akun Anda.', 'success')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Terjadi kesalahan saat mendaftar. Silakan coba lagi.', 'error')
            return render_template('auth/register.html', form=form)
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout', 'info')
    return redirect(url_for('home'))

@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    subjects = db.session.query(Question.subject).distinct().all()
    subjects = [s[0] for s in subjects]
    return render_template('home.html', subjects=subjects)

@app.route('/quiz/<subject>', methods=['GET', 'POST'])
@login_required
def quiz(subject):
    questions = Question.query.filter_by(subject=subject).all()
    
    # Create a copy of questions for modification
    questions_for_display = []
    for q in questions:
        question_copy = {
            'id': q.id,
            'question': clean_question_text(q.question) if q.question else q.question,
            'options': json.loads(q.options),
            'answer': q.answer
        }
        questions_for_display.append(question_copy)

    if request.method == 'POST':
        user_answers = request.form
        results = []
        score = 0
        
        # Calculate time taken
        start_time = int(request.form.get('start_time', 0))
        end_time = int(request.form.get('end_time', 0))
        time_taken = (end_time - start_time) // 1000  # Convert to seconds
        
        for q in questions:
            user_answer = user_answers.get(str(q.id))
            is_correct = user_answer == q.answer
            if is_correct:
                score += 1
            results.append({
                'question': clean_question_text(q.question) if q.question else q.question,
                'user_answer': user_answer,
                'correct_answer': q.answer,
                'is_correct': is_correct,
                'options': json.loads(q.options),
                'id': q.id
            })
        
        # Save quiz history with time taken
        quiz_history = QuizHistory(
            user_id=current_user.id,
            subject=subject,
            score=score,
            total_questions=len(questions),
            time_taken=time_taken,
            answers=json.dumps(results)
        )
        db.session.add(quiz_history)
        db.session.commit()
        
        return render_template('result.html', 
                             subject=subject, 
                             results=results, 
                             score=score, 
                             total=len(questions),
                             time_taken=time_taken)

    return render_template('quiz.html', subject=subject, questions=questions_for_display)

@app.route('/history')
@login_required
def history():
    # Get user's quiz history
    quiz_history = QuizHistory.query.filter_by(user_id=current_user.id).order_by(QuizHistory.completed_at.desc()).all()
    
    # Process the history data
    history_data = []
    for quiz in quiz_history:
        history_data.append({
            'subject': quiz.subject,
            'score': quiz.score,
            'total_questions': quiz.total_questions,
            'percentage': (quiz.score / quiz.total_questions) * 100,
            'date': quiz.completed_at.strftime('%d %B %Y %H:%M'),
            'answers': json.loads(quiz.answers) if quiz.answers else []
        })
    
    return render_template('history.html', history=history_data)

@app.route('/clear_history')
@login_required
def clear_history():
    try:
        # Delete all quiz history for current user
        QuizHistory.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash('Riwayat quiz berhasil dihapus', 'success')
    except:
        db.session.rollback()
        flash('Gagal menghapus riwayat quiz', 'error')
    
    return redirect(url_for('history'))

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()

        # Seed questions
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
            },
            {
                'subject': 'Matematika',
                'question': 'Berapakah akar kuadrat dari 81?',
                'options': ['9', '8', '7', '10'],
                'answer': '9'
            },
            {
                'subject': 'Matematika',
                'question': 'Apa hasil dari 15 - 7?',
                'options': ['8', '7', '9', '6'],
                'answer': '8'
            },

            # Kimia (5 soal)
            {
                'subject': 'Kimia',
                'question': 'Apa simbol kimia untuk air?',
                'options': ['H2O', 'O2', 'CO2', 'NaCl'],
                'answer': 'H2O'
            },
            {
                'subject': 'Kimia',
                'question': 'Apa itu atom?',
                'options': ['Partikel terkecil penyusun materi', 'Molekul', 'Ion', 'Elektron'],
                'answer': 'Partikel terkecil penyusun materi'
            },
            {
                'subject': 'Kimia',
                'question': 'Apa nama unsur dengan simbol Fe?',
                'options': ['Besi', 'Emas', 'Tembaga', 'Perak'],
                'answer': 'Besi'
            },
            {
                'subject': 'Kimia',
                'question': 'Apa itu molekul?',
                'options': ['Gabungan dua atau lebih atom', 'Partikel bermuatan negatif', 'Ion positif', 'Atom tunggal'],
                'answer': 'Gabungan dua atau lebih atom'
            },
            {
                'subject': 'Kimia',
                'question': 'Apa jenis ikatan kimia pada air?',
                'options': ['Ikatan kovalen', 'Ikatan ionik', 'Ikatan logam', 'Ikatan hidrogen'],
                'answer': 'Ikatan kovalen'
            },

            # Bahasa Inggris (5 soal)
            {
                'subject': 'Bahasa Inggris',
                'question': 'What is the synonym of "happy"?',
                'options': ['Sad', 'Joyful', 'Angry', 'Tired'],
                'answer': 'Joyful'
            },
            {
                'subject': 'Bahasa Inggris',
                'question': 'What is the past tense of "go"?',
                'options': ['Went', 'Goed', 'Going', 'Gone'],
                'answer': 'Went'
            },
            {
                'subject': 'Bahasa Inggris',
                'question': 'What does "beautiful" mean?',
                'options': ['Cantik', 'Buruk', 'Besar', 'Kecil'],
                'answer': 'Cantik'
            },
            {
                'subject': 'Bahasa Inggris',
                'question': 'Choose the correct sentence:',
                'options': ['I am happy.', 'I happy.', 'Am I happy?', 'Happy I am.'],
                'answer': 'I am happy.'
            },
            {
                'subject': 'Bahasa Inggris',
                'question': 'What is the antonym of "fast"?',
                'options': ['Slow', 'Quick', 'Rapid', 'Swift'],
                'answer': 'Slow'
            },

            # Sejarah (5 soal)
            {
                'subject': 'Sejarah',
                'question': 'Siapa proklamator kemerdekaan Indonesia?',
                'options': ['Soekarno dan Hatta', 'Soeharto', 'Ahmad Yani', 'Bung Tomo'],
                'answer': 'Soekarno dan Hatta'
            },
            {
                'subject': 'Sejarah',
                'question': 'Kapan Indonesia memproklamasikan kemerdekaan?',
                'options': ['17 Agustus 1945', '1 Juni 1945', '10 November 1945', '28 Oktober 1928'],
                'answer': '17 Agustus 1945'
            },
            {
                'subject': 'Sejarah',
                'question': 'Apa nama perjanjian yang mengakhiri Perang Dunia I?',
                'options': ['Perjanjian Versailles', 'Perjanjian Paris', 'Perjanjian Tokyo', 'Perjanjian Berlin'],
                'answer': 'Perjanjian Versailles'
            },
            {
                'subject': 'Sejarah',
                'question': 'Siapa penemu benua Amerika?',
                'options': ['Christopher Columbus', 'Marco Polo', 'Vasco da Gama', 'Ferdinand Magellan'],
                'answer': 'Christopher Columbus'
            },
            {
                'subject': 'Sejarah',
                'question': 'Apa penyebab utama Perang Dunia II?',
                'options': ['Invasi Jerman ke Polandia', 'Perang Dunia I', 'Perang Dingin', 'Krisis Ekonomi'],
                'answer': 'Invasi Jerman ke Polandia'
            },

            # Geografi (5 soal)
            {
                'subject': 'Geografi',
                'question': 'Apa ibukota Indonesia?',
                'options': ['Jakarta', 'Bandung', 'Surabaya', 'Medan'],
                'answer': 'Jakarta'
            },
            {
                'subject': 'Geografi',
                'question': 'Gunung tertinggi di dunia adalah?',
                'options': ['Gunung Everest', 'Gunung Kilimanjaro', 'Gunung Fuji', 'Gunung Merapi'],
                'answer': 'Gunung Everest'
            },
            {
                'subject': 'Geografi',
                'question': 'Sungai terpanjang di dunia adalah?',
                'options': ['Sungai Nil', 'Sungai Amazon', 'Sungai Mississippi', 'Sungai Yangtze'],
                'answer': 'Sungai Nil'
            },
            {
                'subject': 'Geografi',
                'question': 'Apa nama benua tempat Indonesia berada?',
                'options': ['Asia', 'Afrika', 'Eropa', 'Australia'],
                'answer': 'Asia'
            },
            {
                'subject': 'Geografi',
                'question': 'Apa itu garis khatulistiwa?',
                'options': ['Garis imajiner yang membagi bumi menjadi belahan utara dan selatan', 'Garis batas negara', 'Garis pantai', 'Garis waktu'],
                'answer': 'Garis imajiner yang membagi bumi menjadi belahan utara dan selatan'
            },

            # Ekonomi (5 soal)
            {
                'subject': 'Ekonomi',
                'question': 'Apa itu inflasi?',
                'options': ['Kenaikan harga umum barang dan jasa', 'Penurunan nilai uang', 'Pertumbuhan ekonomi', 'Krisis moneter'],
                'answer': 'Kenaikan harga umum barang dan jasa'
            },
            {
                'subject': 'Ekonomi',
                'question': 'Apa itu permintaan?',
                'options': ['Keinginan dan kemampuan membeli barang', 'Penawaran barang', 'Harga barang', 'Pajak'],
                'answer': 'Keinginan dan kemampuan membeli barang'
            },
            {
                'subject': 'Ekonomi',
                'question': 'Apa itu pasar?',
                'options': ['Tempat bertemunya penjual dan pembeli', 'Gudang penyimpanan', 'Bank', 'Pabrik'],
                'answer': 'Tempat bertemunya penjual dan pembeli'
            },
            {
                'subject': 'Ekonomi',
                'question': 'Apa tujuan utama ekonomi?',
                'options': ['Memenuhi kebutuhan manusia', 'Menghasilkan keuntungan', 'Meningkatkan pajak', 'Mengatur pemerintah'],
                'answer': 'Memenuhi kebutuhan manusia'
            },
            {
                'subject': 'Ekonomi',
                'question': 'Apa itu biaya produksi?',
                'options': ['Biaya untuk membuat barang atau jasa', 'Harga jual barang', 'Pajak pemerintah', 'Pendapatan'],
                'answer': 'Biaya untuk membuat barang atau jasa'
            },

            # Informatika (5 soal)
            {
                'subject': 'Informatika',
                'question': 'Apa kepanjangan dari CPU?',
                'options': ['Central Processing Unit', 'Computer Power Unit', 'Control Program Unit', 'Central Power Unit'],
                'answer': 'Central Processing Unit'
            },
            {
                'subject': 'Informatika',
                'question': 'Apa bahasa pemrograman yang sering digunakan untuk web?',
                'options': ['JavaScript', 'Python', 'C++', 'Assembly'],
                'answer': 'JavaScript'
            },
            {
                'subject': 'Informatika',
                'question': 'Apa itu HTML?',
                'options': ['Bahasa markup untuk membuat halaman web', 'Bahasa pemrograman', 'Database', 'Sistem operasi'],
                'answer': 'Bahasa markup untuk membuat halaman web'
            },
            {
                'subject': 'Informatika',
                'question': 'Apa fungsi dari algoritma?',
                'options': ['Langkah-langkah penyelesaian masalah', 'Jenis hardware', 'Database', 'Bahasa pemrograman'],
                'answer': 'Langkah-langkah penyelesaian masalah'
            },
            {
                'subject': 'Informatika',
                'question': 'Apa itu variabel dalam pemrograman?',
                'options': ['Tempat menyimpan data', 'Jenis fungsi', 'Sistem operasi', 'Perangkat keras'],
                'answer': 'Tempat menyimpan data'
            }
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
    init_db()
    app.run(debug=True)
