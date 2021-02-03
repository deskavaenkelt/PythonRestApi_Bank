USERNAME = "username"
PASSWORD = "password"
AMOUNT = "amount"
TO = "to"


def username_password(posted_data) -> tuple:
    """
    :param posted_data:
    :return: username, password
    """
    username = posted_data[USERNAME]
    password = posted_data[PASSWORD]
    return username, password


def username_password_amount(posted_data) -> tuple:
    """
    :param posted_data:
    :return: username, password, money
    """
    username = posted_data[USERNAME]
    password = posted_data[PASSWORD]
    money = posted_data[AMOUNT]
    return username, password, money


def username_password_to_amount(posted_data) -> tuple:
    """
    :param posted_data:
    :return: username, password, to, money
    """
    username = posted_data[USERNAME]
    password = posted_data[PASSWORD]
    money = posted_data[AMOUNT]
    to = posted_data[TO]
    return username, password, to, money
