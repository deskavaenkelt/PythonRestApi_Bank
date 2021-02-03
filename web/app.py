from flask import Flask, jsonify, request, render_template
from flask_restful import Api, Resource

from encryption import generate_hashed_password, verify_password
from messages import message_signup_success, message_user_fail, message_password_fail, \
    message_amount_added_successfully, message_amount_invalid, message_amount_insufficient, message_user_dont_exist, \
    message_loan_added_successfully, message_loan_paid_successfully, message_loan_paid_fail, message_user_deleted
from mongodb import user_exist, create_new_account, available_amount, debt_amount, update_account_balance, \
    update_debt, get_user_balance, delete_user_account, get_all_users
from posted_data import username_password, username_password_amount, username_password_to_amount

app = Flask(__name__)
api = Api(app)

BANK = "BANK"


class Register(Resource):
    def post(self):
        username, password = username_password(request.get_json())

        if user_exist(username):
            return message_user_fail()

        hashed_password = generate_hashed_password(password)
        create_new_account(username, hashed_password)

        return message_signup_success()


def verify_account(username, password) -> bool:
    if not user_exist(username):
        return False

    successful_verification = verify_password(username, password)
    return successful_verification


def verify_credentials(username, password):
    if not user_exist(username):
        return message_user_fail(), True

    correct_pw = verify_account(username, password)

    if not correct_pw:
        return message_password_fail(), True

    return None, False


class Add(Resource):
    def post(self):
        username, password, money = username_password_amount(request.get_json())

        ret_json, error = verify_credentials(username, password)
        if error:
            return jsonify(ret_json)

        if money <= 0:
            return message_amount_invalid()

        cash = available_amount(username)
        money -= 1  # Transaction fee
        # Add transaction fee to bank account
        bank_cash = available_amount(BANK)
        update_account_balance(BANK, bank_cash + 1)

        # Add remaining to user
        update_account_balance(username, cash + money)

        return message_amount_added_successfully()


class Transfer(Resource):
    def post(self):
        username, password, to, money = username_password_to_amount(request.get_json())

        ret_json, error = verify_credentials(username, password)
        if error:
            return jsonify(ret_json)

        cash = available_amount(username)
        if cash <= 0:
            return message_amount_insufficient()

        if money <= 0:
            return message_amount_invalid()

        if not user_exist(to):
            return message_user_dont_exist()

        cash_from = available_amount(username)
        cash_to = available_amount(to)
        bank_cash = available_amount(BANK)

        update_account_balance(BANK, bank_cash + 1)
        update_account_balance(to, cash_to + money - 1)
        update_account_balance(username, cash_from - money)

        return message_amount_added_successfully()


class Balance(Resource):
    def post(self):
        username, password = username_password(request.get_json())

        ret_json, error = verify_credentials(username, password)
        if error:
            return jsonify(ret_json)

        return get_user_balance(username)


class TakeLoan(Resource):
    def post(self):
        username, password, money = username_password_amount(request.get_json())

        ret_json, error = verify_credentials(username, password)
        if error:
            return jsonify(ret_json)

        cash = available_amount(username)
        debt = debt_amount(username)
        update_account_balance(username, cash + money)
        update_debt(username, debt + money)

        return message_loan_added_successfully()


class PayLoan(Resource):
    def post(self):
        username, password, money = username_password_amount(request.get_json())

        ret_json, error = verify_credentials(username, password)
        if error:
            return jsonify(ret_json)

        cash = available_amount(username)

        if cash < money:
            return message_loan_paid_fail()

        debt = debt_amount(username)
        update_account_balance(username, cash - money)
        update_debt(username, debt - money)

        return message_loan_paid_successfully()


class DeleteUser(Resource):
    def delete(self):
        username, password = username_password(request.get_json())

        existing_user = verify_account(username, password)

        if not existing_user:
            return message_user_dont_exist()

        delete_user_account(username)
        return message_user_deleted()


class AllUsers(Resource):
    def get(self):
        return get_all_users()


api.add_resource(Register, '/register')
api.add_resource(Add, '/add')
api.add_resource(Transfer, '/transfer')
api.add_resource(Balance, '/balance')
api.add_resource(TakeLoan, '/takeloan')
api.add_resource(PayLoan, '/payloan')
api.add_resource(DeleteUser, '/delete')
api.add_resource(AllUsers, '/all')


@app.route('/')
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='80')
