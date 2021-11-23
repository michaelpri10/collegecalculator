def generate_query(parameters):
    university = {
        "state": [], # [] - no filter, else list of states
        "campus_location": [], # [] - no filter, else list of City/Town/Suburb/Rural
        "total_enrollment": [], # [] - no preference, 0 - 0-1000 1 - 1000-5000, 2 - 5000-10000, 3 - 10000-25000, 4 - 25001+
    }

    school_info = {
        "control": 0, # 0 - no preference, 1 - public, 2 - private
        "religious": 0, # 0 - no preference, 1 - religious, 2 - not religious
        "ap_credit": 0, # 0 - no preference, 1 - yes, 2 - no
        "study_abroad": 0, # 0 - no preference, 1 - yes, 2 - no
        "offers_rotc": 0, # 0 - no preference, 1 - yes, 2 - no
        "has_football": 0, # 0 - no preference, 1 - yes, 2 - no
        "has_basketball": 0, # 0 - no preference, 1 - yes, 2 - no
        "ncaa_member": 0, # 0 - no preference, 1 - yes, 2 - no
        "retention_rate": 0, # 0 - no threshold, any other is a threshold
        "graduation_rate": 0, # 0 - no threshold, any other is a threshold
    }

    admission_stats = {
        "total_applicants": 0, # 0 - no threshold, any other is a threshold
        "admission_rate": [], # [] - no threshold, 0 - 0-10%, 1 - 10-20%, 2 - 20-30%, 3 - 30-50%, 4 - 50-75%, 5 - 75-100%
        "sat_reading": 0, # 0 - no bounds, take other scores check between 25%
        "sat_math": 0, # same 
        "act": 0, # same
    }

    financial_stats = {
        "in_state_price": 0, # 0 - no threshold, any other is a threshold
        "out_of_state_price": 0, # 0 - no threshold, any other is a threshold
        "average_price_after_aid": 0, # 0 - no threshold, any other is a threshold
        "percent_given_aid": 0, # 0 - no threshold, any other is a threshold
    }

    for field in university:
        university[field] = parameters.getlist(field)

    for field in school_info:
        param = parameters.get(field)
        if param.isdigit():
            school_info[field] = int(param)
        else:
            school_info[field] = 0
    
    for field in admission_stats:
        if field == 'admission_rate':
            admission_stats[field] = [int(i) for i in parameters.getlist(field)]
        else:
            param = parameters.get(field)
            if param.isdigit():
                admission_stats[field] = int(param)
            else:
                admission_stats[field] = 0

    for field in financial_stats:
        param = parameters.get(field)
        if param.isdigit():
            financial_stats[field] = int(param)
        else:
            financial_stats[field] = 0

    return build_query_string(university, school_info, admission_stats, financial_stats)

ENROLLMENT_BOUNDS = {
    0: [0, 5000],
    1: [5000, 15000],
    2: [15000, 30000],
    3: [30000, 10000000],
}

ADMISSION_BOUNDS = {
    0: [0, 10],
    1: [10, 20],
    2: [20, 30],
    3: [30, 50],
    4: [50, 75],
    5: [75, 100]
}

