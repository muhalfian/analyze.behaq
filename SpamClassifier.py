"""
Created on Mon Jul 20 16:13:21 2015

The script that actually does the classification.

@author: aashishsatya
"""

from TrainingSetsUtil import get_words
import http.client, urllib.request, requests, math
from bs4 import BeautifulSoup
from models import hoax_training_set, ham_training_set, hoax_count, ham_count
from readability.readability import Document
from app import db
from sqlalchemy import select, func
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal, DecimalException

# totalHoax = hoax_training_set.query.count()
# totalHam = ham_training_set.query.count()

totalHoax = db.session.query(func.sum(hoax_count.qty).label('total')).all()[0][0]
totalHam = db.session.query(func.sum(ham_count.qty).label('total')).all()[0][0]

# print(totalHoax)

def classifyLog(message, kind, prior = 0.5, c = 3.7e-4):    
    """
    Returns the probability that the given message is of the given type of
    the training set.
    """
    
    msg_terms = get_words(message)
    msg_probability = 1
    bismillah = ()
    p_hoax = totalHoax/(totalHoax+totalHam)
    p_ham = totalHam/(totalHoax+totalHam)
    p_log = math.log(p_hoax/p_ham)
    nlog=1
    for term in msg_terms:
        prob_hoax = getTrainingSet(term,"hoax",c)
        prob_ham = getTrainingSet(term,"ham",c)
        if(prob_hoax) and (prob_ham):
            nlog *= prob_hoax/prob_ham
        # if temp_log:
        #     nlog += temp_log
    prob = p_log + math.log(nlog)
    print(prob)
    return prob

# using Paul Graham Method
def classifyGraham(message, kind, prior = 0.5, c = 3.7e-4):    
    """
    Returns the probability that the given message is of the given type of
    the training set.
    """
    
    msg_terms = get_words(message)
    p_ham = p_hoax = 1
    n = 0
    for term in msg_terms:
        hoax, ham = getProbability(term)
        p_hoax *= hoax
        p_ham *= ham
        n+=1
        # print(p_ham)
    if (p_hoax == 0) and (p_ham==0):
        prob_hoax = prob_ham = 0
    else :
        # modification tim peter
        p_hoax_all = totalHoax/(totalHoax+totalHam)
        p_ham_all = totalHam/(totalHoax+totalHam)
        #print("p_ham_all = ", totalHam, "/(", totalHoax , "+", totalHam)
        # devide = ((p_hoax_all**(1-n) * p_hoax) + (p_ham_all**(1-n) * p_ham))
        devide = ((p_hoax) + (p_ham))
        # prob_hoax = Decimal((p_hoax_all**(1-n) * p_hoax) / devide)
        prob_hoax = Decimal( p_hoax / devide)
        # print("phoax_all** = ", p_hoax_all**(1-n), " p_hoax = ", p_hoax, " p_ham_all = ", (p_ham_all**(1-n)), " p_ham = " , p_ham)
        # prob_ham = Decimal((p_ham_all**(1-n) * p_ham) / devide)
        prob_ham = Decimal(p_ham / devide)
        # print("prob_hoax = ", (p_hoax_all**(1-n) * p_hoax), " prob_ham = ", (p_ham_all**(1-n) * p_ham), " devide =  ", devide)
    print("PROBALITY : ", prob_hoax, " - ", prob_ham)
    return prob_hoax, prob_ham

def getTrainingSet(term, kind, c):
    if kind=='hoax':
        query = hoax_training_set.query.filter(hoax_training_set.term == term.encode('latin-1', 'ignore'))
    elif kind=='ham' :
        query = hoax_training_set.query.filter(hoax_training_set.term == term.encode('latin-1', 'ignore'))
    value = [result.value for result in query]
    
    if value==[] :
        value = 0
    else :
        if kind == 'hoax':
            value = value[0]/totalHoax
        elif kind == 'ham':
            value = value[0]/totalHam
    # print("VALUEEEEE : ", value)
    return value

#Paul Graham method to get probability words
def getProbability(term):
    
    c = 1
    g = 0.5

    query_ham = ham_training_set.query.filter(ham_training_set.term == term.encode('latin-1', 'ignore'))
    query_hoax = hoax_training_set.query.filter(hoax_training_set.term == term.encode('latin-1', 'ignore'))

    value_ham = [result.value for result in query_ham]
    value_hoax = [result.value for result in query_hoax]
        
    # print(value_ham, " ~ ", value_hoax)

    if value_ham==[] :
        ham = Decimal(0)
    else :
        ham = Decimal(value_ham[0])
    

    if value_hoax==[] :
        hoax = Decimal(0)
    else :
        hoax = Decimal(value_hoax[0])

    # print(hoax, " - ", totalHoax, ' - ', ham, " - ", totalHam, "=", prob_hoax)
    
    prob_hoax = ( Decimal(c * g) + Decimal(hoax/totalHoax))/(Decimal(c) + Decimal(hoax/totalHoax) + Decimal((2*ham)/totalHam))
    
    # print("cg = ", c*g, " - pH = ", ham/Decimal(totalHam), " pS = ", hoax/Decimal(totalHoax))
    prob_ham = ( Decimal(c * g) + ham/Decimal(totalHam))/(Decimal(c) + (hoax/Decimal(totalHoax)) + ((2*ham)/Decimal(totalHam)))
    # print(prob_ham)

    return prob_hoax, prob_ham
    

def analyze(raw):
    # probability = classifyLog(raw,"hoax", 0.2)
    prob_hoax, prob_ham = classifyGraham(raw,"hoax", 0.2)
    # print('PROB = ', probability)
    if(prob_hoax < 0.5):
        print('Your article has been classified as VEFIRIED.')
    else:
        print('Your article has been classified as HOAX.')
    return prob_hoax
       

