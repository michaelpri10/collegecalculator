from flask import Flask, redirect, render_template, request, session, url_for
from flask_mysqldb import MySQL
import yaml
from query_schools import generate_query

app = Flask(__name__)
mysql = MySQL(app)

path = "/cse30246/collegecalculator"
login_username = ""

# configure db
db = yaml.load(open('db.yaml'), Loader=yaml.Loader)
app.config['MYSQL_HOST']= db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.secret_key = "databaseproject"

@app.route(path + "/", methods=['GET', 'POST'])
def login():
	if request.method == 'POST': 
		# get inputs
		userDetails = request.form
		username = userDetails['u']
		password = userDetails['p']
		
		# connect to mysql and run queries
		cur = mysql.connection.cursor()
		
		#check if a username / password exists. if not, make an account	
		cur.execute("SELECT * from login_information where username = '%s' and password = '%s'" % (username, password))
		login_exists = cur.fetchall()

		mysql.connection.commit() #save changes in the database
		cur.close()
		
		if len(login_exists) is not 0:
			login_username = username
			return redirect(url_for('search'))
		else:
			return 'Incorrect username or password'
	
	return render_template('login.html')

@app.route(path + "/create_account", methods = ["GET", "POST"])
def create_account():
	if request.method == "POST":
		#get inputs
		new_user_details = request.form
		new_username = new_user_details['u']
		new_password = new_user_details['p']
		
		cur = mysql.connection.cursor()
		
		#check if username already exists
		cur.execute("SELECT * from login_information where username = '%s'" % new_username)
		login_exists = cur.fetchall()

		if len(login_exists) is not 0:
			return 'Username already in use. Please choose another.'
			return redirect(url_for('/create_account'))
		else:
			#insert into the database
			cur.execute("INSERT INTO login_information(username, password) VALUES(%s, %s)", (new_username, new_password))
			mysql.connection.commit()	
			return redirect(url_for('login'))
		
		cur.close()

	return render_template('create_account.html')

@app.route(path + "/search", methods=["GET", "POST"])
def search():
	if request.method == "POST":
		parameters = request.form
		columns, sql_query = generate_query(parameters)
		session['columns'] = columns
		session['results'] = results
		return redirect(url_for('results'))
	return render_template("search.html")

@app.route(path + "/results")
def results():
	columns = session['columns']
	results = session['results']
	return render_template('results', columns=columns, results=results)

if __name__ == "__main__":
	app.run(host="0.0.0.0", debug=True)
