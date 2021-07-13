import config, db
from db import *
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


def clear_list_of_keyboards(chat_id):
    TMP_KEYBOARD_MESS[chat_id] = []


def delete_keyboard(query):
    # Убираем клаву с прошлого сообщения бота
    query.edit_message_text(
        text=query.message.text
    )


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

        message = "Хорошо. Теперь напиши свое имя и фамилию в одну строку и нажми 'Отправить'\n\nПример: Сергей Орлов\n\n"
        user_info = get_info_on(us_id)
        if user_info == None:
            message += "Текущее использующееся имя: {} {}".format(user.first_name, user.last_name)
        else:
            message += "Текущее использующееся имя: {}".format(user_info["name"])

        # Начинаем следующую фазу - имя
        new_message = context.bot.send_message(
            chat_id=chid,
            text=message,
            reply_markup=generate_name_keys(get_info_on(us_id))
        )
        add_message_to_clearance(chid, new_message)
        CHAT_PHASE[chid] = 2

    elif CHAT_PHASE[chid] == 2:
        if query != None:
            delete_keyboard(query)
            clear_list_of_keyboards(chid)
            if get_info_on(us_id) == None:
                TMP_USR_INF[us_id]["name"] = "{} {}".format(user.first_name, user.last_name)
        else:
            clear_keyboards(chid)
            TMP_USR_INF[us_id]["name"] = update.effective_message.text

        message = "Выбери из списка свой город или напиши его название одной строкой и нажми 'Отправить'"
        user_info = get_info_on(us_id)
        if user_info != None:
            message += "\n\nТекущий город: {}".format(user_info["city"])

        new_message = context.bot.send_message(
            chat_id=chid,
            text=message,
            reply_markup=generate_city_keys(get_info_on(us_id))
        )
        add_message_to_clearance(chid, new_message)
        CHAT_PHASE[chid] = 3

    elif CHAT_PHASE[chid] == 3:

        if query != None:
            delete_keyboard(query)
            clear_list_of_keyboards(chid)
            if current_call != LEAVE_NOW_CALL:
                TMP_USR_INF[us_id]["city"] = current_call
        else:
            clear_keyboards(chid)
            TMP_USR_INF[us_id]["city"] = update.effective_message.text

        message = "Напиши, о чем тебе было бы интересно поговорить, чем ты хочешь поделиться с другими " \
                  " людьми?\nЭто может быть что угодно, от киберспорта до домашнего огорода\n" \
                  "Или ты можешь стать человеком-загадкой и пропустить этот вопрос"
        user_info = get_info_on(us_id)
        if user_info != None:
            if user_info["interest"] != "":
                message += "\n\nТвои текущие интересы: {}".format(user_info["interest"])
            else:
                message += "\n\nСейчас ты - человек-загадка"

        new_message = context.bot.send_message(
            chat_id=chid,
            text=message,
            reply_markup=generate_bio_keys(get_info_on(us_id))
        )

        add_message_to_clearance(chid, new_message)
        CHAT_PHASE[chid] = 4

    elif CHAT_PHASE[chid] == 4:
        if query != None:
            delete_keyboard(query)
            clear_list_of_keyboards(chid)
            if current_call != LEAVE_NOW_CALL:
                TMP_USR_INF[us_id]["interest"] = ""
        else:
            clear_keyboards(chid)
            TMP_USR_INF[us_id]["interest"] = update.effective_message.text

        text = "Отлично! Твой профиль обновлен!"

        context.bot.send_message(
            chat_id=chid,
            text=text
        )

        TMP_USR_INF[us_id]["user_id"] = user.id
        if get_info_on(user.id) == None:
            ok = db.add_new_user(TMP_USR_INF[us_id])
        else:
            ok = db.patch_one_user(TMP_USR_INF[us_id])

        if ok:
            TMP_USR_INF.pop(us_id)
        CHAT_STATUS[chid] = STATUS["FREE"]
        CHAT_PHASE[chid] = 0



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
    if CHAT_STATUS[chid] == STATUS["PROFILE"] and CHAT_PHASE[chid] in [2, 3, 4]:
        regulate_profile(update, context)


def generate_bio_keys(user_info):
    if user_info == None:
        keyboard = [
            [InlineKeyboardButton("Пропустить", callback_data=PASS_CALL)]
        ]

    else:
        keyboard = [
            [InlineKeyboardButton("Оставить как есть", callback_data=LEAVE_NOW_CALL)],
            [InlineKeyboardButton("Пропустить", callback_data=PASS_CALL)]
        ]

    return InlineKeyboardMarkup(keyboard)


def generate_city_keys(user_info):
    if user_info == None:
        keyboard = [
            [InlineKeyboardButton("Москва", callback_data=CITY_CALLS["MOSCOW"]),
             InlineKeyboardButton("Санкт-Петербург", callback_data=CITY_CALLS["SPB"])],
             [InlineKeyboardButton("Казань", callback_data=CITY_CALLS["KAZAN"]),
             InlineKeyboardButton("Нижний Новгород", callback_data=CITY_CALLS["NIZH"])]
        ]

    else:
        keyboard = [
            [InlineKeyboardButton("Москва", callback_data=CITY_CALLS["MOSCOW"]),
             InlineKeyboardButton("Санкт-Петербург", callback_data=CITY_CALLS["SPB"])],
             [InlineKeyboardButton("Казань", callback_data=CITY_CALLS["KAZAN"]),
             InlineKeyboardButton("Нижний Новгород", callback_data=CITY_CALLS["NIZH"])],
            [InlineKeyboardButton("Оставить текущий город", callback_data=LEAVE_NOW_CALL)]
        ]

    return InlineKeyboardMarkup(keyboard)


def generate_name_keys(user_info):
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
    else:
        ml_add = EMOJIS["check"] if user_info["gender"] == "ml" else ""
        fml_add = EMOJIS["check"] if user_info["gender"] == "fml" else ""
        keyboard = [
            [InlineKeyboardButton(f"В мужском{ml_add}", callback_data=GENDER_CALLS["MALE_CALL"]),
             InlineKeyboardButton(f"В женском{fml_add}", callback_data=GENDER_CALLS["FEMALE_CALL"]),
             InlineKeyboardButton("Оставить как есть", callback_data=LEAVE_NOW_CALL)]
        ]

    return InlineKeyboardMarkup(keyboard)


def profile(update: Update, context):
    user_id = update.effective_user.id
    ch_id = update.effective_message.chat_id
    user_info = get_info_on(user_id)

    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=f"Хочешь изменить свой профиль? Хорошо, я помогу тебе с этим!"
    )
    context.bot.send_message(
        chat_id=ch_id,
        text="В каком роде я могу к тебе обращаться?",
        reply_markup=generate_gender_keys(user_info)
    )
    TMP_USR_INF[user_id] = {}
    CHAT_STATUS[ch_id] = STATUS["PROFILE"]
    CHAT_PHASE[ch_id] = 1


def start(update: Update, context):
    user = update.effective_user
    ch_id = update.effective_message.chat_id
    user_name = user.first_name
    db_result = get_info_on(user.id)  # результат

    if db_result != None:
        user_info = get_info_on(user.id)
        context.bot.send_message(
            chat_id=ch_id,
            text=f"Привет, {user_info['name']}!\n Как твои дела?"
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