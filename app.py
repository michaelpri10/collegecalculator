from flask import Flask, redirect, render_template, request, session, url_for
from flask_mysqldb import MySQL
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from flask_nav.elements import *

import yaml
from collections import namedtuple
import concurrent.futures
from query_schools import generate_query, get_college, get_college_basic, find_major, get_major_type_info, get_major_info
from werkzeug.routing import BaseConverter
import requests
import re
from bs4 import BeautifulSoup


class IntListConverter(BaseConverter):
    regex = r'\d+(?:,\d+)*,?'

    def to_python(self, value):
        return [int(x) for x in value.split(',')]

    def to_url(self, value):
        return ','.join(str(x) for x in value)


topbar = Navbar(
                View('Home', 'home'),
                View('MyUniversities', 'saved_universities'),
                View('Find Colleges', 'find_colleges'),
                View('Search Engine', 'search_engine'),
                View('Account', 'user_settings'),
                View('Search Majors', 'find_majors')
                )
# registers the "top" menubar
nav = Nav()
nav.register_element('top', topbar)

app = Flask(__name__)
mysql = MySQL(app)
bootstrap = Bootstrap(app)

app.url_map.converters['int_list'] = IntListConverter

path = "/cse30246/collegecalculator"


# configure db
db = yaml.load(open('db.yaml'), Loader=yaml.Loader)
# app.config['MYSQL_HOST']= db['mysql_host']
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.secret_key = "databaseproject"

CARD_COLUMNS = ("university_id", "name", "city", "state", "website", "campus_location", "total_enrollment") #, "location_score", "academics_score", "finance_score", "other_score")
UNI_COLUMNS = ("university_id", "name", "city", "state", "website", "campus_location", "total_enrollment", "control", "religious", "accepts_ap_credit", "study_abroad", "offers_rotc", "has_football", "has_basketball", "ncaa_member", "retention_rate", "graduation_rate", "total_applicants", "total_admitted", "admission_rate", "male_applicants", "female_applicants", "male_admitted", "female_admitted", "sat_rw_25", "sat_rw_75", "sat_math_25", "sat_math_75", "act_25", "act_75", "in_state_price", "out_of_state_price", "average_price_after_aid", "percent_given_aid", "percent_american_indian_native_alaskan", "percent_asian", "percent_hawaiian_pacific_islander", "percent_black", "percent_white", "percent_hispanic", "percent_other", "percent_two_races")
UniversityCard = namedtuple('UniversityCard', CARD_COLUMNS)
University = namedtuple('University', UNI_COLUMNS)


@app.route(path + '/')
def index():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))

    return redirect(url_for('home'))


@app.route(path + '/home', methods=['GET', 'POST'])
def home():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))

    # get some of your saved universities
    columns = 'u.university_id, u.name, u.city, u.state, u.website, u.campus_location, u.total_enrollment'
    cur = mysql.connection.cursor()
    sql_query = "SELECT u.university_id, u.name, u.city, u.state, u.website, u.campus_location, u.total_enrollment FROM saved_universities s, university u WHERE s.user = %(username)s and s.university_id = u.university_id;"
    cur.execute(sql_query, {'username': session['username']})
    mysql.connection.commit()
    results = cur.fetchall()
    cur.close()
    universities = [UniversityCard(*school) for school in results]

    #get your personality type for majors

    cur = mysql.connection.cursor()
    sql_query = "SELECT major_type FROM user_major_type WHERE user = %(username)s"
    cur.execute(sql_query, {'username': session['username']})
    mysql.connection.commit()
    results = cur.fetchall()
    major_type = ""
    possible_majors = []
    if results:
        major_type = results[0][0]
        query = "SELECT major FROM majors_info WHERE type='" + str(major_type) + "'"

        cur.execute(query)
        data = cur.fetchall()
        type_info = get_major_type_info(major_type)
        possible_majors = {}

        for major in data:
            major = major[0]
            possible_majors[major] = possible_majors.get(major, None)


    return render_template("home.html", universities=universities, major_type=major_type, possible_majors=possible_majors)

