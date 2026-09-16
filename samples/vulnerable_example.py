"""A deliberately vulnerable and messy file, used to test both agents."""

import sqlite3
import subprocess

API_KEY = "sk-live-abc123hardcodedsecret"  # hardcoded secret


def get_user(username):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # SQL injection: user input concatenated directly into query
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchone()


def run_backup(filename):
    # command injection: shell=True with unsanitized input
    subprocess.call("tar -cvf backup.tar " + filename, shell=True)


def load_config(path):
    # unsafe deserialization
    import pickle
    with open(path, "rb") as f:
        return pickle.load(f)


def process_order(order_id, user_id, product_id, quantity, discount_code, shipping_address, gift_wrap):
    # too many parameters, deep nesting, no docstring
    if order_id:
        if user_id:
            if product_id:
                for i in range(quantity):
                    if discount_code:
                        if shipping_address:
                            print("processing")
    return True


class orderManager:
    def __init__(self):
        self.orders = []
