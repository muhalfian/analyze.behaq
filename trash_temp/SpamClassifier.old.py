"""
Created on Mon Jul 20 16:13:21 2015

The script that actually does the classification.

@author: aashishsatya
"""

from TrainingSetsUtil import get_words
import http.client, urllib.request, requests, math
from bs4 import BeautifulSoup
from models import hoax_training_set, ham_training_set
from readability.readability import Document

import MySQLdb
conn = MySQLdb.connect(host= "localhost",
                user="root",
                passwd="root",
                db="behaq")
x = conn.cursor()

x.execute("""SELECT count(*) FROM hoax_training_set""")
totalHoax = x.fetchall()
x.execute("""SELECT count(*) FROM ham_training_set""")
totalHam = x.fetchall()
totalHam = totalHam[0][0]
totalHoax = totalHoax[0][0]
# print(totalHoax, totalHam)

# c is an experimentally obtained value
def classify(message, kind, prior = 0.5, c = 3.7e-4):
    
    """
    Returns the probability that the given message is of the given type of
    the training set.
    """
    
    msg_terms = get_words(message)
    # print(msg_terms)
    # print ('\n')
    
    msg_probability = 1
    # print(msg_probability)
    bismillah = ()
    for term in msg_terms:
        bismillah +=(term, msg_probability, getTrainingSet(term, kind, c))        
        msg_probability = msg_probability * getTrainingSet(term, kind, c)
    
    print(bismillah)
    return msg_probability * prior

def classifyLog(message, kind, prior = 0.5, c = 3.7e-4):
    
    """
    Returns the probability that the given message is of the given type of
    the training set.
    """
    
    msg_terms = get_words(message)
    # print(msg_terms)
    # print ('\n')
    
    msg_probability = 1
    # print(msg_probability)
    bismillah = ()
    p_hoax = totalHoax/(totalHoax+totalHam)
    p_ham = totalHam/(totalHoax+totalHam)
    p_log = math.log(p_hoax/p_ham)
    nlog=0
    for term in msg_terms:
        # bismillah +=(term, msg_probability, getTrainingSet(term, kind, c))        
        # msg_probability = msg_probability * getTrainingSet(term, kind, c)
        nlog += math.log((getTrainingSet(term, "hoax", c)/totalHoax)/(getTrainingSet(term, "ham", c)/totalHam))


    # print(bismillah)
    prob = p_log + nlog
    print(prob)
    return prob

def getTrainingSet(term, kind, c):
    
    # print(term)
    if kind=='hoax':
        x.execute("""SELECT value FROM hoax_training_set WHERE term = %s""",[term.encode('latin-1', 'ignore')])
        # result = hoax_training_set.query.filter(hoax_training_set.term == term.encode('latin-1', 'ignore'))
    elif kind=='ham' :
        x.execute("""SELECT value FROM ham_training_set WHERE term = %s""",[term.encode('latin-1', 'ignore')])
        # result = hoax_training_set.query.filter(ham_training_set.term == term.encode('latin-1', 'ignore'))
    value = x.fetchall()
    # if result :
    #     value = result.value 
    # else :
    #     value = c
    if value==() :
        value = c 
    else :
        value = value[0][0]
    return value

# uncomment this to provide input to the program
def analyze(raw):
    
    # url = result['url']
    # r = requests.get(url)
    # raw = BeautifulSoup(r.text, 'html.parser').get_text()
    
    
    # print(raw)
    print ('\n')
    #raw='Sebarkan !! inilah uang mengheck dan mengganti data di kpud 2017, yang telah menzholimi pemimpin bapak anies dan bapak uno, harusnya Paslon pilihan Allah nomer 3, Bapak Anies dan Bapak Uno, sudah mencapai suara 70% lebih, dari satu putaran kemenangan, tapi gara2 hecker laknatullah ini telah mengganti tabulasi data, dalam seragam mereka tertulis AOCT (Ahokers Organisation Cyber Team). kita muslim Hecker lulusan 212 berhasil mengatasinya.'
    
    # 0.2 and 0.8 because the ratio of samples for spam and ham were the 0.2-0.8
    # spam_probability = classify(mail_msg, spam_training_set, 0.2)
    # ham_probability = classify(mail_msg, ham_training_set, 0.8)
    probability = classifyLog(raw,"hoax", 0.2)
    
    
    print('PROB = ', probability)
        
    if(probability<0):
        print('Your article has been classified as VEFIRIED.')
    else:
        print('Your article has been classified as HOAX.')
    
    # if(total==0):
    #     print('Your mail has been classified as ABSOLUTELY VERIFIED')
    #     unverified_percent = 0
    #     verified_percent = 0    
    # else :
    #     unverified_percent = (unverified_probability/total)*100
    #     verified_percent = (verified_probability/total)*100    
    #     if unverified_percent > verified_probability:
    #         print("HOAX : ",unverified_percent, "%"," VERIFIED : ",verified_percent, "%")
    #         print('Your mail has been classified as HOAX.')
    #     else:
    #         print("HOAX : ",unverified_percent, "%"," VERIFIED : ",verified_percent, "%")
    #         print('Your mail has been classified as VERIFIED') 
    #         print ('\n')
    return probability
       

