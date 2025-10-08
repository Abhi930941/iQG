import subprocess

def install(name):
    subprocess.call(['pip', 'install', name])

install('bs4')
install('difflib')
install('flask')
# install('heapq')
# install('json')
install('nltk')
# install('os')
install('pickle')
install('PyPDF2')
# install('re')
# install('random')
install('requests')
# install('string')
install('textblob')
install('urllib')
install('werkzeug')

import nltk
nltk.download("punkt")
nltk.download("stopwords")
nltk.download("brown")