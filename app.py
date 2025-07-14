from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
# from data import Articles
#IMPORTING MYSQLDB
from flask_mysqldb import MySQL
#FROM FORMS WE IMPORT EACH TYPE OF FIELD WE WILL USE
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
#PASSWORD ENCRYPTION FROM THE PASSLIB
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

#connecting to the database

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Philosophy@360' #USE THE CONFIGURED PASSWORD FOR YOUR DATABASE
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    articles = get_articles()
    return render_template('articles.html', articles=articles)

@app.route('/article/<string:id>/')
def article_info(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()

    # cur.close()

    return render_template('article_info.html', article=article)

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

        return redirect(url_for('login'))

    return render_template('register.html', form=form)


#USER LOGIN

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        
        if result > 0:
            user_data = cur.fetchone()
            password_hash = user_data['password']

            if sha256_crypt.verify(password, password_hash):
                session['logged_in'] = True
                session['username'] = username

                flash(f"You are now logged in! Happy blogging", 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid Password', 'danger')
        else:
            flash('User not found', 'danger')

        cur.close()

    return render_template('login.html')

#CHECK IF USER IS LOGGED IN

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('login'))
    return wrap
        
#LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    flash('You are logged out', 'success')
    return redirect(url_for('login'))

#RETREIVING DATA FROM THE DATABASE


def get_articles():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall() if result > 0 else []
    cur.close()
    return articles



#DASHBOARD
@app.route('/dashboard')
@is_logged_in
def dashboard():
    articles = get_articles()
    if not articles:
        flash("No articles found. Create articles to view them here!", "warning")
    return render_template('dashboard.html', articles=articles)



#ADDING ARTICLE

class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=250)])
    body = TextAreaField('Body', [validators.Length(min=30)])

@app.route('/addArticle', methods=['POST', 'GET'])
@is_logged_in
def addArticle():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        author = session['username']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title, author, body) VALUES (%s, %s, %s)", (title, author, body))

        mysql.connection.commit()

        cur.close()

        flash('New article added', 'success')
        return redirect(url_for('dashboard'))

    return render_template("addArticle.html", form=form)


#EDITING ARTICLE

@app.route('/editArticle/<string:id>', methods=['POST', 'GET'])
@is_logged_in
def editArticle(id):
    # create a cursor

    cur = mysql.connection.cursor()

    #Get article by id

    article = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    #Get form

    form = ArticleForm(request.form)

    #Populate article foem fields

    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        author = session['username']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s", (title, body, id))

        mysql.connection.commit()

        cur.close()

        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))

    return render_template("editArticle.html", form=form)

#DELETING ARTICLE

@app.route('/deleteArticle/<string:id>', methods=['POST'])
@is_logged_in
def deleteArticle(id):

    #create a cursor
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    #commit changes
    mysql.connection.commit()
    cur.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)