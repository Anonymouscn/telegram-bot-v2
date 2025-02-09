#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import datetime
import json
import logging
import os
import time
import requests
from md2tgmd import escape
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# chat cache: username -> {chatName -> []chatContent}
chat_cache = {
    "": {"": []}
}

# context cache: username -> []chatContent
context_cache = {
    "": []
}

# cursor data cache
cursor = {
    "": {
        "": ""
    }
}

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# GENDER, PHOTO, LOCATION, BIO = range(4)

START, CHECK_HISTORY, CONTINUE_LAST, SELECT_HISTORY, NEW_CHAT, CHAT, SEND_PROMPT_TEXT = range(7)


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Starts the conversation and asks the user about their gender."""
#     reply_keyboard = [["Boy", "Girl", "Other"]]
#
#     await update.message.reply_text(
#         "Hi! My name is Professor Bot. I will hold a conversation with you. "
#         "Send /cancel to stop talking to me.\n\n"
#         "Are you a boy or a girl?",
#         reply_markup=ReplyKeyboardMarkup(
#             reply_keyboard, one_time_keyboard=True, input_field_placeholder="Boy or Girl?"
#         ),
#     )
#
#     return GENDER


# async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Stores the selected gender and asks for a photo."""
#     user = update.message.from_user
#     logger.info("Gender of %s: %s", user.first_name, update.message.text)
#     await update.message.reply_text(
#         "I see! Please send me a photo of yourself, "
#         "so I know what you look like, or send /skip if you don't want to.",
#         reply_markup=ReplyKeyboardRemove(),
#     )
#
#     return PHOTO


# async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Stores the photo and asks for a location."""
#     user = update.message.from_user
#     photo_file = await update.message.photo[-1].get_file()
#     await photo_file.download_to_drive("user_photo.jpg")
#     logger.info("Photo of %s: %s", user.first_name, "user_photo.jpg")
#     await update.message.reply_text(
#         "Gorgeous! Now, send me your location please, or send /skip if you don't want to."
#     )
#
#     return LOCATION


# async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Skips the photo and asks for a location."""
#     user = update.message.from_user
#     logger.info("User %s did not send a photo.", user.first_name)
#     await update.message.reply_text(
#         "I bet you look great! Now, send me your location please, or send /skip."
#     )
#
#     return LOCATION


# async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Stores the location and asks for some info about the user."""
#     user = update.message.from_user
#     user_location = update.message.location
#     logger.info(
#         "Location of %s: %f / %f", user.first_name, user_location.latitude, user_location.longitude
#     )
#     await update.message.reply_text(
#         "Maybe I can visit you sometime! At last, tell me something about yourself."
#     )
#
#     return BIO


# async def skip_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Skips the location and asks for info about the user."""
#     user = update.message.from_user
#     logger.info("User %s did not send a location.", user.first_name)
#     await update.message.reply_text(
#         "You seem a bit paranoid! At last, tell me something about yourself."
#     )
#
#     return BIO


# async def bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Stores the info about the user and ends the conversation."""
#     user = update.message.from_user
#     logger.info("Bio of %s: %s", user.first_name, update.message.text)
#     await update.message.reply_text("Thank you! I hope we can talk again some day.")
#
#     return ConversationHandler.END


