from bs4 import BeautifulSoup
import re
import requests

ENROLLMENT_BOUNDS = {
    0: [0, 5000],
    1: [5000, 15000],
    2: [15000, 30000],
    3: [30000, 10000000],
}


def get_college_basic(uni_id_list):
    where_str = ''
    order_by_str = 'ORDER BY (CASE'
    counter = 1
    for id in uni_id_list:
        id_str = f'u.university_id = {id}'
        if len(where_str) > 0:
            where_str = f'{where_str} or {id_str}'
        else:
            where_str = f'{id_str}'

        order_by_str = f'{order_by_str} WHEN {id_str} THEN {counter}'
        counter += 1
    order_by_str = f'{order_by_str} END) ASC'

    columns = "u.university_id, u.name, u.city, u.state, u.website, u.campus_location, u.total_enrollment"
    query = f'SELECT {columns} FROM university u WHERE {where_str} {order_by_str};'
    print(query)
    return query


def get_college(uni_id):
    select_str = "SELECT u.university_id, u.name, u.city, u.state, u.website, u.campus_location, u.total_enrollment, si.control, si.religious, si.accepts_ap_credit, si.study_abroad, si.offers_rotc, si.has_football, si.has_basketball, si.ncaa_member, si.retention_rate, si.graduation_rate, adm.total_applicants, adm.total_admitted, adm.admission_rate, adm.male_applicants, adm.female_applicants, adm.male_admitted, adm.female_admitted, adm.sat_rw_25, adm.sat_rw_75, adm.sat_math_25, adm.sat_math_75, adm.act_25, adm.act_75, fin.in_state_price, fin.out_of_state_price, fin.average_price_after_aid, fin.percent_given_aid, di.percent_american_indian_native_alaskan, di.percent_asian, di.percent_hawaiian_pacific_islander, di.percent_black, di.percent_white, di.percent_hispanic, di.percent_other, di.percent_two_races"
    from_str = "FROM university as u, school_info as si, admission_stats as adm, financial_stats as fin, diversity_stats as di"
    where_str = f"WHERE u.university_id = {uni_id} AND u.university_id = si.university_id AND u.university_id = adm.university_id AND u.university_id = fin.university_id AND u.university_id = di.university_id"

    info_query = f"{select_str}\n{from_str}\n{where_str};"
    majors_query = f"SELECT program_name FROM academic_programs WHERE {uni_id} = university_id;"

    return info_query, majors_query


def generate_query(params):
    state = params.get('state')
    state_location = int(params.get('state_location'))
    campus_location = params.getlist('campus_location')
    size = params.getlist('enrollment')
    majors = params.getlist('study-fields')
    sat_math = int(params.get('sat_math'))
    sat_reading = int(params.get('sat_reading'))
    act = int(params.get('act'))
    tuition = int(params.get('tuition'))
    financial_aid = int(params.get('financial-aid'))
    religious = params.get('religious')
    ap_credit = params.get('ap_credit')
    study_abroad = params.get('study_abroad')
    offers_rotc = params.get('offers_rotc')
    ncaa = params.get('ncaa')

    # Multiple score by this much for each type
    location_mult = 6 - int(params.get('location_rank'))
    academics_mult = 6 - int(params.get('academics_rank'))
    finance_mult = 6 - int(params.get('finance_rank'))
    other_mult = 6 - int(params.get('other_rank'))

    # Initial SQL strings
    where_str = "WHERE u.university_id = si.university_id AND u.university_id = adm.university_id AND u.university_id = fin.university_id AND u.university_id = di.university_id"
    group_str = "GROUP BY u.university_id"

    select_str = "SELECT u.university_id, u.name, u.city, u.state, u.website, u.campus_location, u.total_enrollment"

    majors_query = ""
    if majors:
        majors_string = "(" + ",".join(majors) + ")"
        majors_query = f"""
        , (SELECT uni.university_id, COUNT(a.cip_code) as majors_count
        FROM university as uni, academic_programs as a
        WHERE uni.university_id = a.university_id AND a.cip_code IN {majors_string}
        GROUP BY uni.university_id
        ORDER BY majors_count
        ) as maj
        """
        where_str = f"{where_str} AND u.university_id = maj.university_id"

    from_str = f"FROM university as u, school_info as si, admission_stats as adm, financial_stats as fin, diversity_stats as di {majors_query}"

    # State selection
    location_order = []
    if state_location == 0:
        location_order.append(f"(SUM(u.state = '{state}'))")
    elif state_location == 1:
        location_order.append(f"(SUM(u.state = '{state}') * 3)")
    elif state_location == 2:
        location_order.append(f"SUM(u.state = '{state}')")

    # Campus location and enrollment
    if campus_location:
        location_str = "('" + "', '".join(campus_location) + "')"
        location_order.append(f"SUM(u.campus_location IN {location_str})")
    if size:
        lower_bound = ENROLLMENT_BOUNDS[int(min(size))][0]
        upper_bound = ENROLLMENT_BOUNDS[int(max(size))][1]
        location_order.append(f"SUM(u.total_enrollment >= {lower_bound})")
        location_order.append(f"SUM(u.total_enrollment <= {upper_bound})")
    location_str = "((" + " + ".join(location_order) + \
        f") * {location_mult}) as location_score"

    if location_order:
        select_str = f"{select_str}, {location_str}"
    else:
        select_str = f"{select_str}, 0 as location_score"

    # SAT/ACT Scores
    academics_order = []
    if sat_math > 200:
        academics_order.append(f"SUM(adm.sat_math_25 <= {sat_math})")
    if sat_reading > 200:
        academics_order.append(f"SUM(adm.sat_rw_25 <= {sat_reading})")
    if act > 1:
        academics_order.append(f"SUM(adm.act_25 <= {act})")
    if majors:
        academics_str = "(maj.majors_count + (" + " + ".join(academics_order) + \
            f") * {academics_mult}) as academics_score"
    else:
        academics_str = "((" + " + ".join(academics_order) + \
            f") * {academics_mult}) as academics_score"

    if academics_order:
        select_str = f"{select_str}, {academics_str}"
    else:
        select_str = f"{select_str}, 0 as academics_score"

    # Financial
    finance_order = []
    if tuition:
        if financial_aid:
            finance_order.append(
                f"SUM(fin.percent_given_aid >= 50) + SUM(fin.average_price_after_aid <= {tuition})")
        else:
            price_state = "in_state_price" if state_location == 1 else "out_of_state_price"
            finance_order.append(f"SUM(fin.{price_state} <= {tuition})")
    finance_str = "((" + " + ".join(finance_order) + \
        f") * {finance_mult}) as finance_score"

    if finance_order:
        select_str = f"{select_str}, {finance_str}"
    else:
        select_str = f"{select_str}, 0 as finance_score"

    # Other preferences
    other_order = []
    if religious is not None:
        if int(religious):
            other_order.append("SUM(si.religious = 1)")
        else:
            other_order.append("SUM(si.religious = 0)")
    if ap_credit is not None and int(ap_credit):
        other_order.append("SUM(si.accepts_ap_credit = 1)")
    if study_abroad is not None and int(study_abroad):
        other_order.append("SUM(si.study_abroad = 1)")
    if offers_rotc is not None and int(offers_rotc):
        other_order.append("SUM(si.offers_rotc = 1)")
    if ncaa is not None and int(ncaa):
        other_order.append("SUM(si.ncaa_member = 1)")
    other_str = "((" + " + ".join(other_order) + \
        f") * {other_mult}) as other_score"

    if other_order:
        select_str = f"{select_str}, {other_str}"
    else:
        select_str = f"{select_str}, 0 as other_score"

    # Academic priority
    order_str = "ORDER BY"
    ranks = {
        location_mult: "location_score DESC",
        academics_mult: "academics_score DESC",
        finance_mult: "finance_score DESC",
        other_mult: "other_score DESC",
    }
    order = [ranks[rank] for rank in range(5, 1, -1)]
    order_str = "ORDER BY " + ", ".join(order) + ", u.name ASC"

    limit_str = "LIMIT 21"

    columns = "university_id, name, city, state, website, campus_location, total_enrollment"
    return (f"{select_str}\n{from_str}\n{where_str}\n{group_str}\n{order_str}\n{limit_str};", order)


