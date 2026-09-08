def get_exam_date():

    return {
        "tool": "get_exam_date",
        "result": "Semester 5 examination starts on 15 November 2026."
    }


def get_practical_exam_date():

    return {
        "tool": "get_practical_exam_date",
        "result": "Practical examinations start on 5 November 2026."
    }


def get_fee_details():

    return {
        "tool": "get_fee_details",
        "result": (
            "Semester 5 tuition fee is 45000 INR. "
            "Examination fee is 2500 INR. "
            "Library fee is 1000 INR. "
            "Laboratory fee is 3000 INR. "
            "Total semester fee is 51500 INR."
        )
    }


def get_attendance_rule():

    return {
        "tool": "get_attendance_rule",
        "result": "Students must maintain a minimum attendance of 75%."
    }


def get_office_hours():

    return {
        "tool": "get_office_hours",
        "result": (
            "College office working hours are "
            "Monday to Friday, 9:00 AM to 4:30 PM."
        )
    }


def use_tool(question):

    question = question.lower()


    # ==========================================
    # PRACTICAL EXAM
    # ==========================================

    if (
        "practical" in question
        and "exam" in question
    ):

        return get_practical_exam_date()


    # ==========================================
    # SEMESTER EXAM
    # ==========================================

    if (
        "semester exam" in question
        or "exam date" in question
        or (
            "exam" in question
            and "when" in question
        )
    ):

        return get_exam_date()


    # ==========================================
    # FEES
    # ==========================================

    if (
        "fee" in question
        or "fees" in question
        or "payment" in question
        or "tuition" in question
    ):

        return get_fee_details()


    # ==========================================
    # ATTENDANCE
    # ==========================================

    if (
        "attendance" in question
        or "absent" in question
    ):

        return get_attendance_rule()


    # ==========================================
    # OFFICE
    # ==========================================

    if (
        "office" in question
        or "working hours" in question
    ):

        return get_office_hours()


    return None