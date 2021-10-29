from flask import Flask, redirect, render_template, request, session, url_for
from flask_mysqldb import MySQL
import yaml
from collections import namedtuple
from query_schools import generate_query

app = Flask(__name__)
mysql = MySQL(app)

path = "/cse30246/collegecalculator"

# configure db
db = yaml.load(open('db.yaml'), Loader=yaml.Loader)
# app.config['MYSQL_HOST']= db['mysql_host']
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.secret_key = "databaseproject"

@app.route(path + "/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route(path + "/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get inputs
        userDetails = request.form
        username = userDetails['u']
        password = userDetails['p']

        # connect to mysql and run queries
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO login_info(username, password) VALUES(%s, %s)", (username, email))
        mysql.connection.commit() #save changes in the database
        cur.close()
        return 'success'
    return render_template('login.html')

@app.route(path + "/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        parameters = request.form
        columns, sql_query = generate_query(parameters)
        cur = mysql.connection.cursor()
        cur.execute(sql_query)
        results = cur.fetchall()
        session['columns'] = columns
        session['results'] = results
        return redirect(url_for('results'))

    return render_template("search.html")

@app.route(path + "/results")
def results():
    columns = session['columns']
    results = session['results']
    University = namedtuple('University', columns)
    universities = [University(*school) for school in results]
    return render_template('results.html', universities=universities)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
