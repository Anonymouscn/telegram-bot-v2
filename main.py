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
import json
import logging
import os
import re
from typing import Callable, Awaitable

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

from model.db.t_answer import TAnswer
from model.db.t_question import TQuestion
from model.db.t_session import TSession
from model.db.t_user import TUser
from module.chat.chatgpt.service.chatgpt_service import batch_get_chat_content_in_session_collection
from module.repo.chat.answer_repo import batch_save_answer
from module.repo.chat.question_repo import save_question, get_latest_question
from module.repo.chat.session_repo import batch_get_session_in_user_collection, batch_save_session, \
    get_session_id_by_name, count_user_sessions, get_session_by_name, get_last_session, is_exist_session
from module.repo.user.user_repo import batch_save_or_update
from provider.db import InitDB
from util.dict_util import save_in_dict_chain
from util.lang_util import init_lang, get_with_lang
from util.value_util import set_or_default

# cursor data cache
cursor = {}

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

START, CHECK_HISTORY, CONTINUE_LAST, SELECT_HISTORY, NEW_CHAT, SET_CHAT_NAME, CREATE_PROMPT, SEND_PROMPT_TEXT = range(8)


# 取消操作
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info(
        "User [id:%s, name:%s] canceled the conversation.",
        user.id, user.full_name,
    )
    await update.message.reply_text(
        get_with_lang('cancel_reply', user.language_code),
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# readme 说明/获取帮助
async def readme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get help for """
    user = update.message.from_user
    logger.info(
        "User [id:%s, name:%s] ask for help.",
        user.id, user.full_name,
    )
    await update.message.reply_text(
        get_with_lang('help_reply', user.language_code),
        reply_markup=ReplyKeyboardMarkup(
            [['/gpt', '/deepseek']],
            resize_keyboard=True,
            is_persistent=False,
            one_time_keyboard=True,
            input_field_placeholder=get_with_lang('help_placeholder', user.language_code),
        ),
    )
    return ConversationHandler.END


# gpt 开始切点
async def chatgpt_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await chat_start(update, context, 'ChatGPT')


# deepseek 开始切点
async def deepseek_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await chat_start(update, context, 'DeepSeek')


# 开始切点
async def chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE, factory: str) -> int:
    user = update.message.from_user
    logger.info(
        "User [id:%s, name:%s] start to chat.",
        user.id, user.full_name,
    )
    # 查询 & 更新用户信息
    current_user = TUser(
        id=user.id,
        first_name=set_or_default(user.first_name, ''),
        last_name=set_or_default(user.last_name, ''),
        full_name=set_or_default(user.full_name, ''),
        is_bot=0,
        language_code=set_or_default(user.language_code, ''),
    )
    if user.is_bot:
        current_user.is_bot = 1
    batch_save_or_update([current_user])
    # 预制选项
    options = ['/new_chat', '/cancel']
    # 获取总会话数
    total_sessions = count_user_sessions(user.id, factory)
    save_in_dict_chain(cursor, total_sessions, [user.id, factory, 'total_sessions'])
    if total_sessions > 0:
        options.append('/history')  # 选择上次聊天历史
    last_session = get_last_session(user.id, factory)
    if last_session is not None:
        options.append('/continue')
        save_in_dict_chain(cursor, last_session.id, [user.id, factory, 'last_session', 'id'])
        save_in_dict_chain(cursor, last_session.name, [user.id, factory, 'last_session', 'chat_name'])
        save_in_dict_chain(cursor, last_session.factory, [user.id, factory, 'last_session', 'factory'])
        save_in_dict_chain(cursor, last_session.model, [user.id, factory, 'last_session', 'model'])
    tips = (get_with_lang("chat_start_reply", user.language_code).replace("$factory", factory))
    for option in options:
        tips = tips + (option + "\n")
    await update.message.reply_text(
        tips,
        reply_markup=ReplyKeyboardMarkup(
            [options],
            resize_keyboard=True,
            is_persistent=True,
            one_time_keyboard=True,
            input_field_placeholder=get_with_lang('chat_start_placeholder', user.language_code),
        ),
    )
    return CHECK_HISTORY


async def chatgpt_check_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await check_history(update, context, 'ChatGPT')


async def deepseek_check_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await check_history(update, context, 'DeepSeek')


# gpt 检查历史
async def check_history(update: Update, context: ContextTypes.DEFAULT_TYPE, factory: str) -> int:
    selected = update.message.text
    user = update.message.from_user
    match selected:
        case "/continue":
            # 获取最新的会话
            session_id = cursor[user.id][factory]['last_session']['id']
            save_in_dict_chain(cursor, cursor[user.id][factory]['last_session']['model'], [user.id, factory, 'model'])
            save_in_dict_chain(cursor, session_id, [user.id, factory, 'session_id'])
            latest_question = get_latest_question(session_id)
            if latest_question is not None:
                save_in_dict_chain(cursor, latest_question.id, [user.id, factory, 'parent_id'])
            await update.message.reply_text(
                get_with_lang("continue_reply", user.language_code),
                reply_markup=ReplyKeyboardMarkup(
                    [['/cancel']],
                    resize_keyboard=True,
                    is_persistent=True,
                    one_time_keyboard=True,
                    input_field_placeholder=get_with_lang('continue_placeholder', user.language_code),
                ),
            )
            return SEND_PROMPT_TEXT
        case "/history":
            chat_names = []
            # 获取全部会话名
            sessions = batch_get_session_in_user_collection(
                user_id_list=[user.id], factory=factory, limit=4
            )
            for s in sessions:
                chat_names.append("/" + s.name)
            chat_names.append('/cancel')
            if cursor[user.id][factory]['total_sessions'] > 4:
                chat_names.append("/more")
            tips = get_with_lang('history_reply', user.language_code)
            for chat_name in chat_names:
                tips += (chat_name + "\n")
            await update.message.reply_text(
                tips,
                reply_markup=ReplyKeyboardMarkup(
                    [chat_names],
                    resize_keyboard=True,
                    is_persistent=True,
                    one_time_keyboard=True,
                    input_field_placeholder=get_with_lang('history_placeholder', user.language_code)
                ),
            )
            return SELECT_HISTORY
        case "/new_chat":
            await update.message.reply_text(
                get_with_lang('new_chat_reply', user.language_code),
                reply_markup=ReplyKeyboardMarkup(
                    [['/cancel']],
                    resize_keyboard=True,
                    is_persistent=True,
                    one_time_keyboard=True,
                    input_field_placeholder=get_with_lang('new_chat_placeholder', user.language_code)
                ),
            )
            return SET_CHAT_NAME
    return CREATE_PROMPT


async def chatgpt_set_chat_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await set_chat_name(update, context, 'ChatGPT', chatgpt_new_chat)


async def deepseek_set_chat_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await set_chat_name(update, context, 'DeepSeek', deepseek_new_chat)


# 设置聊天名
async def set_chat_name(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        factory: str,
        next_step: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[int]]
) -> int:
    user = update.message.from_user
    chat_name = update.message.text
    pattern = r'^[a-zA-Z0-9_]+$'
    # 格式检查
    length = len(chat_name)
    if len(chat_name) == 0:
        await update.message.reply_text(
            get_with_lang('chat_name_empty_reply', user.language_code),
            reply_markup=ReplyKeyboardMarkup(
                [['/cancel']],
                resize_keyboard=True,
                is_persistent=True,
                one_time_keyboard=True,
                input_field_placeholder=get_with_lang('new_chat_placeholder', user.language_code)
            ),
        )
        return SET_CHAT_NAME
    if length >= 50:
        await update.message.reply_text(
            get_with_lang('chat_name_too_long_reply', user.language_code),
            reply_markup=ReplyKeyboardMarkup(
                [['/cancel']],
                resize_keyboard=True,
                is_persistent=True,
                one_time_keyboard=True,
                input_field_placeholder=get_with_lang('new_chat_placeholder', user.language_code)
            ),
        )
        return SET_CHAT_NAME
    if not re.match(pattern, chat_name):
        await update.message.reply_text(
            get_with_lang('chat_name_invalid_reply', user.language_code),
            reply_markup=ReplyKeyboardMarkup(
                [['/cancel']],
                resize_keyboard=True,
                is_persistent=True,
                one_time_keyboard=True,
                input_field_placeholder=get_with_lang('new_chat_placeholder', user.language_code)
            ),
        )
        return SET_CHAT_NAME
    # 重复名称检查
    if is_exist_session(user.id, factory, chat_name):
        await update.message.reply_text(
            get_with_lang('chat_name_duplicate_reply', user.language_code),
            reply_markup=ReplyKeyboardMarkup(
                [['/cancel']],
                resize_keyboard=True,
                is_persistent=True,
                one_time_keyboard=True,
                input_field_placeholder=get_with_lang('new_chat_placeholder', user.language_code)
            ),
        )
        return SET_CHAT_NAME
    await update.message.reply_text(
        "OK.",
    )
    return await next_step(update, context)


async def chatgpt_new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await new_chat(update, context, ['/gpt_4o', '/gpt_4o_mini', '/o1_preview', '/o1_mini'], 'ChatGPT')


async def deepseek_new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await new_chat(update, context, ['/deepseek_chat', '/deep_research'], 'DeepSeek')


# gpt 新建聊天
async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, models: list, factory: str) -> int:
    chat_name = update.message.text
    user = update.message.from_user
    save_in_dict_chain(cursor, chat_name, [user.id, factory, 'chat_name'])
    save_in_dict_chain(cursor, None, [user.id, factory, 'parent_id'])
    reply_keyboard = [models]
    tips = get_with_lang('new_chat_select_model_reply', user.language_code)
    for model in reply_keyboard[0]:
        tips += (model + "\n")
    await update.message.reply_text(
        tips,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
            is_persistent=True,
            one_time_keyboard=True,
            input_field_placeholder=get_with_lang('new_chat_select_model_placeholder', user.language_code)
        ),
    )
    return CREATE_PROMPT


async def chatgpt_select_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await select_history(update, context, 'ChatGPT')


async def deepseek_select_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await select_history(update, context, 'DeepSeek')


async def select_history(update: Update, context: ContextTypes.DEFAULT_TYPE, factory: str) -> int:
    session = update.message.text.replace("/", "")
    user = update.message.from_user
    save_in_dict_chain(cursor, session, [user.id, factory, 'chat_name'])
    selected = get_session_by_name(user.id, session, factory)
    save_in_dict_chain(cursor, selected.model, [user.id, factory, 'model'])
    save_in_dict_chain(cursor, selected.id, [user.id, factory, 'session_id'])
    latest_question = get_latest_question(selected.id)
    save_in_dict_chain(cursor, latest_question.id, [user.id, factory, 'parent_id'])
    await update.message.reply_text(
        get_with_lang('select_history_reply', user.language_code).replace("$session", session),
        reply_markup=ReplyKeyboardMarkup(
            [['/cancel']],
            resize_keyboard=True,
            is_persistent=True,
            one_time_keyboard=True,
            input_field_placeholder=get_with_lang('chat_placeholder', user.language_code)
        ),
    )
    return SEND_PROMPT_TEXT


async def chatgpt_create_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await create_prompt(update, context, 'ChatGPT')


async def deepseek_create_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await create_prompt(update, context, 'DeepSeek')


async def create_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, factory: str) -> int:
    user = update.message.from_user
    # 保存当前使用模型名称
    save_in_dict_chain(
        cursor,
        update.message.text.replace("/", "").replace("_", "-"),
        [user.id, factory, 'model']
    )
    chat_name = cursor[user.id][factory]['chat_name']
    model = cursor[user.id][factory]['model']

    # 新建会话
    batch_save_session([
        TSession(
            user_id=user.id,
            name=chat_name,
            factory=factory,
            model=model,
        )
    ])
    # 保存会话 id
    save_in_dict_chain(
        cursor,
        get_session_id_by_name(user.id, chat_name, factory)[0],
        [user.id, factory, 'session_id']
    )
    await update.message.reply_text(
        get_with_lang('create_prompt_reply', user.language_code).replace("$model", model),
        reply_markup=ReplyKeyboardMarkup(
            [['/cancel']],
            resize_keyboard=True,
            is_persistent=True,
            one_time_keyboard=True,
            input_field_placeholder=get_with_lang('create_prompt_placeholder', user.language_code)
        ),
    )
    return SEND_PROMPT_TEXT


async def chatgpt_send_prompt_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    def create_payload(messages: list, prompt: str, model: str) -> dict:
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
        return payload

    return await send_prompt_text(update, context, 'ChatGPT', 'multiple', create_payload)


async def deepseek_send_prompt_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    def create_payload(messages: list, prompt: str, model: str) -> dict:
        messages.append({
            "role": "user",
            "content": prompt
        })
        payload = {
            "model_factory": "deepseek",
            "model_payload": {
                "model": model,
                "messages": messages,
            }
        }
        return payload

    return await send_prompt_text(update, context, 'DeepSeek', 'default', create_payload)


async def send_prompt_text(update: Update, context: ContextTypes.DEFAULT_TYPE, factory: str, msg_type: str,
                           fn: Callable[[list, str, str], dict]) -> int:
    user = update.message.from_user
    prompt = update.message.text
    model = cursor[user.id][factory]['model']
    # 获取消息
    session_id = int(cursor[user.id][factory]['session_id'])
    message_chain: list = batch_get_chat_content_in_session_collection([session_id], content_type=msg_type)
    messages: list = []
    if len(message_chain) == 1:
        messages = message_chain[0]
    parent_id = 0
    if 'parent_id' in cursor[user.id][factory]:
        parent_id = cursor[user.id][factory]['parent_id']
    session_id = int(cursor[user.id][factory]['session_id'])
    current_question = TQuestion(
        session_id=session_id,
        parent_id=parent_id,
        type=0,
        content=prompt,
    )
    latest_question = save_question(current_question)
    if latest_question is not None:
        save_in_dict_chain(cursor, latest_question.id, [user.id, factory, 'parent_id'])
    payload = fn(messages, prompt, model)
    result = requests.post(
        url="http://192.168.2.70:8080/service/model/chat",
        data=json.dumps(payload)
    ).json()
    response = get_with_lang('server_error_reply', user.language_code)
    if result['data']['choices'] is not None and len(result['data']['choices']) > 0:
        response = result['data']['choices'][0]['message']['content']
    current_answer = TAnswer(
        session_id=session_id,
        question_id=latest_question.id,
        type=0,
        content=response,
    )
    batch_save_answer([current_answer])
    response_data = escape(response)
    max_len = 4096
    if len(response_data) > max_len:
        for x in range(0, len(response_data), max_len):
            await update.message.reply_text(
                response_data[x:x + max_len],
                reply_markup=ReplyKeyboardMarkup(
                    [['/cancel']],
                    resize_keyboard=True,
                    is_persistent=True,
                    one_time_keyboard=True,
                    input_field_placeholder=get_with_lang('chat_placeholder', user.language_code)
                ),
            )
    else:
        await update.message.reply_text(
            escape(response),
            parse_mode="MarkdownV2",
            reply_markup=ReplyKeyboardMarkup(
                [['/cancel']],
                resize_keyboard=True,
                is_persistent=True,
                one_time_keyboard=True,
                input_field_placeholder=get_with_lang('chat_placeholder', user.language_code)
            ),
        )
    return SEND_PROMPT_TEXT


# main entrypoint
def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your token.
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
        entry_points=[CommandHandler("gpt", chatgpt_start)],  # 开始
        states={
            CHECK_HISTORY: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, chatgpt_check_history)],
            # 检查聊天历史
            CONTINUE_LAST: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, chatgpt_create_prompt)],
            # 继续上一次聊天
            SELECT_HISTORY: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, chatgpt_select_history)],
            # 选择历史聊天
            SET_CHAT_NAME: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, chatgpt_set_chat_name)],
            NEW_CHAT: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, chatgpt_new_chat)],  # 新建聊天
            CREATE_PROMPT: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, chatgpt_create_prompt)],
            SEND_PROMPT_TEXT: [CommandHandler("cancel", cancel),
                               MessageHandler(filters.TEXT, chatgpt_send_prompt_text)],
        },
        fallbacks=[],
    )
    # deepseek handler
    deepseek_handler = ConversationHandler(
        entry_points=[CommandHandler("deepseek", deepseek_start)],
        states={
            CHECK_HISTORY: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, deepseek_check_history)],
            CONTINUE_LAST: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, deepseek_create_prompt)],
            SELECT_HISTORY: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, deepseek_select_history)],
            SET_CHAT_NAME: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, deepseek_set_chat_name)],
            NEW_CHAT: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, deepseek_set_chat_name)],
            CREATE_PROMPT: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT, deepseek_create_prompt)],
            SEND_PROMPT_TEXT: [CommandHandler("cancel", cancel),
                               MessageHandler(filters.TEXT, deepseek_send_prompt_text)],
        },
        fallbacks=[],
    )

    application.add_handler(help_handler)
    application.add_handler(gpt_handler)
    application.add_handler(deepseek_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    init_lang()
    InitDB()
    main()


