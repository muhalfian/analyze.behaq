<<<<<<< HEAD
# ./app.py
from flask import Flask
app = Flask(__name__)
@app.route('/')
def index():
	return "Yo, it's working!"
if __name__ == "__main__":
	app.run()
=======
from flask import Flask
app = Flask(__name__)


@app.route('/')
def hello():
    return "Hello World!"

if __name__ == '__main__':
    app.run()
>>>>>>> 91611d73569c03b8d98e8cb890233f064e8b5dee
