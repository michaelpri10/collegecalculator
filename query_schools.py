school_info = {
    "control": 0, # 0 - no preference, 1 - public, 2 - private
    "religious": 1, # 0 - no preference, 1 - religious, 2 - not religious
    "ap_credit": 1, # 0 - no preference, 1 - yes, 2 - no
    "study_abroad": 1, # 0 - no preference, 1 - yes, 2 - no
    "offers_rotc": 1, # 0 - no preference, 1 - yes, 2 - no
    "has_football": 1, # 0 - no preference, 1 - yes, 2 - no
    "has_basketball": 1, # 0 - no preference, 1 - yes, 2 - no
    "ncaa_member": 1, # 0 - no preference, 1 - yes, 2 - no
    "retention_rate": 70, # 0 - no threshold, any other is a threshold
    "graduation_rate": 70, # 0 - no threshold, any other is a threshold
}

admission_stats = {
    "total_applicants": 0, # 0 - no threshold, any other is a threshold
    "admission_rate": [], # [] - no threshold, 0 - 0-10%, 1 - 10-20%, 2 - 20-30%, 3 - 30-50%, 4 - 50-75%, 5 - 75-100%
    "sat_reading": 740, # 0 - no bounds, take other scores check between 25%
    "sat_math": 740, # same 
    "act": 0, # same
}

financial_stats = {
    "in_state_price": 0, # 0 - no threshold, any other is a threshold
    "out_of_state_price": 0, # 0 - no threshold, any other is a threshold
    "average_price_after_aid": 0, # 0 - no threshold, any other is a threshold
    "percent_given_aid": 0, # 0 - no threshold, any other is a threshold
}

university = {
    "state": ['PA', 'IN', 'NY', 'NJ', 'FL', 'CA', 'MA'], # [] - no filter, else list of states
    "campus_location": [], # [] - no filter, else list of City/Town/Suburb/Rural
    "total_enrollment": [], # [] - no preference, 0 - 0-1000 1 - 1000-5000, 2 - 5000-10000, 3 - 10000-25000, 4 - 25001+
}

ENROLLMENT_BOUNDS = {
    0: [0, 1000],
    1: [1000, 5000],
    2: [5000, 10000],
    3: [10000, 25000],
    4: [25000, 10000000],
}

ADMISSION_BOUNDS = {
    1: [0, 10],
    2: [10, 20],
    3: [20, 30],
    4: [30, 50],
    5: [50, 75],
    6: [75, 100]
}

def build_query_string(university, school_info, admission_stats, financial_stats):
    select_str = "SELECT u.name, u.city, u.state, u.website, u.total_enrollment"
    from_str = "FROM university as u"
    where_str = "WHERE"
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
    add_table = False
    if school_info["control"]:
        add_table = True
        control = "'Public'" if school_info["control"] == 1 else "'Private'"
        where_str = f"{where_str} si.control = {control} AND"
    if school_info["religious"]:
        add_table = True
        religious = 1 if school_info["religious"] == 1 else 0
        where_str = f"{where_str} si.religious = {religious} AND"
    if school_info["ap_credit"]:
        add_table = True
        ap_credit = 1 if school_info["ap_credit"] == 1 else 0
        where_str = f"{where_str} si.accepts_ap_credit = {ap_credit} AND"
    if school_info["study_abroad"]:
        add_table = True
        study_abroad = 1 if school_info["study_abroad"] == 1 else 0
        where_str = f"{where_str} si.study_abroad = {study_abroad} AND"
    if school_info["offers_rotc"]:
        add_table = True
        offers_rotc = 1 if school_info["offers_rotc"] == 1 else 0
        where_str = f"{where_str} si.offers_rotc = {offers_rotc} AND"
    if school_info["has_football"]:
        add_table = True
        has_football = 1 if school_info["has_football"] == 1 else 0
        where_str = f"{where_str} si.has_football = {has_football} AND"
    if school_info["has_basketball"]:
        add_table = True
        has_basketball = 1 if school_info["has_basketball"] == 1 else 0
        where_str = f"{where_str} si.has_basketball = {has_basketball} AND"
    if school_info["ncaa_member"]:
        add_table = True
        ncaa_member = 1 if school_info["ncaa_member"] == 1 else 0
        where_str = f"{where_str} si.ncaa_member = {ncaa_member} AND"
    if school_info["retention_rate"]:
        add_table = True
        where_str = f"{where_str} si.retention_rate >= {school_info['retention_rate']} AND"
    if school_info["graduation_rate"]:
        add_table = True
        where_str = f"{where_str} si.graduation_rate >= {school_info['graduation_rate']} AND"
    if add_table:
        from_str = f"{from_str}, school_info as si"
        where_str = f"{where_str} u.university_id = si.university_id AND"
        select_str = f"{select_str}, si.control, si.religious, si.accepts_ap_credit, si.study_abroad, si.offers_rotc, si.has_football, si.has_basketball, si.ncaa_member, si.retention_rate, si.graduation_rate"


    # Financial stat filters
    add_table = False
    for field in financial_stats:
        if financial_stats[field]:
            add_table = True
            where_str = f"{where_str} fin.{field} <= {financial_stats[field]} AND"
    if add_table:
        from_str = f"{from_str}, financial_stats as fin"
        where_str = f"{where_str} u.university_id = fin.university_id AND"
        select_str = f"{select_str}, fin.in_state_price, fin.out_of_state_price, fin.average_price_after_aid, fin.percent_given_aid"

    #  Admission stat filters
    add_table = False
    if admission_stats["total_applicants"]:
        add_table = True
        where_str = f"{where_str} adm.{field} <= {admission_stats['total_applicants']} AND"
    if len(admission_stats["admission_rate"]):
        add_table = True
        lower_bound = ADMISSION_BOUNDS[min(admission_stats["admission_rate"])][0]
        upper_bound = ADMISSION_BOUNDS[max(admission_stats["admission_rate"])][1]
        where_str = f"{where_str} adm.admission_rate >= {lower_bound} AND adm.admission_rate <= {upper_bound} AND"

    if admission_stats["sat_reading"]:
        add_table = True
        score = admission_stats["sat_reading"]
        where_str = f"{where_str} adm.sat_rw_25 <= {score} AND"
    if admission_stats["sat_math"]:
        add_table = True
        score = admission_stats["sat_math"]
        where_str = f"{where_str} adm.sat_math_25 <= {score} AND"
    if admission_stats["act"]:
        add_table = True
        score = admission_stats["sat_math"]
        where_str = f"{where_str} adm.act <= {score} AND"

    if add_table:
        from_str = f"{from_str}, admission_stats as adm"
        where_str = f"{where_str} u.university_id = adm.university_id AND"
        select_str = f"{select_str}, adm.total_applicants, adm.total_admitted, adm.admission_rate, adm.male_applicants, adm.female_applicants, adm.male_admitted, adm.female_admitted, adm.sat_rw_25, adm.sat_rw_75, adm.sat_math_25, adm.sat_math_75, adm.act_25, adm.act_75"

    if where_str.endswith(" AND"):
        where_str = where_str[:-4]

    return f"{select_str} {from_str} {where_str} {group_str} {order_str};"


# print(build_query_string(university, school_info, admission_stats, financial_stats))
