from flask import Flask, jsonify, request, render_template
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.MoneyManagementDB
users = db["Users"]


def user_exist(username):
    if users.find({"Username": username}).count() == 0:
        return False
    else:
        return True


class Register(Resource):
    def post(self):
        # Step 1 is to get posted data by the user
        postedData = request.get_json()

        # Get the data
        username = postedData["username"]
        password = postedData["password"]  # "123xyz"

        if user_exist(username):
            retJson = {
                'status': 301,
                'msg': 'Invalid Username'
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        # Store username and pw into the database
        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Own": 0,
            "Debt": 0
        })

        retJson = {
            "status": 200,
            "msg": "You successfully signed up for the API"
        }
        return jsonify(retJson)


def verify_pw(username, password):
    if not user_exist(username):
        return False

    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False


def cash_with_user(username):
    cash = users.find({
        "Username": username
    })[0]["Own"]
    return cash


def debt_with_user(username):
    debt = users.find({
        "Username": username
    })[0]["Debt"]
    return debt


def generate_return_dictionary(status, msg):
    retJson = {
        "status": status,
        "msg": msg
    }
    return retJson


def verify_credentials(username, password):
    if not user_exist(username):
        return generate_return_dictionary(301, "Invalid Username"), True

    correct_pw = verify_pw(username, password)

    if not correct_pw:
        return generate_return_dictionary(302, "Incorrect Password"), True

    return None, False


def update_account(username, balance):
    users.update({
        "Username": username
    }, {
        "$set": {
            "Own": balance
        }
    })


def update_debt(username, balance):
    users.update({
        "Username": username
    }, {
        "$set": {
            "Debt": balance
        }
    })


class Add(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        money = postedData["amount"]

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        if money <= 0:
            return jsonify(generate_return_dictionary(304, "The money amount entered must be greater than 0"))

        cash = cash_with_user(username)
        money -= 1  # Transaction fee
        # Add transaction fee to bank account
        bank_cash = cash_with_user("BANK")
        update_account("BANK", bank_cash + 1)

        # Add remaining to user
        update_account(username, cash + money)

        return jsonify(generate_return_dictionary(200, "Amount Added Successfully to account"))


class Transfer(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        to = postedData["to"]
        money = postedData["amount"]

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        cash = cash_with_user(username)
        if cash <= 0:
            return jsonify(generate_return_dictionary(303, "You are out of money, please Add Cash or take a loan"))

        if money <= 0:
            return jsonify(generate_return_dictionary(304, "The money amount entered must be greater than 0"))

        if not user_exist(to):
            return jsonify(generate_return_dictionary(301, "Recieved username is invalid"))

        cash_from = cash_with_user(username)
        cash_to = cash_with_user(to)
        bank_cash = cash_with_user("BANK")

        update_account("BANK", bank_cash + 1)
        update_account(to, cash_to + money - 1)
        update_account(username, cash_from - money)

        return jsonify(generate_return_dictionary(200, "Amount added successfully to account"))


class Balance(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        retJson = users.find({
            "Username": username
        }, {
            "Password": 0,  # projection
            "_id": 0
        })[0]

        return jsonify(retJson)


class TakeLoan(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data["username"]
        password = posted_data["password"]
        money = posted_data["amount"]

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        cash = cash_with_user(username)
        debt = debt_with_user(username)
        update_account(username, cash + money)
        update_debt(username, debt + money)

        return jsonify(generate_return_dictionary(200, "Loan Added to Your Account"))


class PayLoan(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data["username"]
        password = posted_data["password"]
        money = posted_data["amount"]

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        cash = cash_with_user(username)

        if cash < money:
            return jsonify(generate_return_dictionary(303, "Not Enough Cash in your account"))

        debt = debt_with_user(username)
        update_account(username, cash - money)
        update_debt(username, debt - money)

        return jsonify(generate_return_dictionary(200, "Loan Paid"))


api.add_resource(Register, '/register')
api.add_resource(Add, '/add')
api.add_resource(Transfer, '/transfer')
api.add_resource(Balance, '/balance')
api.add_resource(TakeLoan, '/takeloan')
api.add_resource(PayLoan, '/payloan')


@app.route('/')
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='80')
