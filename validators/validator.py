import re

def is_password_strong(password):
    password_regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,20}$')
    return re.match(password_regex, password)


def is_login_valid(user_id):
    return 5 <= len(user_id) <= 20