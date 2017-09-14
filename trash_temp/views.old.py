import http.client, urllib.request, urllib.parse, urllib.error, base64, json, requests, operator, re, nltk, gensim

from flask import render_template, request, flash, redirect, url_for, Flask, request
from flask_login import login_user, logout_user
from stop_words import stops
from words import diskriminatif, provokatif, negatif
from collections import Counter
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.tokenize import wordpunct_tokenize
from SpamClassifier import analyze
from readability.readability import Document

from app import app
from app import login_manager
from forms import LoginForm, SearchForm
import MySQLdb
conn_sql = MySQLdb.connect(host= "localhost",
                user="root",
                passwd="root",
                db="behaq")

@app.route('/')
def homepage():
    form = SearchForm()
    return render_template('search_index.html', form=form)

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form = LoginForm(request.form)
        if form.validate():
            login_user(form.user, remember=form.remember_me.data)
            flash("Successfully logged in as %s." % form.user.email, "success")
            return redirect(request.args.get("next") or url_for("homepage"))
    else:
        form = LoginForm()
    return render_template("login.html", form=form)

@app.route("/logout/")
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(request.args.get('next') or url_for('homepage'))    

@app.route("/feedback/", methods=["POST"])
def feedback():
    if request.method == "POST":
        input = request.form
        if request.form['status'] == "on" :
            status = 1 
        else :
            status = 0

        x = conn_sql.cursor()
        result = x.execute("""INSERT INTO feedback(url, status, reason, ip_address) VALUES(%s,%s,%s,%s)""",[request.form['url'], status, request.form['reason'], request.remote_addr])
        
        try:
            conn_sql.commit()
            flash("Ulasan telah ditambahkan")
        except:
            conn_sql.rollback()            
    return render_template("index.html")

@app.route("/search/")
def searchImage():
    search = request.args.get('q')
    if request.args.get('count') : 
        count = request.args.get('count') 
    else : 
        count=10
    if request.args.get('offset') : 
        offset = request.args.get('offset') 
    else : 
        offset=0

    if search:
        headers = {'Ocp-Apim-Subscription-Key': 'd94125558b884a309dd71f9e1aa8b9fb'}
        params = urllib.parse.urlencode({
            'q': search,
            'count': count,
            'offset': offset,
            'mkt': 'en-us',
            'safesearch': 'Moderate',
        })

        try:
            conn = http.client.HTTPSConnection('api.cognitive.microsoft.com')
            conn.request("GET", "/bing/v7.0/search?%s" % params, "{body}", headers)
            response = conn.getresponse()
            data = response.read().decode('utf-8')
            data_array  = json.loads(data)
            conn.close()
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))

        for result in data_array['webPages']['value']:
            try:
                response = requests.get(result['url'], verify=False)
            except requests.exceptions.ConnectionError:
                print(result['url'], "Connection refused")
                response = requests.get("https://pens.ac.id", verify=False)
                
            print(result['url'])
            doc = Document(response.content)
            raw = BeautifulSoup(doc.summary(html_partial=True), 'html.parser').get_text()
            result['sentiment'] = int(getSentiment(raw))
            print("SENTIMENT : ", result['sentiment'])
            result['status'] = analyze(raw)
        
        return render_template("index.html", data=data_array)
    else:
        return render_template("index.html")

def getSentiment(data):
    data = data.replace('\n', ' ').replace('\r', '').replace('\"', '\'')
    data = re.sub(' +',' ',data)

    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': '1e226548390644cdb5633c0c30365b46',
    }

    params = urllib.parse.urlencode({
        # Request parameters
        'numberOfLanguagesToDetect': '1',
    })

    print("DATA : ", data[:100])

    body = {
        "documents": [
            {
                "id": "1",
                "text": data[:1000]
            }
        ]
    }

    try:
        conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
        conn.request("POST", "/text/analytics/v2.0/languages?%s" % params, json.dumps(body), headers)
        response = conn.getresponse().read().decode('utf-8')
        data_array  = json.loads(response)
        lang = [j['iso6391Name'] for i in data_array['documents'] for j in i['detectedLanguages'] ]
        print("BAHASA : ",lang[0])
        if(lang[0]=='id') or (lang[0]=='ms'):
            params = urllib.parse.urlencode({
                # Request parameters
                'kalimat': data[:1000],
            })
            conn_sent = http.client.HTTPConnection('www.prayuga.com')
            conn_sent.request("GET", "/api.php?%s" % params)
            sentiment_value = conn_sent.getresponse().read().decode('utf-8')

        else:
            body = {
                "documents": [
                    {
                        "id": "1",
                        "text": data[:1000]
                    }
                ]
            }
            
            conn_sent = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
            conn_sent.request("POST", "/text/analytics/v2.0/sentiment?%s" % params, json.dumps(body), headers)
            sentiment = conn_sent.getresponse().read().decode('utf-8')
            sentiment_array  = json.loads(sentiment)
            sentiment_value = [int(i['id']) for i in data_array['documents'] ]
            print("SENTIMENT FLOAT : ", sentiment_value[0])
            if(sentiment_value[0]<1) and (sentiment_value[0]>-1) :
                sentiment_value = 0
            elif (sentiment_value[0]>1) or (sentiment_value[0]==1):
                sentiment_value = 1
            else :
                sentiment_value = -1

        conn.close()
    except Exception as e:
        print("Connection refused. SENTIMENT NOT CREATED.")
        sentiment_value = 0
        # print("[Errno {0}] {1}".format(e.errno, e.strerror))

    return sentiment_value

