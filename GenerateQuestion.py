import json
import re
import random
import requests
from typing import List, Dict, Any
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag

# Try to download required NLTK data, but don't fail if not available
try:
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    NLTK_AVAILABLE = True
except:
    NLTK_AVAILABLE = False


class Aqua:
    """
    Question generator class
    """

    def __init__(self, text: str):
        self.text = text if text else ""
        self.sentences = []
        self.questions = []
        self.stopwords_set = set(
            ['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
             'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be',
             'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did']
        )

        if NLTK_AVAILABLE:
            try:
                self.stopwords_set.update(stopwords.words('english'))
            except:
                pass

        self.preprocess_text()

    def preprocess_text(self):
        """Clean and split text into meaningful sentences"""
        if not self.text:
            return

        cleaned_text = self.text
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\[[0-9]+\]', '', cleaned_text)
        cleaned_text = re.sub(r'\[[a-z_ ]*\]', '', cleaned_text)
        cleaned_text = cleaned_text.strip()

        if NLTK_AVAILABLE:
            try:
                sentences = sent_tokenize(cleaned_text)
            except:
                sentences = self.simple_sentence_split(cleaned_text)
        else:
            sentences = self.simple_sentence_split(cleaned_text)

        self.sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (30 <= len(sentence) <= 400 and 
                not sentence.startswith('See also') and
                not sentence.startswith('External links') and
                '=' not in sentence and
                sentence.count('.') <= 3):
                self.sentences.append(sentence)

    def simple_sentence_split(self, text: str) -> List[str]:
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def extract_key_terms(self, sentence: str) -> List[str]:
        key_terms = []
        if NLTK_AVAILABLE:
            try:
                words = word_tokenize(sentence)
                pos_tags = pos_tag(words)
                for word, pos in pos_tags:
                    word_clean = re.sub(r'[^\w]', '', word)
                    if (word_clean and 
                        word_clean.lower() not in self.stopwords_set and
                        len(word_clean) > 2 and
                        (pos.startswith('NN') or pos.startswith('JJ') or pos.startswith('VB'))):
                        key_terms.append(word_clean)
            except:
                key_terms = self.simple_key_extraction(sentence)
        else:
            key_terms = self.simple_key_extraction(sentence)

        key_terms = list(dict.fromkeys(key_terms))
        return key_terms[:5]

    def simple_key_extraction(self, sentence: str) -> List[str]:
        words = re.findall(r'\b[A-Za-z]+\b', sentence)
        key_terms = []
        for word in words:
            word_lower = word.lower()
            if (len(word) > 3 and 
                word_lower not in self.stopwords_set and
                (word[0].isupper() or 
                 word_lower in ['learning', 'algorithm', 'data', 'model', 'network', 
                                'intelligence', 'system', 'training', 'prediction', 
                                'classification', 'regression', 'clustering', 
                                'supervised', 'unsupervised', 'neural', 'deep',
                                'machine', 'artificial', 'computer', 'science', 
                                'technology'])):
                key_terms.append(word)
        return key_terms

    def generate_options(self, correct_answer: str, context: str = "") -> List[str]:
        ml_terms = [
            'supervised learning', 'unsupervised learning', 'deep learning',
            'reinforcement learning', 'neural network', 'decision tree',
            'random forest', 'support vector machine', 'logistic regression',
            'linear regression', 'k-means clustering', 'gradient descent',
            'backpropagation', 'overfitting', 'underfitting', 'cross-validation',
            'feature selection', 'data preprocessing', 'model evaluation',
            'hyperparameter tuning', 'convolutional neural network',
            'recurrent neural network', 'natural language processing',
            'computer vision', 'pattern recognition', 'artificial intelligence',
            'machine learning'
        ]

        ai_terms = [
            'artificial intelligence', 'machine intelligence',
            'cognitive computing', 'expert system', 'knowledge base',
            'inference engine', 'natural language processing',
            'computer vision', 'robotics', 'automation', 'intelligent agent',
            'search algorithm', 'optimization', 'game theory', 'fuzzy logic',
            'genetic algorithm', 'swarm intelligence'
        ]

        all_terms = ml_terms + ai_terms
        options = [correct_answer]

        if ' ' in correct_answer:
            words = correct_answer.split()
            if len(words) >= 2:
                options.append(words[0])
                options.append(' '.join(words[1:]))

        relevant_terms = [term for term in all_terms if term.lower() != correct_answer.lower()]
        random.shuffle(relevant_terms)
        options.extend(relevant_terms[:2])

        options = list(dict.fromkeys(options))
        while len(options) < 4:
            options.append("None of the above")
        return options[:4]

    def create_fill_in_blank_question(self, sentence: str) -> Dict[str, Any]:
        key_terms = self.extract_key_terms(sentence)
        if not key_terms:
            return None
        for term in key_terms:
            if term in sentence:
                question_text = sentence.replace(term, "______", 1)
                options = self.generate_options(term, sentence)
                random.shuffle(options)
                return {
                    "Question": question_text,
                    "Options": options,
                    "Answer": term
                }
        return None

    def create_conceptual_question(self, sentence: str) -> Dict[str, Any]:
        key_terms = self.extract_key_terms(sentence)
        if not key_terms:
            return None

        templates = [
            "What concept is primarily discussed in this context?",
            "Which term best describes the main topic?",
            "What is the key concept mentioned?",
            "Which of the following is the main focus?"
        ]
        question_text = random.choice(templates)
        correct_answer = key_terms[0]

        options = self.generate_options(correct_answer, sentence)
        random.shuffle(options)
        return {
            "Question": question_text,
            "Options": options,
            "Answer": correct_answer
        }

    def generate_fallback_questions(self) -> List[Dict[str, Any]]:
        fallback = [
            {
                "Question": "What does ML stand for in computer science?",
                "Options": ["Machine Learning", "Multi-Level", "Major Logic", "Memory Load"],
                "Answer": "Machine Learning"
            },
            {
                "Question": "Which of the following is a supervised learning algorithm?",
                "Options": ["Decision Tree", "K-means", "Web Crawler", "Text Editor"],
                "Answer": "Decision Tree"
            },
            {
                "Question": "What is the primary goal of artificial intelligence?",
                "Options": ["Simulate human intelligence", "Store data", "Create websites", "Print documents"],
                "Answer": "Simulate human intelligence"
            },
            {
                "Question": "Which algorithm is commonly used for clustering?",
                "Options": ["K-means", "Linear Search", "Bubble Sort", "Binary Tree"],
                "Answer": "K-means"
            },
            {
                "Question": "What type of learning uses labeled training data?",
                "Options": ["Supervised Learning", "Unsupervised Learning", "File Management", "Data Storage"],
                "Answer": "Supervised Learning"
            },
            {
                "Question": "Which neural network layer is used for feature extraction in images?",
                "Options": ["Convolutional Layer", "Text Layer", "Audio Layer", "Print Layer"],
                "Answer": "Convolutional Layer"
            }
        ]
        return random.sample(fallback, min(6, len(fallback)))

    def finalQuestions(self) -> str:
        try:
            self.questions = []

            if self.sentences:
                num_sentences = min(10, len(self.sentences))   # ✅ 6 → 10
                selected = random.sample(self.sentences, num_sentences)

                for sentence in selected:
                    question = self.create_fill_in_blank_question(sentence)
                    if not question:
                        question = self.create_conceptual_question(sentence)
                    if question:
                        self.questions.append(question)

                unique = []
                seen = set()
                for q in self.questions:
                    if q["Question"] not in seen:
                        unique.append(q)
                        seen.add(q["Question"])
                self.questions = unique

            if len(self.questions) < 5:
                self.questions.extend(self.generate_fallback_questions())

            self.questions = self.questions[:10]   # ✅ limit max 10

            result = {"quiz": self.questions}
            return json.dumps(result, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error in question generation: {e}")
            result = {"quiz": self.generate_fallback_questions()}
            return json.dumps(result, indent=2, ensure_ascii=False)


class QuestionGenerator(Aqua):
    """Alias for backward compatibility"""
    pass


def generate_questions_from_text(text: str) -> str:
    generator = Aqua(text)
    return generator.finalQuestions()


def test_question_generation():
    sample_text = """
    Machine learning is a method of data analysis that automates analytical model building. 
    It is a branch of artificial intelligence based on the idea that systems can learn from data, 
    identify patterns and make decisions with minimal human intervention. Deep learning is a subset 
    of machine learning that uses neural networks with multiple layers. Supervised learning uses 
    labeled training data to make predictions.
    """
    print("Testing question generation...")
    generator = Aqua(sample_text)
    questions_json = generator.finalQuestions()
    print("Generated Questions JSON:")
    print(questions_json)


if __name__ == "__main__":
    test_question_generation()
