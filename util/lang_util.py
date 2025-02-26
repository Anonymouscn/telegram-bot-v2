import json
from util.dict_util import save_in_dict_chain

# 语言缓存
content = {}


# 初始化语言
def init_lang():
    with open('lang/zh.json', 'r') as file:
        data = json.load(file)
        save_in_dict_chain(content, data, ['zh'])
    with open('lang/en.json', 'r') as file:
        data = json.load(file)
        save_in_dict_chain(content, data, ['en'])


# 使用客制化版本语言
def get_with_lang(key: str, lang: str) -> str:
    used_lang = 'en'
    if lang is not None and 'zh' in lang:
        used_lang = 'zh'
    return content[used_lang][key]
