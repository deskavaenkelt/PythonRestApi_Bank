from flask import jsonify
from pymongo import MongoClient

client = MongoClient("mongodb://db:27017")
db = client.MoneyManagementDB
users = db["Users"]


def user_exist(username) -> bool:
    if users.find({"Username": username}).count() == 0:
        return False
    else:
        return True


def create_new_account(username, hashed_password):
    users.insert({
        "Username": username,
        "Password": hashed_password,
        "Own": 0,
        "Debt": 0
    })


def get_hashed_password(username) -> bytes:
    hashed_password = users.find({
        "Username": username
    })[0]["Password"]

    return hashed_password


def user_owned_amount(username) -> int:
    return users.find({
        "Username": username
    })[0]["Own"]


def user_debt_amount(username) -> int:
    return users.find({
        "Username": username
    })[0]["Debt"]


def update_account_balance(username, balance):
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


def get_user_balance(username):
    retJson = users.find({
        "Username": username
    }, {
        "Password": 0,  # projection
        "_id": 0
    })[0]

    return jsonify(retJson)


def delete_user_account(username):
    users.delete_one({
        "Username": username
    })


def get_all_users():
    retJson = users.find({})

    return jsonify(retJson)