def find_major(majors_list):
    # second advanced function
    # NOTE: this does not seem too advanced, so maybe we can parse each major / type to describe what it is
    # calculate quiz output
    major_dict = {}
    for l in majors_list:
        for major in l:
            major_dict[major] = major_dict.get(major, 0) + 1
    major_type = max(major_dict, key=major_dict.get)

# query for majors based on type
    query = "SELECT major FROM majors_info WHERE type='" + \
        str(major_type) + "'"
    return major_type, query


def get_major_type_info(major):
    URL = "https://acd.iupui.edu/explore/choose-your-major/connect-majors-to-careers/interests/" + \
        major.lower() + "/index.html"
    html_text = requests.get(URL).text
    soup = BeautifulSoup(html_text, 'html.parser')

    sub_title = str(soup.find('h3'))[4:-5]

    desc = str(soup.find_all('div', class_="text", string=re.compile("These")))
    desc = desc.split('. ', 1)[1]
    desc = desc.split(' If not,')[0]

    return sub_title, desc


def get_major_info(major_name):
    major_path = "https://www.mymajors.com/college-majors/"
    name = re.sub("[^a-zA-z]+", " ", major_name)
    major = "-".join(name.lower().split())
    url = major_path + major

    page = requests.get(url).text

    default_text = "A general program that focuses on law and legal issues from the perspective of the social sciences and humanities."
    soup = BeautifulSoup(page, "html.parser")
    desc = soup.find("p", {"class": "lead"}).get_text()
    desc_text = desc.split('\n')[1].strip()
    if desc_text == default_text:
        return "Not found"
    class_list = soup.find("ul", {"class": "cols3"})
    if type(class_list) == None:
        return "Not found"

    class_list = class_list.get_text().strip().split('\n')
    classes = [cl.strip() for cl in class_list if cl.strip()]

    career_url = "https://www.mymajors.com/careers/" + major + "-major"
    careers_page = requests.get(career_url).text

    soup = BeautifulSoup(careers_page, "html.parser")
    job_list = soup.find("ul", {"class": "cols2"}
                         )
    if job_list != None:
        job_list = job_list.get_text().strip().split('\n')
    else:
        return "Not Found"
    jobs = [job.strip() for job in job_list if job.strip()]

    salary_data = soup.find_all("td")
    salaries = {}
    for i in range(0, len(salary_data), 2):
        label = salary_data[i].get_text().strip()
        salary = salary_data[i+1].get_text().strip()
        salaries[label] = salary

    return desc_text, classes, jobs, salaries