def build_query_string(university, school_info, admission_stats, financial_stats):
    select_str = "SELECT u.name, u.city, u.state, u.website, u.total_enrollment, si.control, si.religious, si.accepts_ap_credit, si.study_abroad, si.offers_rotc, si.has_football, si.has_basketball, si.ncaa_member, si.retention_rate, si.graduation_rate, adm.total_applicants, adm.total_admitted, adm.admission_rate, adm.male_applicants, adm.female_applicants, adm.male_admitted, adm.female_admitted, adm.sat_rw_25, adm.sat_rw_75, adm.sat_math_25, adm.sat_math_75, adm.act_25, adm.act_75, fin.in_state_price, fin.out_of_state_price, fin.average_price_after_aid, fin.percent_given_aid, di.percent_american_indian_native_alaskan, di.percent_asian, di.percent_hawaiian_pacific_islander, di.percent_black, di.percent_white, di.percent_hispanic, di.percent_other, di.percent_two_races"

    from_str = "FROM university as u, school_info as si, admission_stats as adm, financial_stats as fin, diversity_stats as di"
    where_str = "WHERE u.university_id = si.university_id AND u.university_id = adm.university_id AND u.university_id = fin.university_id AND u.university_id = di.university_id AND"
    group_str = "GROUP BY u.university_id"
    order_str = "ORDER BY u.name ASC"

    # General university filters
    if len(university["state"]):
        states = "'" + "', '".join(university["state"]) + "'"
        where_str = f"{where_str} u.state IN ({states}) AND"
    if len(university["campus_location"]):
        locations = "'" + "', '".join(university["campus_location"]) + "'"
        where_str = f"{where_str} u.campus_location IN ({locations}) AND"
    if len(university["total_enrollment"]):
        lower_bound = ENROLLMENT_BOUNDS[min(university["total_enrollment"])][0]
        upper_bound = ENROLLMENT_BOUNDS[max(university["total_enrollment"])][1]
        where_str = f"{where_str} u.total_enrollment >= {upper_bound} AND u.total_enrollment <= {upper_bound} AND"


    # School info filters
    if school_info["control"]:
        control = "'Public'" if school_info["control"] == 1 else "'Private'"
        where_str = f"{where_str} si.control = {control} AND"
    if school_info["religious"]:
        religious = 1 if school_info["religious"] == 1 else 0
        where_str = f"{where_str} si.religious = {religious} AND"
    if school_info["ap_credit"]:
        ap_credit = 1 if school_info["ap_credit"] == 1 else 0
        where_str = f"{where_str} si.accepts_ap_credit = {ap_credit} AND"
    if school_info["study_abroad"]:
        study_abroad = 1 if school_info["study_abroad"] == 1 else 0
        where_str = f"{where_str} si.study_abroad = {study_abroad} AND"
    if school_info["offers_rotc"]:
        offers_rotc = 1 if school_info["offers_rotc"] == 1 else 0
        where_str = f"{where_str} si.offers_rotc = {offers_rotc} AND"
    if school_info["has_football"]:
        has_football = 1 if school_info["has_football"] == 1 else 0
        where_str = f"{where_str} si.has_football = {has_football} AND"
    if school_info["has_basketball"]:
        has_basketball = 1 if school_info["has_basketball"] == 1 else 0
        where_str = f"{where_str} si.has_basketball = {has_basketball} AND"
    if school_info["ncaa_member"]:
        ncaa_member = 1 if school_info["ncaa_member"] == 1 else 0
        where_str = f"{where_str} si.ncaa_member = {ncaa_member} AND"
    if school_info["retention_rate"]:
        where_str = f"{where_str} si.retention_rate >= {school_info['retention_rate']} AND"
    if school_info["graduation_rate"]:
        where_str = f"{where_str} si.graduation_rate >= {school_info['graduation_rate']} AND"

    # Financial stat filters
    for field in financial_stats:
        if financial_stats[field]:
            where_str = f"{where_str} fin.{field} <= {financial_stats[field]} AND"

    #  Admission stat filters
    if admission_stats["total_applicants"]:
        where_str = f"{where_str} adm.total_applicants <= {admission_stats['total_applicants']} AND"
    if len(admission_stats["admission_rate"]):
        print(admission_stats["admission_rate"])
        lowest_choice = min(admission_stats["admission_rate"])
        highest_choice = max(admission_stats["admission_rate"])
        lower_bound = 0
        upper_bound = 100
        if lowest_choice in ADMISSION_BOUNDS:
            lower_bound = ADMISSION_BOUNDS[lowest_choice][0]
        if highest_choice in ADMISSION_BOUNDS:
            upper_bound = ADMISSION_BOUNDS[highest_choice][1]
        where_str = f"{where_str} adm.admission_rate >= {lower_bound} AND adm.admission_rate <= {upper_bound} AND"

    if admission_stats["sat_reading"]:
        score = admission_stats["sat_reading"]
        where_str = f"{where_str} adm.sat_rw_25 <= {score} AND"
    if admission_stats["sat_math"]:
        score = admission_stats["sat_math"]
        where_str = f"{where_str} adm.sat_math_25 <= {score} AND"
    if admission_stats["act"]:
        score = admission_stats["sat_math"]
        where_str = f"{where_str} adm.act_25 <= {score} AND"

    # Take off AND at end of WHERE block
    where_str = where_str[:-4]
    columns = [i.split('.')[1] for i in select_str.split(' ', 1)[1].split(', ')]

    return (columns, f"{select_str}\n{from_str}\n{where_str}\n{group_str}\n{order_str};")
