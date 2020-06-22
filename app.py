from flask import Flask, render_template, request, jsonify, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from scrapper import Scrapper
import pandas as pd

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = "i don't have a secret!!"
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(30), unique = True, nullable = False)
    email = db.Column(db.String(20), nullable = True)
    password = db.Column(db.String(30), nullable = False)

    def __repr__(self):
        return f'self.username, self.email, self.password'

class Record(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    product = db.Column(db.String(30), nullable = False)
    created = db.Column(db.String(20), nullable = True)
    pages = db.Column(db.String(30), nullable = False)
    data = db.Column(db.String(30), nullable = False)
    user = db.Column(db.String(30), nullable = False)

    def __repr__(self):
        return f'self.username, self.email, self.password'


db.create_all()

@app.route('/')
@app.route('/home')
def home():
    if not session.get('user'):
        return redirect('/signin')
    return render_template('home.html', loggedin = session.get('user'))

@app.route('/signin', methods = ["POST", "GET"])
def Signin():
    
    if request.method == 'POST':
        data = request.form
        
        user = User.query.filter_by(username = data.get('username')).first()
        if user:
            print(user)
            if user.password == data.get('password'):
                print('login success')
                session['user'] = user.username
                return jsonify('success')
                
            else:
                return jsonify('failed')
        else:
            return jsonify('failed')

    return render_template('signin.html')

@app.route('/signup', methods = ["POST", "GET"])
def Signup():
    if request.method == 'POST':
        data = request.form
        user = User(username = data.get('username'), email = data.get('email'), password = data.get('password'))
        db.session.add(user)
        db.session.commit()
        print('data saved!!')
        return jsonify('success')

    return render_template('signup.html')

@app.route('/logout')
def Logout():
    session['user'] = None
    return redirect('/signin')
    

@app.route('/scrap')
def Scrap():
    product = request.args.get('product')
    maxpages = request.args.get('max')
    website = request.args.get('website')

    if not maxpages:
        maxpages = 2
    print(product, maxpages)

    scrap = Scrapper()
    scrapped_data, csvfile = scrap.start(product, max = maxpages, website = website)

    record = Record(product= product, created= datetime.today().strftime('%d_%m_%Y'), pages= maxpages,
     data= csvfile.split('/')[-1], user = session.get('user'))
    db.session.add(record)
    db.session.commit()

    return jsonify(scrapped_data)

@app.route('/display')
def displayData():
    return render_template('/display.html', loggedin = session.get('user'))

@app.route('/report')
def report():
    data = Record.query.all()
    return render_template('report.html', data = data, loggedin = session.get('user'))


@app.route('/scrapdata')
def scrappedData():
    id = request.args.get('id')
    sortprice = request.args.get('sortprice')

    data = Record.query.filter_by(id=id).first()
    df = pd.read_csv('csvfiles/'+data.data)

    if sortprice == '1':
        df = df.sort_values(by = 'price')
    elif sortprice == '2':
        df = df.sort_values(by = 'price', ascending = False)

    return render_template('scrapdetails.html', data = df, id=id, loggedin = session.get('user'))

@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    if not session.get('user'):
        return redirect('/login')
    return send_file(filename_or_fp=f'csvfiles/{filename}')

if __name__ == "__main__":
    app.run(debug=True)