#login window
@app.route(path + "/login", methods=['GET', 'POST'])
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
                        return redirect(url_for('home'))
                else:
                        return render_template('login.html', error='Username/password not found')

        if session.get('logged_in', False):
                return redirect(url_for('find_colleges'))

        if "error" in session:
            error = session["error"]
            del session["error"]
            return render_template('login.html', error=error)
        elif "result" in session:
            result = session["result"]
            del session["result"]
            return render_template('login.html', result=result)
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
                        return render_template('create_account.html', error='Username already in use. Please choose another.')
                else:
                        #insert into the database
                        cur.execute("INSERT INTO login_information(username, password) VALUES(%(new_username)s, %(new_password)s)",
                            {'new_username': new_username, 'new_password': new_password}
                        )
                        mysql.connection.commit()
                        session["result"] = "Account created successfully."
                        return redirect(url_for('login'))

                cur.close()

        if session.get('logged_in', False):
                return redirect(url_for('find_colleges'))

        return render_template('create_account.html')

# user settings window
@app.route(path + "/user_settings", methods = ["GET", "POST"])
def user_settings():
        if request.method == "POST":
                form_details = request.form
                cur = mysql.connection.cursor()

                #Update account password
                if form_details['submit_button'] == 'update':
                        old_password = form_details['oldpassword']
                        new_password = form_details['newpassword']

                        #check if information is correct
                        cur.execute("SELECT * from login_information where username = %(username)s and password = %(password)s", {'username': session["username"], 'password': old_password}
                        )
                        login_exists = cur.fetchall()

                        if len(login_exists) == 0:
                                return render_template('user_settings.html', username=session['username'], error='Incorrect account information. Account settings not saved.')
                        else:
                                cur.execute("UPDATE login_information SET password=%(new_password)s WHERE username=%(username)s", {'new_password': new_password, 'username': session["username"]})
                                mysql.connection.commit()
                                cur.close()
                                return render_template('user_settings.html', username=session['username'], result='Password updated.')

                #Delete Account
                elif form_details['submit_button'] == 'delete':
                        password = form_details['delete_pass']

                        #check if information is correct
                        cur.execute("SELECT * from login_information where username = %(username)s and password = %(password)s",
                            {'username': session['username'], 'password': password}
                        )
                        login_exists = cur.fetchall()

                        if len(login_exists) == 0:
                                return render_template('user_settings.html', username=session['username'], error='Incorrect account information. Account not deleted.')
                        else:
                                cur.execute("DELETE FROM login_information where username=%(username)s and password=%(password)s", {'username': session['username'], 'password': password})
                                mysql.connection.commit()
                                cur.close()
                                session["logged_in"] = False
                                del session["username"]
                                session["error"] = "Account Deleted."
                                return redirect(url_for('login'))

                elif form_details['submit_button'] == 'logout':
                        session["logged_in"] = False
                        if 'username' in session:
                            del session['username']
                        return redirect(url_for('login'))

        if not session.get('logged_in', False):
                return redirect(url_for('login'))

        return render_template("user_settings.html", username=session["username"])


@app.route(path + "/search", methods=["GET", "POST"])
def search_engine():
    if "uni_ids" in session:
        del session["uni_ids"]
    if request.method == "POST":
        parameters = request.form
        if 'term' in parameters and parameters['term']:
            term = parameters['term']
            sql_query  = "SELECT university_id FROM university WHERE name like %(term)s ORDER BY total_enrollment DESC LIMIT 21"
            print(sql_query)
            cur = mysql.connection.cursor()
            cur.execute(sql_query, {'term': "%" + term + "%"})
            results = cur.fetchall()
            uni_ids = []
            for i in results:
                uni_ids.append(i[0])
            if not uni_ids:
                return render_template("search_engine.html", error="No results found")
            session["uni_ids"] = uni_ids
            return redirect(url_for("results"))
        else:
            return render_template("search_engine.html", error="No search term")
    return render_template("search_engine.html")