def saveResults(data_array):
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    
    bulk_data = [] 
    i = 1
    for result in data_array['webPages']['value']:
        data_dict = {}
        data_dict['id'] = i
        data_dict['name'] = result['name']
        data_dict['url'] = result['url']
        data_dict['displayUrl'] = result['displayUrl']
        data_dict['snippet'] = result['snippet']
        data_dict['dateLastCrawled'] = result['dateLastCrawled']
        i = i+1

        op_dict = {
            "index": {
                "_index": "temp", 
                "_type": "article", 
                "_id": data_dict['id']
            }
        }
        bulk_data.append(op_dict)
        bulk_data.append(data_dict)

    res = es.bulk(index = "temp", body = bulk_data, refresh = True)

@app.route('/count/', methods=['GET', 'POST'])
def count():
    errors = []
    results = {}
    corpus = []
    dictionary = []
    if request.method == "POST":
        # get url that the user has entered
        try:
            url = request.form['url']
            url2 = request.form['url2']
            r = requests.get(url)
            r2 = requests.get(url2)
            # print(r.text)
        except:
            errors.append(
                "Unable to get URL. Please make sure it's valid and try again."
            )
            return render_template('counting.html', errors=errors)
        if r:
            # text processing
            raw = BeautifulSoup(r.text, 'html.parser').get_text()
            raw2 = BeautifulSoup(r2.text, 'html.parser').get_text()
            
            # print(soup.prettify())
            nltk.data.path.append('./nltk_data/')  # set the path

            tokens_word = nltk.word_tokenize(raw)  # split raw text to words
            tokens_sent = nltk.sent_tokenize(raw)  # split raw text to words
            text_word = nltk.Text(tokens_word)
            print(text_word)

            tokens2_word = nltk.word_tokenize(raw2) # split raw text to words
            tokens2_sent = nltk.sent_tokenize(raw2) # split raw text to words
            text2_word = nltk.Text(tokens2_word)
            
            # remove punctuation, count raw words
            nonPunct = re.compile('.*[A-Za-z].*')
            Punct = re.compile('.*[.,?!A-Z].*')
            # date = re.compile('.*(?:(?:31(\/|-|\.)(?:0?[13578]|1[02]))\1|(?:(?:29|30)(\/|-|\.)(?:0?[1,3-9]|1[0-2])\2))(?:(?:1[6-9]|[2-9]\d)?\d{2})$|^(?:29(\/|-|\.)0?2\3(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00))))$|^(?:0?[1-9]|1\d|2[0-8])(\/|-|\.)(?:(?:0?[1-9])|(?:1[0-2]))\4(?:(?:1[6-9]|[2-9]\d)?\d{2}).*')

            raw_words = []
            punc = fail_punc = date_true = 0
            # print(text)
            for w in text_word :
                if nonPunct.match(w) :
                    raw_words.append(w)
                    punc = 0
                elif Punct.match(w) :
                    if punc < 4 :
                        punc = punc + 1
                    else :
                        fail_punc = fail_punc+1

            raw_words2 = []
            punc2 = fail_punc2 = date_true2 = 0
            # print(text)
            for w in text2_word :
                if nonPunct.match(w) :
                    raw_words2.append(w)
                    punc = 0
                elif Punct.match(w) :
                    if punc < 4 :
                        punc = punc + 1
                    else :
                        fail_punc = fail_punc+1

            # raw_words = [w for w in text if nonPunct.match(w)]
            raw_word_count = Counter(raw_words)

            # stop words
            no_stop_words = [w for w in raw_words if w.lower() not in stops]
            no_stop_words_count = Counter(no_stop_words)

            ### compare other article
            
            # generate words from sentence and save to dictionary
            gen_docs = [[w.lower() for w in word_tokenize(text)] for text in tokens_sent]
            dictionary = gensim.corpora.Dictionary(gen_docs)
            # below how to prove dictionary savings.
            # print("Number of words in dictionary:",len(dictionary))
            # for i in range(len(dictionary)):
            #     print(i, dictionary[i])
            
            # load dictionary to be assign as corpus
            corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
            # print(corpus)

            # assign corpus to tf_idf as tfid models
            tf_idf = gensim.models.TfidfModel(corpus)
            
            sims = gensim.similarities.Similarity('/usr/workdir/',tf_idf[corpus], num_features=len(dictionary))
            
            
            query_docs = [[w.lower() for w in word_tokenize(text)] for text in tokens2_sent]
            print(query_docs)
            query_doc_bow = [dictionary.doc2bow(query_doc) for query_doc in query_docs]
            print(query_doc_bow)
            query_doc_tf_idf = tf_idf[query_doc_bow]
            print(query_doc_tf_idf)
            print(sims[query_doc_tf_idf])

            # count diskriminatif, provokatif, negatif
            neg_count = 0
            dis_count = 0
            pro_count = 0
            for w in raw_words :
                if w.lower() in negatif:
                    neg_count = neg_count + 1
                elif w.lower() in diskriminatif:
                    dis_count = dis_count + 1
                elif w.lower() in provokatif:
                    pro_count = pro_count + 1

            print(neg_count)
            print(dis_count)
            print(pro_count)
            print(fail_punc)
            print(date_true)

            # save the results
            results = sorted(
                no_stop_words_count.items(),
                key=operator.itemgetter(1),
                reverse=True
            )
            try:
                result = Result(
                    url=url,
                    result_all=raw_word_count,
                    result_no_stop_words=no_stop_words_count
                )
                # db.session.add(result)
                # db.session.commit()
            except:
                errors.append("Unable to add item to database.")
    return render_template('counting.html', errors=errors, results=results, corpus=corpus, dictionary=dictionary) #results=results, 

