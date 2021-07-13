import config, db
import sqlite3
from utility import *
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackQueryHandler

#CALLBACK_GOOD = "good"
#CALLBACK_BAD = "bad"

#GOOD_STICKER = "CAACAgIAAxkBAAJX_16nCRx3_yNcHjGJJ8UkEk62o0MTAAIXAAN_gBAunKNhxU-S6OIZBA"
#BAD_STICKER = "CAACAgIAAxkBAAJYAV6nCSUZKTelneyyMG6wcXKM5u4VAAImAAN_gBAuCDLXyOyP3gYZBA"


# Два массива отвечают за то, на какой стадии диалога с ботом находится юзер из конкретного чата
# chat_id: <str>
CHAT_STATUS = {}

# chat_id: <int>
CHAT_PHASE = {}

# user_id: <dict>
TMP_USR_INF = {}

# chat_id: <list>
TMP_KEYBOARD_MESS = {}


def create_cursor():
    global MAIN_CONNECTION
    return MAIN_CONNECTION.cursor()


def add_message_to_clearance(chat_id, message):
    if chat_id in TMP_KEYBOARD_MESS.keys():
        TMP_KEYBOARD_MESS[chat_id].append(message)
    else:
        TMP_KEYBOARD_MESS[chat_id] = [message]


def clear_keyboards(chat_id):
    for i in TMP_KEYBOARD_MESS[chat_id]:
        i.edit_reply_markup(reply_markup=None)
    TMP_KEYBOARD_MESS[chat_id] = []


def delete_keyboard(query):
    # Убираем клаву с прошлого сообщения бота
    query.edit_message_text(
        text=query.message.text
    )

""""
def generate_keyboard():
    keyboard = [
        [InlineKeyboardButton("Хорошо", callback_data=CALLBACK_GOOD),
         InlineKeyboardButton("Плохо", callback_data=CALLBACK_BAD)]
    ]

    return InlineKeyboardMarkup(keyboard)
"""


def regulate_profile(update: Update, context, query=None, current_call=None):
    chid = update.effective_message.chat_id
    user = update.effective_user
    us_id = update.effective_user.id

    if CHAT_PHASE[chid] == 1:

        replies = {GENDER_CALLS["MALE_CALL"]: "В мужском", GENDER_CALLS["FEMALE_CALL"]: "В женском",
                   LEAVE_NOW_CALL: "Оставить как есть"}
        reply = replies[current_call]

        # убираем клаву
        delete_keyboard(query)

        # Подтверждаем для пользователя его выбор
        context.bot.send_message(
            chat_id=chid,
            text=reply
        )

        # Записываем изменения для пользователя
        if current_call in GENDER_CALLS.values():
            TMP_USR_INF[us_id]["gender"] = current_call

        CHAT_PHASE[chid] = 2
        # Начинаем следующую фазу - имя
        new_message = context.bot.send_message(
            chat_id=chid,
            text="Хорошо. Теперь напиши свое имя и фамилию в одну строку и нажми 'Отправить'\n\nПример: Сергей Орлов\n\n"
                 "Текущее использующееся имя: {} {}".format(user.first_name, user.last_name),
            reply_markup=generate_name_keys(check_user_in_db(us_id))
        )
        add_message_to_clearance(chid, new_message)

    elif CHAT_PHASE[chid] == 2:
        if query != None:
            delete_keyboard(query)
            TMP_USR_INF[us_id]["name"] = "{} {}".format(user.first_name, user.last_name)
        else:
            clear_keyboards(chid)
            TMP_USR_INF[us_id]["name"] = update.effective_message.text

        context.bot.send_message(
            chat_id=chid,
            text="OK, SPASIBO"
        )
        print(TMP_USR_INF)


def keyboard_regulate(update: Update, context):
    query = update.callback_query
    current_callback = query.data
    chid = update.effective_message.chat_id
    #us_id = update.effective_user.id

    # Работа с профилем пользователя
    if CHAT_STATUS[chid] == STATUS["PROFILE"]:
        regulate_profile(update, context, query, current_callback)


def texting(update: Update, context):
    chid = update.effective_message.chat_id
    if CHAT_STATUS[chid] == STATUS["PROFILE"]:
        regulate_profile(update, context)



def check_user_in_db(user_id):
    mc = sqlite3.connect("data/users.db").cursor()
    mc.execute("SELECT * FROM users WHERE tid = {}".format(str(user_id)))
    db_result = mc.fetchone()
    return db_result


def profile(update: Update, context):
    user_id = update.effective_user.id
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=f"Привет, {str(user_id)}!\nКак твои дела?"
    )


def generate_name_keys(user_info):
    if user_info == None:
        keyboard = [
            [InlineKeyboardButton("Оставить текущее имя", callback_data=LEAVE_NOW_CALL)]
        ]

    return InlineKeyboardMarkup(keyboard)


def generate_gender_keys(user_info):
    if user_info == None:
        keyboard = [
            [InlineKeyboardButton("В мужском", callback_data=GENDER_CALLS["MALE_CALL"]),
             InlineKeyboardButton("В женском", callback_data=GENDER_CALLS["FEMALE_CALL"])]
        ]

    return InlineKeyboardMarkup(keyboard)



def start(update: Update, context):
    user = update.effective_user
    ch_id = update.effective_message.chat_id
    user_name = user.first_name
    db_result = check_user_in_db(user.id)  # результат

    if db_result != None:
        context.bot.send_message(
            chat_id=ch_id,
            text=f"Привет, {str(user_name)}!\n Как твои дела?"
        )

    else:
        context.bot.send_message(
            chat_id=ch_id,
            text="Привет! Ты, похоже, здесь впервые, верно? Прежде, чем я начну тебе помогать, давай познакомимся!️"
        )
        context.bot.send_message(
            chat_id=ch_id,
            text="В каком роде я могу к тебе обращаться?",
            reply_markup=generate_gender_keys(db_result)
        )
        TMP_USR_INF[user.id] = {}
        CHAT_STATUS[ch_id] = STATUS["PROFILE"]
        CHAT_PHASE[ch_id] = 1


def main():
    global MAIN_CONNECTION, MAIN_CURSOR
    my_update = Updater(
        token=config.TOKEN,
        #base_url=config.PROXI,
        use_context=True
    )

    MAIN_CONNECTION = sqlite3.connect("data/users.db")
    MAIN_CURSOR = MAIN_CONNECTION.cursor()

    keyboard_handler = CallbackQueryHandler(callback=keyboard_regulate, pass_chat_data=True)
    text_handler = MessageHandler(Filters.all, texting)
    start_handler = CommandHandler("start", start)
    profile_handler = CommandHandler("profile", profile)

    my_update.dispatcher.add_handler(keyboard_handler)
    my_update.dispatcher.add_handler(start_handler)
    my_update.dispatcher.add_handler(profile_handler)
    my_update.dispatcher.add_handler(text_handler)

    my_update.start_polling()
    my_update.idle()


if __name__ == "__main__":
    main()