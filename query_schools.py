ENROLLMENT_BOUNDS = {
    0: [0, 5000],
    1: [5000, 15000],
    2: [15000, 30000],
    3: [30000, 10000000],
}

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
    location_str = "((" + " + ".join(location_order) + f") * {location_mult}) as location_score"

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
    academics_str = "(maj.majors_count + (" + " + ".join(academics_order) + f") * {academics_mult}) as academics_score"

    if academics_order:
        select_str = f"{select_str}, {academics_str}"
    else:
        select_str = f"{select_str}, 0 as academics_score"

    # Financial
    finance_order = []
    if tuition:
        if financial_aid:
            finance_order.append(f"SUM(fin.percent_given_aid >= 50) + SUM(fin.average_price_after_aid <= {tuition})")
        else:
            price_state = "in_state_price" if state_location == 1 else "out_of_state_price"
            finance_order.append(f"SUM(fin.{price_state} <= {tuition})")
    finance_str = "((" + " + ".join(finance_order) + f") * {finance_mult}) as finance_score"

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
    other_str = "((" + " + ".join(other_order) + f") * {other_mult}) as other_score"

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
    return f"{select_str}\n{from_str}\n{where_str}\n{group_str}\n{order_str}\n{limit_str};"
