import sqlite3
import config


def get_info_on(user_id):
    conn = sqlite3.connect(config.DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE tid = {}".format(str(user_id)))
    db_result = cursor.fetchone()
    if db_result != None:
        new_result = {}
        keys = ["user_id", "name", "gender", "city", "interest"]
        counter = 0
        for i in db_result:
            new_result[keys[counter]] = i
            counter += 1
        db_result = new_result
    conn.close()
    return db_result


def patch_one_user(data):
    conn = sqlite3.connect(config.DB)
    cursor = conn.cursor()

    for key in data.keys():
        if key != "user_id":
            cursor.execute("UPDATE users set {} = ? where tid = ?".format(key), (data[key], data["user_id"]))

    conn.commit()
    conn.close()
    return True


def add_new_user(data):
    conn = sqlite3.connect(config.DB)
    cursor = conn.cursor()

    dataset = (data["user_id"], data["name"], data["gender"], data["city"], data["interest"])
    cursor.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?);", dataset)
    conn.commit()
    conn.close()
    return True
