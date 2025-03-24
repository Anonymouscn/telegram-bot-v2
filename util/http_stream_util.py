import asyncio
import json
from telegram import Update
from telegram.ext import ContextTypes
import httpx
from multiprocessing import Value
from util.lang_util import get_with_lang


# 事件流处理
async def stream_events(target: str, body: any, on_receive, on_error, update: Update,
                        context: ContextTypes.DEFAULT_TYPE, state,
                        lock: asyncio.Lock = asyncio.Lock(), save_lock: Value = Value('i', 0)):
    retries = 3
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(
                    timeout=httpx.Timeout(timeout=300),
                    headers={
                        "Connection": "keep-alive",
                        "Cache-control": "no-cache",
                    },
            ) as client:
                async with client.stream("POST", target, json=body) as response:
                    if on_receive is None:
                        return
                    # 检查响应状态码
                    response.raise_for_status()
                    # 循环读取数据流
                    async for line in response.aiter_lines():
                        # 过滤掉心跳行（通常会发送空行作为心跳）
                        if line:
                            # 根据不同 api 风格进行处理 (openai / claude)
                            style = 'default'
                            if state['factory'] == 'Claude':
                                style = 'claude'
                            if style == 'default':
                                await decode_openai_event_stream(line, on_receive, on_error, update, context, state, lock, save_lock)
                            else:
                                if style == 'claude':
                                    await decode_claude_event_stream(line, on_receive, on_error, update, context, state, lock, save_lock)
                    break
        except Exception as e:
            print(f"Request failed: {e}")
            # 重试后仍然请求失败，执行错误处理
            if attempt >= retries - 1:
                user = update.message.from_user
                error = {
                    "message": get_with_lang('server_busy_or_error_reply', user.language_code),
                }
                await on_error(update, context, state, error, save_lock)
                raise
            state['content'] = ''
            state['finish'] = False


async def decode_openai_event_stream(line, on_receive, on_error, update, context, state, lock, save_lock):
    decoded_line = line
    decoded_line = decoded_line.replace('data: ', '')
    try:
        chunk = json.loads(decoded_line)
        finished = None
        # 错误处理
        error = chunk.get('error', None)
        if error is not None:
            if on_error is not None:
                await on_error(update, context, state, error, save_lock)
            return
        for choice in chunk.get('choices', []):
            reasoning_content: str = choice. \
                get('delta', {}). \
                get('reasoning_content', None)
            content: str = choice. \
                get('delta', {}). \
                get('content', '')
            finished = choice.get('finish_reason', None)
            # 深度思考兼容
            if reasoning_content is not None and len(reasoning_content) > 0:
                reasoning_content = reasoning_content. \
                    replace('\"', '"'). \
                    replace('\t', '  '). \
                    replace('\n', '\n> ')
                if len(state['content']) == 0:
                    user = update.message.from_user
                    reasoning_content = \
                        get_with_lang('deepthink_prefix', user.language_code) + \
                        reasoning_content
                state['content'] += reasoning_content
                await on_receive(update, context, state, lock, save_lock)
            # 普通模型 content 传参
            else:
                if content is not None and len(content) > 0:
                    content = content. \
                        replace('\"', '"'). \
                        replace('\t', '  ')
                    state['content'] += content
                    await on_receive(update, context, state, lock, save_lock)
        if finished is not None:
            state['finish'] = True
            asyncio.create_task(on_receive(update, context, state, lock, save_lock))
    except json.JSONDecodeError:
        if "[DONE]" in str(decoded_line):
            state['finish'] = True
            await asyncio.create_task(on_receive(update, context, state, lock, save_lock))
        else:
            print(f'no a regular json content, ignore: {decoded_line}')


async def decode_claude_event_stream(line, on_receive, on_error, update, context, state, lock, save_lock):
    # 解码并打印事件数据
    decoded_line = line
    if 'data: ' not in decoded_line:
        print(f'no data chunk found, ignore: {decoded_line}')
        return
    decoded_line = decoded_line.replace('data: ', '')
    try:
        chunk = json.loads(decoded_line)
        # 错误处理
        error = chunk.get('error', None)
        if error is not None:
            if on_error is not None:
                await on_error(update, context, state, error, save_lock)
            return
        msgType: str = chunk.get('type', '')
        if msgType != 'content_block_delta':
            print(f'not a content delta, ignore: {chunk}')
            if msgType == 'message_stop':
                state['finish'] = True
                asyncio.create_task(on_receive(update, context, state, lock, save_lock))
            return
        content = chunk.get('delta', {}).get('text', {})
        if len(content) > 0:
            state['content'] += content
            await on_receive(update, context, state, lock, save_lock)
    except json.JSONDecodeError:
        if "\"message_stop\"" in str(decoded_line):
            state['finish'] = True
            await asyncio.create_task(on_receive(update, context, state, lock, save_lock))
        else:
            print(f'no a regular json content, ignore: {decoded_line}')