def getUrl(url):
    try:
        r = requests.get(url)
    except:
        errors.append("Unable to get URL. Please make sure it's valid and try again.")
        return render_template('counting.html', errors=errors)
    return r

def getContent(r):
    # text processing
    raw = BeautifulSoup(r.text, 'html.parser').get_text()
    nltk.data.path.append('./nltk_data/')  # set the path
    tokens_sent = nltk.sent_tokenize(raw)  # split raw text to sentence
    tokens_word = nltk.word_tokenize(raw)  # split raw text to word
    text_word = nltk.Text(tokens_sent)
    
    # count punctuation errors, repetition uppercase, repetition punctuation that parameter of unstructured documents
    Punc = re.compile('.*[.,?!A-Z].*')
    no_stop_words = w = []
    punc = fail_punc = date_true = neg_count = dis_count = pro_count = 0
    for w in tokens_word :
        if Punc.match(w) :
            if punc < 4 : 
                punc += 1 
            else : 
                fail_punc += 1 
            if w.lower() in negatif:
                neg_count += 1
            elif w.lower() in diskriminatif:
                dis_count += dis_count + 1
            elif w.lower() in provokatif:
                pro_count += 1
        else : 
            punc = 0
        if w.lower() not in stops :  # removing stop words for eliminate hi-frequency words
            no_stop_words.append(w.lower()) 
    return punc, fail_punc, no_stop_words, tokens_sent

def processContent(tokens_sent, tokens2_sent):
    # generate and saving dictionary
    gen_docs = [[w.lower() for w in word_tokenize(text)] for text in tokens_sent]
    dictionary = gensim.corpora.Dictionary(gen_docs)
    print(dictionary)

    # load dictionary to be assign as corpus
    corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
    tf_idf = gensim.models.TfidfModel(corpus)
            
    sims = gensim.similarities.Similarity('/usr/workdir/',tf_idf[corpus], num_features=len(dictionary))
    print(sims)
    print(type(sims))

    query_docs = [[w.lower() for w in word_tokenize(text)] for text in tokens2_sent]
    print(query_docs)
    query_doc_bow = [dictionary.doc2bow(query_doc) for query_doc in query_docs]
    print(query_doc_bow)
    query_doc_tf_idf = tf_idf[query_doc_bow]
    print(query_doc_tf_idf)
    # print(sims[query_doc_tf_idf])


@app.route('/proses/', methods=['GET', 'POST'])
def process():
    errors = []
    results = {}
    corpus = []
    dictionary = []

    if request.method == "POST":
        r = getUrl(request.form['url'])
        # r2 = getUrl(request.form['url2'])
        if r:
            punch, fail_punc, no_stop_words, tokens_sent = getContent(r)
            # punch2, fail_punc2, no_stop_words2, tokens2_sent = getContent(r2)
            processContent(tokens_sent, tokens2_sent)
                        
            # print(neg_count)
            # print(dis_count)
            # print(pro_count)
            # print(fail_punc)
            
            # save the results
            results = sorted(
                no_stop_words_count.items(),
                key=operator.itemgetter(1),
                reverse=True
            )
            try:
                result = Result(
                    url=url,
                    result_all=raw_word_count,
                    result_no_stop_words=no_stop_words_count
                )
                # db.session.add(result)
                # db.session.commit()
            except:
                errors.append("Unable to add item to database.")
    return render_template('counting.html', errors=errors, results=results, corpus=corpus, dictionary=dictionary) #results=results, 
