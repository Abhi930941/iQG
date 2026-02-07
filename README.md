# iQGenerator - Intelligent Quiz Generation Platform

## Overview

iQGenerator is an AI-powered web application that automatically generates quiz questions from educational content. It eliminates the manual effort of creating assessments by using Natural Language Processing (NLP) to extract key concepts and generate multiple-choice questions from Wikipedia articles or uploaded PDF documents.

**Problem Statement**: Educators spend significant time manually creating quiz questions. Students lack personalized practice materials for self-assessment.

**Solution**: An automated system that generates high-quality quiz questions in seconds, complete with scoring, progress tracking, and performance analytics.

---

## Tech Stack

**Frontend**
- HTML5, CSS3, Bootstrap 
- JavaScript, jQuery 
- Chart.js (data visualization)

**Backend**
- Python 
- Flask (web framework)
- Flask-Login (authentication)
- Flask-SQLAlchemy 

**Database**
- SQLite (relational database)

**AI/ML & Data Processing**
- NLTK (Natural Language Processing)
- BeautifulSoup4 (web scraping)
- PyPDF2 (PDF processing)

---

## Key Features

### Core Functionality
- **Automatic Question Generation**: Creates fill-in-the-blank and conceptual questions using NLP
- **Multi-Source Input**: Supports Wikipedia topics and PDF document uploads
- **Intelligent Option Generation**: Auto-generates plausible distractors for multiple-choice questions
- **Real-Time Quizzing**: 10-minute timed quizzes with live progress tracking

### User Experience
- **User Authentication**: Secure registration and login system with password hashing
- **Performance Analytics**: Visual score reports with pie charts showing correct/incorrect answers
- **History Tracking**: Complete record of past quiz attempts and scores

### Educational Content
- **21 Pre-loaded Topics**: Machine Learning, AI, Neural Networks, and related subjects
- **Content Scraping**: Automatic retrieval of educational material from Wikipedia
- **Topic Navigation**: Structured learning paths with section-wise content

---

## User Roles

**Student/Learner**
- Register and create personal account
- Select topics or upload custom PDFs
- Take timed quizzes with auto-graded results
- View performance history and analytics
- Track learning progress over time

---

## System Architecture

```
User Interface (HTML/CSS/JS)
            ↓
Flask Web Server (Python)
            ↓
      ┌─────┴─────────┐
      ↓               ↓
Business Logic    Authentication
      ↓               ↓
      ↓         SQLite Database
      ↓         (Users, Results)
      ↓
NLP Pipeline
      ↓
┌─────┴──────┐
↓            ↓
Wikipedia  PDF Upload
Scraper    Parser
 ↓           ↓
Question Generator (NLTK)
```

**Data Flow**:
1. User selects topic or uploads PDF
2. System scrapes/extracts text content
3. NLP module processes text 
4. Algorithm generates questions with options
5. User takes quiz with timer
6. System evaluates answers and calculates score
7. Results stored in database and displayed visually

---


---

## Project Structure

```
iqgenerator/
│
├── app.py                      # Main Flask application
├── GenerateQuestion.py         # NLP question generation module
│
├── templates/                  # HTML templates
│   ├── index.html             # Landing page
│   ├── login.html             # Login page
│   ├── register.html          # Registration page
│   ├── home.html              # User dashboard
│   ├── TutorialList.html      # Topic selection
│   ├── TopicContent.html      # Learning content
│   ├── Questions.html         # Quiz interface
│   ├── Result.html            # Score display
│   ├── history.html           # Performance history
│   └── HowItWorks.html        # System explanation
│
├── static/                     # Static assets
│   ├── css/                   # Stylesheets
│   ├── js/                    # JavaScript files
│   ├── images/                # Images and logos
│   └── json/                  # Data files
│
└── iqgenerator.db             # SQLite database 
```

---

## Usage Guide

### For Students:
1. **Register**: Create account with username and password
2. **Login**: Access personal dashboard
3. **Select Topic**: Choose from 21 pre-loaded topics OR upload PDF
4. **Learn**: Read content section by section
5. **Take Quiz**: Attempt 10-question timed quiz (10 minutes)
6. **Review Results**: View score, correct/incorrect breakdown
7. **Track Progress**: Check history page for past performance

---

## Demo & Links

**Live Demo**: https://intelligent-question-generator.onrender.com

**Repository**: https://github.com/Abhi930941/iQG

---

## Why This Project Matters

### Problem Solved
- **For Educators**: Reduces assessment creation time from hours to seconds
- **For Students**: Provides unlimited practice material for self-paced learning
- **For Institutions**: Scalable solution for automated assessment generation

---

## Contact

**Developer**: Abhishek Sahani

**Email**: abhishek242443@gmail.com

**LinkedIn**: https://linkedin.com/in/abhishek-sahani-447851341

**GitHub**: https://github.com/Abhi930941?tab=repositories

**Portfolio**: abhi930941.github.io/Portfolio

---

## Acknowledgments

- Wikipedia API for educational content
- NLTK developers for NLP tools
- Flask and Bootstrap communities

---

**Built with passion for transforming education through technology.**
