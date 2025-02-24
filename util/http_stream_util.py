import asyncio
import json
from telegram import Update
from telegram.ext import ContextTypes
import httpx
from multiprocessing import Value


async def stream_events(target: str, body: any, on_receive, update: Update,
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
                    try:
                        # 循环读取数据流
                        async for line in response.aiter_lines():
                            # 过滤掉心跳行（通常会发送空行作为心跳）
                            if line:
                                # 解码并打印事件数据
                                decoded_line = line
                                decoded_line = decoded_line.replace('data: ', '')
                                try:
                                    chunk = json.loads(decoded_line)
                                    print(chunk)
                                    finished = None
                                    for choice in chunk.get('choices', []):
                                        content = choice.get('delta', {}).get('content', '')
                                        finished = choice.get('finish_reason', None)
                                        if content is not None and content != '':
                                            state['content'] += content
                                            await on_receive(update, context, state, lock, save_lock)
                                    if finished is not None:
                                        state['finish'] = True
                                        asyncio.create_task(on_receive(update, context, state, lock, save_lock))
                                except json.JSONDecodeError:
                                    print(str(decoded_line))
                                    if "[DONE]" in str(decoded_line):
                                        state['finish'] = True
                                        await asyncio.create_task(on_receive(update, context, state, lock, save_lock))
                                    else:
                                        print(f'no a regular json content, ignore: {decoded_line}')
                    except KeyboardInterrupt:
                        print("Stream closed by user.")
                    break
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            print(f"Request failed: {e}")
            if attempt == retries - 1:
                raise  # Re-raise the last exception after all retries
            print("Retrying...")
            state['content'] = ''
            state['finish'] = False
