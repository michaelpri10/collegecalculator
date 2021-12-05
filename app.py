from flask import Flask, redirect, render_template, request, session, url_for
from flask_mysqldb import MySQL
import yaml
from collections import namedtuple
from query_schools import generate_query, get_college

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

CARD_COLUMNS = ("university_id", "name", "city", "state", "website", "campus_location", "total_enrollment", "location_score", "score_score", "finance_score", "other_score")
UNI_COLUMNS = ("university_id", "name", "city", "state", "website", "campus_location", "total_enrollment", "control", "religious", "accepts_ap_credit", "study_abroad", "offers_rotc", "has_football", "has_basketball", "ncaa_member", "retention_rate", "graduation_rate", "total_applicants", "total_admitted", "admission_rate", "male_applicants", "female_applicants", "male_admitted", "female_admitted", "sat_rw_25", "sat_rw_75", "sat_math_25", "sat_math_75", "act_25", "act_75", "in_state_price", "out_of_state_price", "average_price_after_aid", "percent_given_aid", "percent_american_indian_native_alaskan", "percent_asian", "percent_hawaiian_pacific_islander", "percent_black", "percent_white", "percent_hispanic", "percent_other", "percent_two_races")
UniversityCard = namedtuple('UniversityCard', CARD_COLUMNS)
University = namedtuple('University', UNI_COLUMNS)

#login window
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
                cur.execute("SELECT * from login_information where username = %(username)s and password = %(password)s",
                    {'username': username, 'password': password}
                )
                login_exists = cur.fetchall()

                mysql.connection.commit() #save changes in the database
                cur.close()
                
                if len(login_exists) != 0:
                        session["username"] = username
                        session["logged_in"] = True
                        return redirect(url_for('find_colleges'))
                else:
                        return 'Incorrect username or password'
        
        return render_template('login.html')

# create account window
@app.route(path + "/create_account", methods = ["GET", "POST"])
def create_account():
        if request.method == "POST":
                #get inputs
                new_user_details = request.form
                new_username = new_user_details['u']
                new_password = new_user_details['p']
                
                cur = mysql.connection.cursor()
                
                #check if username already exists
                cur.execute("SELECT * from login_information where username = %(new_username)s", {'new_username': new_username})
                login_exists = cur.fetchall()

                if len(login_exists) != 0:
                        return 'Username already in use. Please choose another.'
                        return redirect(url_for('/create_account'))
                else:
                        #insert into the database
                        cur.execute("INSERT INTO login_information(username, password) VALUES(%(new_username)s, %(new_password)s)",
                            {'new_username': new_username, 'new_password': new_password}
                        )
                        mysql.connection.commit()       
                        return redirect(url_for('login'))

                cur.close()

        if session['logged_in']:
                return redirect(url_for('user_settings'))
        return render_template('create_account.html')

# user settings window
@app.route(path + "/user_settings", methods = ["GET", "POST"])
def user_settings():
        if request.method == "POST":
                form_details = request.form
                cur = mysql.connection.cursor()

                #Update account password
                if form_details['submit_button'] == 'update':
                        username = form_details['username']
                        old_password = form_details['oldpassword']
                        new_password = form_details['newpassword']
                        
                        #check if information is correct
                        cur.execute("SELECT * from login_information where username = %(username)s and password = %(password)s", {'username': session["username"], 'password': old_password}
                        )
                        login_exists = cur.fetchall()

                        if len(login_exists) == 0:
                                return 'Incorrect account information. Account settings not saved.'
                        else:
                                cur.execute("UPDATE login_information SET password=%(new_password)s WHERE username=%(username)s", {'new_password': new_password, 'username': session["username"]})
                                mysql.connection.commit()
                                cur.close()
                                return 'Password updated.'

                #Delete Account
                elif form_details['submit_button'] == 'delete':
                        username = form_details['delete_user']
                        password = form_details['delete_pass']
                        
                        #check if information is correct
                        cur.execute("SELECT * from login_information where username = %(username)s and password = %(password)s",
                            {'username': username, 'password': password}
                        )
                        login_exists = cur.fetchall()   

                        if len(login_exists) == 0:
                                return 'Incorrect account information. Account settings not saved.'
                        else:
                                cur.execute("DELETE FROM login_information where username=%(username)s and password=%(password)s", {'username': username, 'password': password})
                                mysql.connection.commit()
                                cur.close()
                        return 'Account Deleted.'
                elif form_details['submit_button'] == 'logout':
                        print('logging out')
                        session['logged_in'] = False
                        del session['username']
                        return redirect(url_for('login'))
        return render_template("user_settings.html", username=session["username"])


@app.route(path + "/search", methods=["GET", "POST"])
def find_colleges():
    if request.method == "POST":
        parameters = request.form
        sql_query = generate_query(parameters)
        cur = mysql.connection.cursor()
        cur.execute(sql_query)
        results = cur.fetchall()
        universities = [UniversityCard(*school) for school in results]
        return render_template('results.html', universities=universities)
    return render_template("user_form.html")

@app.route(path + "/colleges/<int:id>", methods=["GET"])
def college_info(id):
	info_query, majors_query = get_college(id)
	cur = mysql.connection.cursor()
	cur.execute(info_query)
	data = cur.fetchall()
	if len(data):
		info = data[0]
		cur.execute(majors_query)
		majors = [major[0].strip().replace('"', '') for major in cur.fetchall()]
		university = University(*info)
		return render_template("college.html", uni=university, majors=majors)
	else:
		return redirect(url_for("find_colleges"))

#find majors
@app.route(path+ "/search_majors", methods=["GET","POST"])
def find_majors():
	if request.method == "POST":
		parameters = request.form
		return render_template('results_majors.html')
	return render_template("user_form_majors.html")


if __name__ == "__main__":
        app.run(host="0.0.0.0", debug=True)