@app.route(path + "/find", methods=["GET", "POST"])
def find_colleges():
    if "uni_ids" in session:
        del session["uni_ids"]
    if request.method == "POST":
        parameters = request.form
        sql_query, order = generate_query(parameters)
        cur = mysql.connection.cursor()
        cur.execute(sql_query)
        results = cur.fetchall()
        uni_ids = []
        for i in results:
            uni_ids.append(i[0])
        session["uni_ids"] = uni_ids
        return redirect(url_for("results"))
    if "error" in session:
        error = session["error"]
        del session["error"]
        return render_template("user_form.html", error=error)

    return render_template("user_form.html")

@app.route(path + "/results", methods=["GET", "POST"])
def results():
    ids = session.get("uni_ids", [])
    if not ids:
        session["error"] = "No universities found"
        return redirect(url_for('find_colleges'))
    sql_query = get_college_basic(ids)
    cur = mysql.connection.cursor()
    cur.execute(sql_query)
    results = cur.fetchall()
    universities = [UniversityCard(*school) for school in results]

    if request.method == 'POST':
        if not session.get('logged_in', False):
            return redirect(url_for('login'))
        university = request.form
        print(university['save'])
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO saved_universities(user, university_id) VALUES(%(username)s, %(save)s);", {'username': session['username'], 'save': university['save']})

        print('WORKED')
        mysql.connection.commit()
        cur.close()
    return render_template('results.html', universities=universities)

@app.route(path + "/saved_universities", methods=["GET", "POST"])
def saved_universities():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))

    if request.method == 'POST':
        university = request.form
        print(university['delete'])
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM saved_universities WHERE user = %s and university_id = %s;", (session['username'], university['delete']))
        mysql.connection.commit()
        cur.close()

    columns = 'u.university_id, u.name, u.city, u.state, u.website, u.campus_location, u.total_enrollment'
    cur = mysql.connection.cursor()
    sql_query = "SELECT u.university_id, u.name, u.city, u.state, u.website, u.campus_location, u.total_enrollment FROM saved_universities s, university u WHERE s.user = %s and s.university_id = u.university_id;"
    cur.execute(sql_query, [session['username']])
    mysql.connection.commit()
    results = cur.fetchall()
    cur.close()
    universities = [UniversityCard(*school) for school in results]
    return render_template('saved_universities.html', universities=universities)


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

        majors_list = list(parameters.listvalues())
        if majors_list:
            major_type, query = find_major(majors_list)
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM user_major_type wHERE user = %s",[session['username']])
            results = cur.fetchall()

            if len(results) == 0:
                print(results)
                cur.execute("INSERT INTO user_major_type(user, major_type) VALUES(%s, %s)", (session['username'], major_type))
            else:
                cur.execute("UPDATE user_major_type SET major_type=%s WHERE user=%s", (major_type, session['username']))
            mysql.connection.commit()

            cur.execute(query)
            data = cur.fetchall()
            type_info = get_major_type_info(major_type)
            possible_majors = {}

            with concurrent.futures.ThreadPoolExecutor() as e:
                future = [
                    e.submit(request_major_info, major, possible_majors)
                    for major in data
                ]
                for res in concurrent.futures.as_completed(future):
                    res.result()
                    
        else:
            return render_template('user_form_majors.html', error='Please enter preferences')
        return render_template('results_majors.html', major_type=major_type, major_info=type_info, type_stats=possible_majors, majors=data)

    return render_template("user_form_majors.html")

def request_major_info(major, possible_majors):
        major = major[0]
        possible_majors[major] = possible_majors.get(major, None)
        unpacked_args = get_major_info(major)
        if unpacked_args != "Not found":
                desc_text, classes, jobs, salaries = unpacked_args
                possible_majors[major] = (desc_text, classes, jobs, salaries)

nav.init_app(app)

if __name__ == "__main__":
        app.run(host="0.0.0.0", debug=True, port =5006)

