import numpy as np


# 重排选项卡
def reshape_options(selectable_models):
    selectable_models = list(selectable_models)
    length = len(selectable_models)  # 计算长度
    if length % 2 == 1:
        reshaped_part = np.array(selectable_models[:-1], dtype=object).reshape(-1, 2)  # 只 reshape 偶数部分
        last_element = np.array([selectable_models[-1]], dtype=object)  # 让最后一个元素成为二维数组
        return np.vstack([reshaped_part, last_element])  # 合并
    else:
        return np.array(selectable_models, dtype=object).reshape(-1, 2)  # 直接 reshape