# 取消操作
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def readme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s ask for help", user.first_name)
    await update.message.reply_text(
        "Anonymous X Bot is coming soon!\n\n"
        "/help 查看帮助\n"
        "/gpt 使用 chatgpt (已支持)\n"
        "/deepseek 使用 deepseek (正在支持)\n"
        , reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# gpt 开始切点
async def gpt_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their gender."""
    user = update.message.from_user
    options = ['new chat', '/cancel']
    if user.name in chat_cache and len(chat_cache[user.name]) > 0:
        options.append('continue')
        options.append('history')
    else:
        chat_cache[user.name] = {}
    await update.message.reply_text(
        "Hi! Welcome to use OpenAI in Anonymous X !"
        "Send /cancel to stop talking to me.\n\n",
        reply_markup=ReplyKeyboardMarkup(
            [options], resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="start chat"
        ),
    )
    return CHECK_HISTORY


# gpt 检查历史
async def check_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected = update.message.text
    user = update.message.from_user
    match selected:
        case "continue":
            await update.message.reply_text(
                "Hi! Good to see U again !"
                "Send /cancel to stop talking to me.\n\n",
                reply_markup=ReplyKeyboardMarkup(
                    [['/cancel']], resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="continue chat"
                ),
            )
            return SEND_PROMPT_TEXT
        case "history":
            chat_names = []
            for chat_name in chat_cache[user.name]:
                chat_names.append(chat_name)
            chat_names.append('/cancel')
            await update.message.reply_text(
                "Hi! Welcome to use OpenAI in Anonymous X !"
                "Send /cancel to stop talking to me.\n\n",
                reply_markup=ReplyKeyboardMarkup(
                    [chat_names], resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="select chat"
                ),
            )
            return SELECT_HISTORY
        case "new chat":
            user = update.message.from_user
            context_cache[user.name] = []
            if user.name not in chat_cache:
                chat_cache[user.name] = {
                    "": {"": []}
                }
            await update.message.reply_text(
                "Create a chat name to chat with Anonymous X !"
                "Send /cancel to stop talking to me.\n\n",
                reply_markup=ReplyKeyboardMarkup(
                    [['/cancel']], resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="chat name"
                ),
            )
            return NEW_CHAT
    return CHAT


# gpt 新建聊天
async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_name = update.message.text
    user = update.message.from_user
    if user.name not in cursor:
        cursor[user.name] = {
            "": ""
        }
    cursor[user.name]['chat_name'] = chat_name
    chat_cache[user.name][chat_name] = []
    reply_keyboard = [['gpt-4o', 'gpt-4o-mini', 'o1-preview', 'o1-mini']]
    await update.message.reply_text(
        "Select a model to chat in Anonymous X !"
        "Send /cancel to stop talking to me.\n\n",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="select model"
        ),
    )
    return CHAT


def time_to_str(t) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', t)


def time_str_to_int(s):
    datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


def str_to_time(s):
    return datetime.datetime.strftime(s, '%Y-%m-%d %H:%M:%S')


async def select_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    session = update.message.text
    user = update.message.from_user
    cursor[user.name]['name'] = session
    context_cache[user.name] = chat_cache[user.name][session]
    await update.message.reply_text(
        "Hi, you have came back to " + session + " session. Continue to have fun !",
        reply_markup=ReplyKeyboardMarkup(
            [['/cancel']], resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="chat"
        ),
    )
    return SEND_PROMPT_TEXT


async def create_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    cache = context_cache[user.name]
    if len(cache) == 0:
        if user.name not in cursor:
            cursor[user.name] = {
                "": ""
            }
        cursor[user.name]['model'] = update.message.text
    await update.message.reply_text(
        "Hello, I'm " + cursor[user.name]['model'] + ", "
                                                     "you can ask me a question or chat to me, or send /cancel if you don't want to.",
        reply_markup=ReplyKeyboardMarkup(
            [['/cancel']], resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="select model"
        ),
    )
    return SEND_PROMPT_TEXT


async def send_prompt_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    prompt = update.message.text
    model = cursor[user.name]['model']
    messages: list = context_cache[user.name]
    messages.append({
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": prompt,
            }
        ]
    })
    payload = {
        "model_factory": "openai",
        "prompt_type": "multiple",
        "model_payload": {
            "model": model,
            "messages": messages,
        }
    }
    result = requests.post(url="http://192.168.2.70:8080/service/model/chat", data=json.dumps(payload)).json()
    response = result['data']['choices'][0]['message']['content']
    messages.append({
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": response,
            }
        ]
    })
    context_cache[user.name] = messages
    chat_cache[user.name][cursor[user.name]['chat_name']] = messages
    response_data = escape(response)
    max_len = 4096
    if len(response_data) > max_len:
        for x in range(0, len(response_data), max_len):
            await update.message.reply_text(
                response_data[x:x + max_len],
                reply_markup=ReplyKeyboardMarkup(
                    [['/cancel']], resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="chat"
                ),
            )
    else:
        await update.message.reply_text(
            escape(response),
            parse_mode="MarkdownV2",
            reply_markup=ReplyKeyboardMarkup(
                [['/cancel']], resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="chat"
            ),
        )
    return SEND_PROMPT_TEXT


# invoke_model 调用模型
def invoke_model(factory: str, model: str, messages) -> str:
    payload = {
        "model_factory": factory,
        "prompt_type": "multiple",
        "model_payload": {
            "model": model,
            "messages": messages
        }
    }
    result = requests.post(url="http://192.168.2.70:8080/service/model/chat", data=json.dumps(payload)).json()
    response = result['data']['choices'][0]['message']['content']
    return escape(response)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your token.
    # 7654069819:AAFXrxCc2ym-JdLm_1zgBconCEQ1bgQKnCo
    token = os.environ.get('BOT_TOKEN')
    if token is None or token == "":
        print('BOT_TOKEN not found !')
        exit(1)
    application = Application.builder().token(token).build()

    # help handler
    help_handler = ConversationHandler(
        entry_points=[CommandHandler("help", readme)],
        states={},
        fallbacks=[],
    )

    # gpt handler
    gpt_handler = ConversationHandler(
        entry_points=[CommandHandler("gpt", gpt_start)],  # 开始
        states={
            CHECK_HISTORY: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, check_history)],  # 检查聊天历史
            CONTINUE_LAST: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, create_prompt)],  # 继续上一次聊天
            SELECT_HISTORY: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, select_history)],  # 选择历史聊天
            NEW_CHAT: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, new_chat)],  # 新建聊天
            CHAT: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, create_prompt)],  # 开始聊天
            SEND_PROMPT_TEXT: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, send_prompt_text)]  # 发送普通文本 prompt
        },
        fallbacks=[],
    )

    # deepseek handler
    deepseek_handler = ConversationHandler(
        entry_points=[CommandHandler("deepseek", readme)],
        states={
        },
        fallbacks=[],
    )

    application.add_handler(help_handler)
    application.add_handler(gpt_handler)
    application.add_handler(deepseek_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
