from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
#IMPORTING MYSQLDB
from flask_mysqldb import MySQL
#FROM FORMS WE IMPORT EACH TYPE OF FIELD WE WILL USE
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
#PASSWORD ENCRYPTION FROM THE PASSLIB
from passlib.hash import sha256_crypt

app = Flask(__name__)

#connecting to the database

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html', articles=Articles)

@app.route('/article/<string:id>/')
def article_info(id):
    return id
    # return render_template('article_info.html', article=Articles)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username= StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message="Passwords do not match")
    ])
    confirm = PasswordField('Confirm')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #create a cursor to help execute queries (sql)

        sql = mysql.connection.cursor()

        sql.execute("INSERT INTO users(name, email, username, password) VALUES (%s, %s, %s, %s)", (name, email, username, password))

        #Commit to changes to db
        mysql.connection.commit()

        #close connection
        sql.close()

        flash("You are now registered and can log in", 'success')

        return redirect(url_for('index'))

    return render_template('register.html', form=form)

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)