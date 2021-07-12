import config, db
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackQueryHandler

CALLBACK_GOOD = "good"
CALLBACK_BAD = "bad"

GOOD_STICKER = "CAACAgIAAxkBAAJX_16nCRx3_yNcHjGJJ8UkEk62o0MTAAIXAAN_gBAunKNhxU-S6OIZBA"
BAD_STICKER = "CAACAgIAAxkBAAJYAV6nCSUZKTelneyyMG6wcXKM5u4VAAImAAN_gBAuCDLXyOyP3gYZBA"



def generate_keyboard():
    keyboard = [
        [InlineKeyboardButton("Хорошо", callback_data=CALLBACK_GOOD),
         InlineKeyboardButton("Плохо", callback_data=CALLBACK_BAD)]
    ]

    return InlineKeyboardMarkup(keyboard)


def keyboard_regulate(update: Update, context):
    query = update.callback_query
    current_callback = query.data

    chat_id1 = update.effective_message.chat_id

    query.edit_message_text(
        text=update.effective_message.text
    )

    if current_callback == CALLBACK_GOOD:
        context.bot.send_sticker(
            chat_id=chat_id1,
            sticker=GOOD_STICKER
        )

    elif current_callback == CALLBACK_BAD:
        context.bot.send_sticker(
            chat_id=chat_id1,
            sticker=BAD_STICKER
        )


def hello(update: Update, context):
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=update.effective_message.text
    )


def check_db(user_id):
    file = db.names
    return user_id in file


def profile(update: Update, context):
    user_id = update.effective_user.id
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=f"Привет, {str(user_id)}!\nКак твои дела?"
    )


def start(update: Update, context):
    is_new_user = check_db(update.effective_user.id)
    ch_id = update.effective_message.chat_id
    user_name = update.effective_user.user_name

    context.bot.send_message(
        chat_id=ch_id,
        text=f"{str(is_new_user)}"
    )
    """"
    if is_new_user:
        context.bot.send_message(
            chat_id=ch_id,
            text=f"Привет, {str(user_name)}!\nТы, похоже, новенький! Как твои дела?"
        )

    else:
        context.bot.send_message(
            chat_id=ch_id,
            text=f"Привет, {str(user_name)}!\n Как твои дела?"
        )
"""

def main():
    my_update = Updater(
        token=config.TOKEN,
        #base_url=config.PROXI,
        use_context=True
    )


    keyboard_handler = CallbackQueryHandler(callback=keyboard_regulate, pass_chat_data=True)
    my_handler = MessageHandler(Filters.all, hello)
    start_handler = CommandHandler("start", start)
    profile_handler = CommandHandler("profile", profile)

    my_update.dispatcher.add_handler(keyboard_handler)
    my_update.dispatcher.add_handler(start_handler)
    my_update.dispatcher.add_handler(profile_handler)
    my_update.dispatcher.add_handler(my_handler)

    my_update.start_polling()
    my_update.idle()


if __name__ == "__main__":
    main()