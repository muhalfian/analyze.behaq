import datetime, http.client, urllib.request, urllib.parse, urllib.error, base64, json, requests, operator, re, nltk, gensim

from flask import render_template, request, flash, redirect, url_for, Flask, request, session
from flask_login import login_user, logout_user
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.tokenize import wordpunct_tokenize
from SpamClassifier import analyze
from readability.readability import Document
from models import Feedback, ow_base_user
from app import db
from dateutil import parser

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
            vote = 1 
        else :
            vote = 0

        x = conn_sql.cursor()

        hasil = Feedback(url=request.form['url'], vote=vote, reason=request.form['reason'], user_id=1, ip_address=request.remote_addr, created_timestamp=datetime.datetime.now())
        db.session.add(hasil)
            
        # result = x.execute("""INSERT INTO feedback(url, status, reason, user_id, ip_address, created_timestamp) VALUES(%s,%s,%s,%s,%s,%s)""",[request.form['url'], status, request.form['reason'], 1, request.remote_addr, datetime.datetime.now()])
        
        try:
            db.session.commit()    
            # conn_sql.commit()
            flash("Ulasan telah ditambahkan")
        except:
            # conn_sql.rollback()
            pass            
    return render_template("index.html")

@app.route("/login/ustadz/", methods=["POST"])
def login_ustadz():
    if request.method == "POST":
        input = request.form

        check = ow_base_user.query.filter_by(email=request.form['email']).first()
        if check:
            flash("Login berhasil.")
            session['email'] = str(check.email)
        else :
            flash("Email atau password Anda salah")

    return redirect(url_for('search'))

@app.route("/search/logout/")
def logout_ustadz():
    session.pop('email', None)
    return redirect(url_for('search'))

@app.route("/search/")
def search():
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
            'mkt': 'id-ms',
            'safesearch': 'Moderate',
        })

        try:
            conn_url = http.client.HTTPSConnection('api.cognitive.microsoft.com')
            conn_url.request("GET", "/bing/v7.0/search?%s" % params, "{body}", headers)
            response = conn_url.getresponse()
            data = response.read().decode('utf-8')
            data_array  = json.loads(data)
            conn_url.close()
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))

        print(data_array)

        i=0
        for result in data_array['webPages']['value']:
            try:
                response = requests.get(result['url'], verify=False,stream=True)
            except requests.exceptions.ConnectionError:
                print(result['url'], "Connection refused")
                response = requests.get("https://pens.ac.id", verify=False)
                
            print(result['url'])
            doc = Document(response.content)
            raw = BeautifulSoup(doc.summary(html_partial=True), 'html.parser').get_text()
            result['sentiment'] = int(getSentiment(raw))
            print("SENTIMENT : ", result['sentiment'])
            result['status'] = analyze(raw)
            result['id_rank'] = i
            i+=1
        
        return render_template("index.html", data=data_array)
    else:
        return render_template("index.html")

@app.route("/news/")
def news():
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
            'mkt': 'en-id',
            'safesearch': 'Moderate',
        })

        try:
            conn_url = http.client.HTTPSConnection('api.cognitive.microsoft.com')
            conn_url.request("GET", "/bing/v7.0/news/search?%s" % params, "{body}", headers)
            response = conn_url.getresponse()
            data = response.read().decode('utf-8')
            data_array  = json.loads(data)
            conn_url.close()
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))

        print(data_array)

        i=0
        for result in data_array['value']:
            try:
                response = requests.get(result['url'], verify=False, allow_redirects=False)
            except requests.exceptions.ConnectionError:
                print(result['url'], "Connection refused")
                response = requests.get("https://pens.ac.id", verify=False)
                
            print(result['url'])
            doc = Document(response.content)
            raw = BeautifulSoup(doc.summary(html_partial=True), 'html.parser').get_text()
            result['sentiment'] = int(getSentiment(raw))
            print("SENTIMENT : ", result['sentiment'])
            result['status'] = analyze(raw)
            result['id_rank'] = i
            if result['datePublished']: 
                result['datePublished'] = parser.parse(result['datePublished'])
                result['datePublished'] = result['datePublished'].strftime('Diterbitkan pada %d %b %Y pukul %I:%M WIB')
                print(result['datePublished'])
            i+=1
        
        return render_template("news.html", data=data_array)
    else:
        return render_template("news.html")

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
        # conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
        # conn.request("POST", "/text/analytics/v2.0/languages?%s" % params, json.dumps(body), headers)
        # response = conn.getresponse().read().decode('utf-8')
        # data_array  = json.loads(response)
        # lang = [j['iso6391Name'] for i in data_array['documents'] for j in i['detectedLanguages'] ]
        # print("BAHASA : ",lang[0])
        # if(lang[0]=='id') or (lang[0]=='ms'):
            
        params = urllib.parse.urlencode({
            # Request parameters
            'kalimat': data[:1000],
        })
        conn_sent = http.client.HTTPConnection('www.prayuga.com')
        conn_sent.request("GET", "/api.php?%s" % params)
        sentiment_value = int(conn_sent.getresponse().read().decode('utf-8'))

        # else:
        #     # print(data[:1000])
        #     body = {
        #         "documents": [
        #             {
        #                 "id": "1",
        #                 "text": data[:1000]
        #             }
        #         ]
        #     }
            
        #     conn_sent = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
        #     conn_sent.request("POST", "/text/analytics/v2.0/sentiment?%s" % params, json.dumps(body), headers)
        #     sentiment = conn_sent.getresponse().read().decode('utf-8')
        #     sentiment_array  = json.loads(sentiment)
        #     sentiment_value = [int(i['id']) for i in data_array['documents'] ]
        #     print("SENTIMENT FLOAT : ", sentiment_value[0])
        #     if(sentiment_value[0]<1) and (sentiment_value[0]>-1) :
        #         sentiment_value = 0
        #     elif (sentiment_value[0]>1) or (sentiment_value[0]==1):
        #         sentiment_value = 1
        #     else :
        #         sentiment_value = -1

        conn_sent.close()

    except Exception as e:
        print("Connection refused. SENTIMENT NOT CREATED.")
        sentiment_value = 0
        # print("[Errno {0}] {1}".format(e.errno, e.strerror))

    return sentiment_value
