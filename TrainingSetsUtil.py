"""
Created on Thu Jul 16 21:58:45 2015

Script that handles operations involving the body of the e-mail, such as
tokenizing, counting words, etc.

@author: Aashish Satyajith
"""

# for tokenize
import nltk, re, requests
from bs4 import BeautifulSoup
from readability.readability import Document
# from elasticsearch import Elasticsearch
# from nltk.corpus import stopwords
from nltk.tokenize import wordpunct_tokenize
from urllib.request import urlopen
from models import hoax_training_set, ham_training_set, Stopwords
from app import db

# for reading all the files
from os import listdir
from os.path import isfile, join

# add path to NLTK file
nltk.data.path = ['nltk_data']
# load stopwords
# stopwords = set(stopwords.words('english'))

def get_words(message):
    
    """
    Extracts all the words from the given mail and returns it as a set.
    """
    all_words = set(wordpunct_tokenize(message.replace('=\\n', '').lower()))

    msg_words = []
    for word in all_words:
        query = Stopwords.query.filter(Stopwords.term == word).first()
        if not query and len(word)>2:
            msg_words.append(word)    

    nonPunct = re.compile('.*[,.!?A-Za-z].*')
    msg_words = [w for w in msg_words if nonPunct.match(w)]
    return msg_words


def get_content_from_file(path):
    content_in_dir = [content_file for content_file in listdir(path) if isfile(join(path, content_file))]
    # count of cmds in the directory
    cmds_count = 0
    # total number of files in the directory
    total_file_count = len(content_in_dir)
    print(content_in_dir)
    data=[]
    for content_name in content_in_dir:
        message = ''
        with open(path + content_name, 'rb') as content_file:
            for line in content_file:
                if line == b'\n':
                    # make a string out of the remaining lines
                    # print(str(line))
                    for line in content_file:
                        # print(str(line))
                        message += str(line)
        data.append([content_name, message])
    # print("DATAAAA", data)
    return data

def get_content_from_link(url):
    response = requests.get(url, verify=False)
    print(url)
    doc = Document(response.content)
    raw = BeautifulSoup(doc.summary(html_partial=True), 'html.parser').get_text()
    data = raw.replace('\n', ' ').replace('\r', '').replace('\"', '\'')
    data = re.sub(' +',' ',data)
    url = url
    return [[url, data]]

def make_training_set(path, kind):
    
    # initializations
    training_set = {}
    # article = get_content_from_file(path)
    article = get_content_from_link(path)
    # print(article)
    for content in article: 
        message = content[1]
        # print(message)
    
        terms = get_words(message)
        print(terms)    
                
        for term in terms:
            check = [hasil for hasil in training_set if term == hasil ]
            # print(term)
            if check:
                training_set[str(term)] = training_set[str(term)] + 1
                # print(term, " : ", training_set[term])
            else:
                training_set[term] = 1
            # print(training_set)
            # print("HASIL : ",term, ":", training_set[term])
    # print(training_set)
    for terms in training_set.keys(): 
        if(kind=='ham'):
            # check = ham_training_set.query.filter_by(term=terms).first()
            check = ham_training_set.query.filter_by(term=terms).first()
            print(check, ":")
            if check:
                check.value = int(check.value) + training_set[terms]
                print("UPDATE ", check.term)
            else :
                hasil = ham_training_set(term=terms, value=training_set[terms])
                db.session.add(hasil)
                print("ADD ", hasil.term)
        elif(kind=='hoax'):
            check = hoax_training_set.query.filter_by(term=terms).first()
            if check:
                check.value = int(check.value) + training_set[term]
                print("UPDATE ", check.term)
            else :
                hasil = hoax_training_set(term=terms, value=training_set[terms])
                db.session.add(hasil)
                print("ADD ", hasil.term)
        db.session.commit()

    # print(hasil)

    # print(training_set)

# hoax_path = 'data/hoax/'
# make_training_set(hoax_path, "hoax")