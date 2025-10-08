from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import os
import io
import re
import json
import requests
from bs4 import BeautifulSoup
from random import shuffle
from werkzeug.utils import secure_filename
import PyPDF2

# Optional local import
try:
    import GenerateQuestion as GenQ
except Exception as e:
    GenQ = None

############################################################
# Flask + DB setup
############################################################
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iqgenerator.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_change_in_production'

# File upload config
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'mark')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Initialize DB
db = SQLAlchemy(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

############################################################
# Models
############################################################
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    
    # Relationship with QuizResult
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True, cascade='all, delete-orphan')

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(200))
    correct = db.Column(db.Integer)
    wrong = db.Column(db.Integer)
    score = db.Column(db.Float)
    
    # Foreign key to link with User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Database initialization
def init_database():
    """Initialize database with proper schema"""
    try:
        with app.app_context():
            db.create_all()
            print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization error: {e}")

# Initialize database
init_database()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

############################################################
# Routes - Auth
############################################################
@app.route('/')
def index():
    """Landing page for non-authenticated users"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validation
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('register'))
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'danger')
            return redirect(url_for('register'))
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists! Please choose a different one.', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'danger')
            return redirect(url_for('register'))
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validation
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return redirect(url_for('login'))
            
        try:
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password. Please try again.', 'danger')
        except Exception as e:
            print(f"Login error: {e}")
            flash('Login failed. Please try again.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

############################################################
# Routes - App pages
############################################################
@app.route('/home')
@login_required
def home():
    """Main home page after login - using original design"""
    try:
        # Only show quiz results for current user, limit to 5 most recent
        results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.id.desc()).limit(5).all()
        return render_template('home.html', title='iQGenerator - Home', results=results)
    except Exception as e:
        print(f"Home page error: {e}")
        return render_template('home.html', title='iQGenerator - Home', results=[])

@app.route('/HowItWorks')
@login_required
def HowItWorks():
    return render_template('HowItWorks.html', title='iQGenerator - How It Works')

@app.route('/History')
@login_required
def history():
    try:
        # Only show quiz results for current user
        results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.id.desc()).all()
        return render_template('history.html', title='Your Score History', results=results)
    except Exception as e:
        print(f"History page error: {e}")
        return render_template('history.html', title='Your Score History', results=[])

############################################################
# Tutorial list + Wiki topic content
############################################################
@app.route('/TutorialList', methods=['GET'])
@login_required
def TutorialList():
    try:
        data = readTutorialListJson()
    except Exception:
        data = []
    return render_template('TutorialList.html', title='iQGenerator - TutorialList', posts=data)

@app.route('/TopicContent/<topic_id>', methods=['GET'])
@login_required
def TopicContent(topic_id: str):
    try:
        data = {
            'Id': (topic_id.replace('_', ' ')).title(),
            'sample_text': wiki_scrape_sections(topic_id),
        }
        return render_template('TopicContent.html', title='iQGenerator - Topic', message=data)
    except Exception:
        flash('Could not load topic from Wikipedia.', 'warning')
        return redirect(url_for('TutorialList'))

############################################################
# Core - Question generation from Wikipedia
############################################################
WIKI_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@app.route('/Questions/<topic_name>')
@login_required
def Questions(topic_name: str):
    try:
        wiki_url = 'https://en.wikipedia.org/wiki/' + topic_name.replace(' ', '_')
        r = requests.get(wiki_url, headers=WIKI_HEADERS, timeout=30)
        r.raise_for_status()
        parsed = BeautifulSoup(r.text, 'html.parser')
        sample_text = ''.join([p.get_text(' ', strip=True) for p in parsed.find_all('p')])
        
        if not sample_text.strip():
            flash('No readable content found on the Wikipedia page.', 'warning')
            return redirect(url_for('TopicContent', topic_id=topic_name))
            
        questions = generate_questions(sample_text)
        if not questions:
            flash('Question generation failed. Showing topic content instead.', 'warning')
            return redirect(url_for('TopicContent', topic_id=topic_name))
            
        # Save for result page
        session['last_topic'] = topic_name
        _store_scraped_questions(questions)
        return render_template('Questions.html', title='iQGenerator - Quiz', posts=questions)
        
    except Exception as e:
        print('Question generation error (Wikipedia):', e)
        flash('Error generating questions from Wikipedia.', 'danger')
        return redirect(url_for('TopicContent', topic_id=topic_name))

############################################################
# Core - Question generation from uploaded PDF
############################################################
ALLOWED_EXTENSIONS = {'.pdf'}

def _allowed_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET'])
@login_required
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['POST'])
@login_required
def uploadfile():
    if 'file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('upload_file'))

    f = request.files['file']
    if not f or f.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('upload_file'))

    if not _allowed_file(f.filename):
        flash('Only PDF files are supported.', 'danger')
        return redirect(url_for('upload_file'))

    filename = secure_filename(f.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        f.save(file_path)
        with open(file_path, 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    # Extract text
    sample_text = ''
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            text = page.extract_text() or ''
            sample_text += text + ' '
    except Exception as e:
        print('PDF processing error:', e)
        flash('Could not extract text from the PDF.', 'danger')
        return redirect(url_for('upload_file'))

    if not sample_text.strip():
        flash('No text extracted from the PDF.', 'warning')
        return redirect(url_for('upload_file'))

    try:
        questions = generate_questions(sample_text)
    except Exception as e:
        print('Question generation error (PDF):', e)
        questions = []

    if not questions:
        flash('Question generation failed for this PDF.', 'danger')
        return redirect(url_for('upload_file'))

    session['last_topic'] = filename or 'Uploaded PDF'
    _store_scraped_questions(questions)
    return render_template('Questions.html', title='iQGenerator - Quiz', posts=questions)

############################################################
# Results
############################################################
scraped_questionSet = []

def _store_scraped_questions(data):
    global scraped_questionSet
    for q in data:
        if isinstance(q, dict) and 'Options' in q and isinstance(q['Options'], list):
            shuffle(q['Options'])
    scraped_questionSet = data

@app.route('/Result/<data>')
@login_required
def Result(data: str):
    global scraped_questionSet
    if not scraped_questionSet:
        flash('No quiz data found. Please generate questions first.', 'warning')
        return redirect(url_for('home'))

    chosen = data.split(',') if data else []
    actual = [q.get('Answer') for q in scraped_questionSet]
    correct = sum(1 for a, b in zip(chosen, actual) if a == b)
    total = len(actual) or 1

    result = {
        'NOQuestions': len(actual),
        'correctAns': correct,
        'worngAns': len(actual) - correct,
        'score': round(correct / total * 100, 2),
    }

    topic = session.get('last_topic', 'Sample Topic')
    
    try:
        quiz_result = QuizResult(
            topic=topic, 
            correct=result['correctAns'], 
            wrong=result['worngAns'], 
            score=result['score'],
            user_id=current_user.id
        )
        db.session.add(quiz_result)
        db.session.commit()
        print(f"Quiz result saved for user {current_user.username}")
    except Exception as e:
        print(f"Error saving quiz result: {e}")
        db.session.rollback()
        flash('Result saved locally but not in history due to technical issue.', 'warning')

    return render_template('Result.html', title='iQGenerator - Result', result=result)

############################################################
# Utilities
############################################################
def readTutorialListJson():
    """Read/seed static json for TutorialList."""
    site_root = os.path.realpath(os.path.dirname(__file__))
    json_path = os.path.join(site_root, 'static', 'json', 'tutorialList.json')
    if not os.path.exists(json_path):
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        default_data = {
            "Topics": [
                {"Id": 1, "TopicName": "Linear Regression"},
                {"Id": 2, "TopicName": "Artificial Intelligence"},
                {"Id": 3, "TopicName": "Machine Learning"},
                {"Id": 4, "TopicName": "K-nearest neighbors algorithm"},
                {"Id": 5, "TopicName": "Supervised learning"},
                {"Id": 6, "TopicName": "Unsupervised learning"},
                {"Id": 7, "TopicName": "Reinforcement Learning"},
                {"Id": 8, "TopicName": "Logistic regression"},
                {"Id": 9, "TopicName": "Decision Tree"},
                {"Id": 10, "TopicName": "Naive Bayes classifier"},
                {"Id": 11, "TopicName": "K-means clustering"},
                {"Id": 12, "TopicName": "Random Forest"},
                {"Id": 13, "TopicName": "Dimensionality reduction"},
                {"Id": 14, "TopicName": "Gradient boosting"},
                {"Id": 15, "TopicName": "Convolutional neural network"},
                {"Id": 16, "TopicName": "Recurrent Neural Network"},
                {"Id": 17, "TopicName": "Gradient Descent"},
                {"Id": 18, "TopicName": "Artificial Neural Network"},
                {"Id": 19, "TopicName": "Long short-term memory"},
                {"Id": 20, "TopicName": "Generative adversarial network"},
                {"Id": 21, "TopicName": "Support Vector Machine"}
            ]
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2)
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('Topics', [])

def wiki_scrape_sections(page_id: str):
    """Return a list of section dictionaries from a Wikipedia page."""
    try:
        url = 'https://en.wikipedia.org/wiki/' + page_id
        r = requests.get(url, headers=WIKI_HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        mw_body = soup.find(class_='mw-body')
        if not mw_body:
            raise RuntimeError('Wikipedia content not found')
        contents = mw_body.find_all(['p', 'h2', 'h3'])
        lst, contentwrapper = [], []
        topicName = 'Home'
        for c in contents:
            tag = c.name.lower() if hasattr(c, 'name') else ''
            if tag in ['p', 'h3']:
                para = re.sub(r'\[[0-9]*\]|\n|\[[a-z_ ]*\]|.*?\{(.*?)\}', '', c.get_text())
                lst.append({"type": "P" if tag == 'p' else 'h3', "text": para})
            if tag == 'h2' and c.get_text(strip=True) != 'Contents':
                contentwrapper.append({"TopicName": topicName, "Content": lst})
                topicName = re.sub(r'\[[a-z]*\]', '', c.get_text())
                lst = []
        if lst:
            contentwrapper.append({"TopicName": topicName, "Content": lst})
        outlist = [cont for cont in contentwrapper if len(str(cont)) > 400]
        if outlist:
            return outlist
    except Exception as e:
        print(f"Wikipedia scraping error: {e}")
        pass

    topic_name = page_id.replace('_', ' ').title()
    return [{
        "TopicName": "Introduction",
        "Content": [
            {"type": "P", "text": f"Learn about {topic_name} and explore its key concepts."},
            {"type": "P", "text": f"{topic_name} is an important topic for general knowledge."},
        ],
    }]

def generate_questions(sample_text: str):
    """Use GenQ.Aqua to generate quiz questions with fallback handling."""
    if not GenQ or not hasattr(GenQ, 'Aqua'):
        # Fallback questions if GenerateQuestion is not available
        return [
            {
                "Question": "What is the primary purpose of machine learning?",
                "Options": ["Data analysis", "Web development", "Game development", "Hardware design"],
                "Answer": "Data analysis"
            },
            {
                "Question": "Which algorithm is commonly used for classification?",
                "Options": ["K-means", "Linear Regression", "Decision Tree", "Apriori"],
                "Answer": "Decision Tree"
            },
            {
                "Question": "What does AI stand for?",
                "Options": ["Artificial Intelligence", "Automated Input", "Advanced Interface", "Algorithmic Integration"],
                "Answer": "Artificial Intelligence"
            },
            {
                "Question": "Which type of learning uses labeled data?",
                "Options": ["Supervised Learning", "Unsupervised Learning", "Reinforcement Learning", "Semi-supervised Learning"],
                "Answer": "Supervised Learning"
            },
            {
                "Question": "What is the main goal of deep learning?",
                "Options": ["Pattern recognition", "Data storage", "Network security", "File management"],
                "Answer": "Pattern recognition"
            }
        ]

    try:
        aqua = GenQ.Aqua(sample_text)
        json_payload = aqua.finalQuestions()

        try:
            data = json.loads(json_payload)
            quiz = data.get('quiz', []) if isinstance(data, dict) else []
        except Exception:
            quiz = []

        if not quiz and hasattr(aqua, 'generate_fallback_questions'):
            try:
                quiz = aqua.generate_fallback_questions() or []
            except Exception:
                quiz = []

        shuffle(quiz)
        for q in quiz:
            if isinstance(q, dict) and 'Options' in q and isinstance(q['Options'], list):
                shuffle(q['Options'])
        return quiz
        
    except Exception as e:
        print(f"Question generation error: {e}")
        # Return fallback questions
        return [
            {
                "Question": "What is machine learning?",
                "Options": ["A type of AI", "A programming language", "A database system", "A hardware component"],
                "Answer": "A type of AI"
            },
            {
                "Question": "Which library is commonly used for machine learning in Python?",
                "Options": ["TensorFlow", "Django", "React", "Spring"],
                "Answer": "TensorFlow"
            }
        ]

############################################################
# Main
############################################################
if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
            print("=" * 50)
            print("iQGenerator Application Starting...")
            print("Database: Ready")
            print("Static Files: Ready") 
            print("Routes: Configured")
            print("=" * 50)
    except Exception as e:
        print(f"Startup database check failed: {e}")
    
    # Run the application
    app.run(debug=True)