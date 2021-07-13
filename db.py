import sqlite3


def get_info_on(user_id):
    cursor = sqlite3.connect("data/users.db").cursor()
    cursor.execute("SELECT * FROM users WHERE tid = {}".format(str(user_id)))
    db_result = cursor.fetchone()
    return db_result


def add_new_user(data):
    conn = sqlite3.connect("data/users.db")
    cursor = conn.cursor()

    dataset = (data["user_id"], data["name"], data["gender"], data["city"], data["interest"])
    cursor.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?);", dataset)
    conn.commit()
    return True
