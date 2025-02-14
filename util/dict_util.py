
def clean_dict(obj):
    """去除 None 值，确保数据库使用默认值"""
    return {k: v for k, v in obj.__dict__.items() if v is not None and not k.startswith('_')}


def to_dict(obj: any):
    if isinstance(obj, dict):  # 如果已经是字典，直接返回
        return obj
    elif isinstance(obj, list):  # 如果是列表，递归处理每个元素
        return [to_dict(i) for i in obj]
    elif hasattr(obj, "__dict__"):  # 如果是自定义对象
        return {k: to_dict(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    else:  # 其他基本类型（str, int, float, bool, None）
        return obj


def get_on_not_null(target: dict, key: any, default: any):
    if key in target:
        return target[key]
    return default


def save_in_dict_chain(target: dict, value: any, paths: list):
    if target is None or value is None or paths is None:
        return
    # 使用一个临时变量来跟踪当前的嵌套层级
    current = target
    # 遍历路径，逐级创建字典
    for i, path in enumerate(paths):
        if i == len(paths) - 1:
            # 如果是最后一个路径，直接赋值
            current[path] = value
        else:
            # 如果不是最后一个路径，确保当前路径存在并进入下一层
            if path not in current:
                current[path] = {}
            current = current[path]
