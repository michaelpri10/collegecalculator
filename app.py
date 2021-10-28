from flask import Flask, render_template, url_for
from flask_mysqldb import MySQL
import yaml

app = Flask(__name__)

path = "/cse30246/collegecalculator"

#configure db
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST']= db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

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
        user_details = request.form
        pass

    return render_template("search.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
