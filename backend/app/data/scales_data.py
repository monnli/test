"""预置 5 套心理量表的完整题库。

出处：PHQ-9、GAD-7 为公开国际量表；SCARED、CES-DC 使用公开中文版；
MHT 使用华东师大版简版维度（完整版 100 题由于版权原因，这里给出演示用精简版）。
"""

from __future__ import annotations

# 四点频率选项（PHQ-9、GAD-7 通用）
_FREQ4 = [
    {"label": "完全没有", "score": 0},
    {"label": "有几天", "score": 1},
    {"label": "一半以上的天数", "score": 2},
    {"label": "几乎每天", "score": 3},
]

# SCARED 三点选项
_SCARED3 = [
    {"label": "不像我", "score": 0},
    {"label": "有点像我", "score": 1},
    {"label": "完全像我", "score": 2},
]

# CES-DC 四点选项（反向已处理）
_CESDC4 = [
    {"label": "几乎没有（<1 天/周）", "score": 0},
    {"label": "偶尔（1-2 天）", "score": 1},
    {"label": "经常（3-4 天）", "score": 2},
    {"label": "大部分时间（5-7 天）", "score": 3},
]

_YESNO = [
    {"label": "是", "score": 1},
    {"label": "否", "score": 0},
]


SCALES = [
    {
        "code": "PHQ-9",
        "name": "PHQ-9 抑郁症筛查量表",
        "target": "抑郁筛查",
        "description": "在过去的两周里，你有多经常被以下问题困扰？",
        "interpretation": [
            {"min": 0, "max": 4, "level": "无明显抑郁", "color": "green", "advice": "心理状态良好，继续保持"},
            {"min": 5, "max": 9, "level": "轻度抑郁", "color": "blue", "advice": "注意自我调节，必要时寻求支持"},
            {"min": 10, "max": 14, "level": "中度抑郁", "color": "orange", "advice": "建议与心理老师沟通"},
            {"min": 15, "max": 19, "level": "中重度抑郁", "color": "red", "advice": "需要专业心理干预"},
            {"min": 20, "max": 27, "level": "重度抑郁", "color": "purple", "advice": "尽快寻求精神科医生评估"},
        ],
        "questions": [
            {"content": "做事时提不起劲或没有兴趣", "options": _FREQ4},
            {"content": "感到心情低落、沮丧或绝望", "options": _FREQ4},
            {"content": "入睡困难、睡不安稳或睡眠过多", "options": _FREQ4},
            {"content": "感觉疲倦或没有活力", "options": _FREQ4},
            {"content": "食欲不振或吃太多", "options": _FREQ4},
            {"content": "觉得自己很糟、让自己或家人失望", "options": _FREQ4},
            {"content": "对事物专注有困难，例如看报纸或电视时", "options": _FREQ4},
            {"content": "动作或说话速度缓慢到别人察觉，或相反地烦躁难以静坐", "options": _FREQ4},
            {"content": "有不如死掉或用某种方式伤害自己的念头", "options": _FREQ4},
        ],
    },
    {
        "code": "GAD-7",
        "name": "GAD-7 广泛性焦虑量表",
        "target": "焦虑筛查",
        "description": "在过去的两周里，你有多经常被以下问题困扰？",
        "interpretation": [
            {"min": 0, "max": 4, "level": "无明显焦虑", "color": "green", "advice": "焦虑水平正常"},
            {"min": 5, "max": 9, "level": "轻度焦虑", "color": "blue", "advice": "可尝试放松训练"},
            {"min": 10, "max": 14, "level": "中度焦虑", "color": "orange", "advice": "建议心理辅导"},
            {"min": 15, "max": 21, "level": "重度焦虑", "color": "red", "advice": "建议寻求专业帮助"},
        ],
        "questions": [
            {"content": "感觉紧张，焦虑或急切", "options": _FREQ4},
            {"content": "不能够停止或控制担忧", "options": _FREQ4},
            {"content": "对各种各样的事情担忧过多", "options": _FREQ4},
            {"content": "很难放松下来", "options": _FREQ4},
            {"content": "由于不安而难以静坐", "options": _FREQ4},
            {"content": "变得容易烦恼或急躁", "options": _FREQ4},
            {"content": "感到似乎将有可怕的事情发生而害怕", "options": _FREQ4},
        ],
    },
    {
        "code": "SCARED",
        "name": "SCARED 儿童焦虑相关情绪障碍筛查",
        "target": "儿童青少年焦虑",
        "description": "以下描述与你近 3 个月的感觉是否符合？",
        "interpretation": [
            {"min": 0, "max": 24, "level": "焦虑水平低", "color": "green", "advice": "情绪状态良好"},
            {"min": 25, "max": 40, "level": "可能存在焦虑障碍", "color": "orange", "advice": "建议家长与老师关注"},
            {"min": 41, "max": 82, "level": "明显焦虑倾向", "color": "red", "advice": "建议心理评估"},
        ],
        "questions": [
            {"content": "感到害怕时心跳加快", "options": _SCARED3, "dimension": "恐慌"},
            {"content": "在学校感到紧张", "options": _SCARED3, "dimension": "分离焦虑"},
            {"content": "害怕离开家", "options": _SCARED3, "dimension": "分离焦虑"},
            {"content": "担心自己生病", "options": _SCARED3, "dimension": "躯体担忧"},
            {"content": "在陌生人面前感到害羞", "options": _SCARED3, "dimension": "社交焦虑"},
            {"content": "担心没人喜欢我", "options": _SCARED3, "dimension": "社交焦虑"},
            {"content": "头疼或肚子疼", "options": _SCARED3, "dimension": "躯体担忧"},
            {"content": "担心考试成绩", "options": _SCARED3, "dimension": "广泛性焦虑"},
            {"content": "夜里醒来很难再睡", "options": _SCARED3, "dimension": "广泛性焦虑"},
            {"content": "遇到新情境时害怕", "options": _SCARED3, "dimension": "社交焦虑"},
            {"content": "担心家人出事", "options": _SCARED3, "dimension": "分离焦虑"},
            {"content": "害怕一个人睡觉", "options": _SCARED3, "dimension": "分离焦虑"},
            {"content": "手心出汗或颤抖", "options": _SCARED3, "dimension": "恐慌"},
            {"content": "担心无法完成作业", "options": _SCARED3, "dimension": "广泛性焦虑"},
            {"content": "害怕同学嘲笑我", "options": _SCARED3, "dimension": "社交焦虑"},
            {"content": "胸闷或呼吸困难", "options": _SCARED3, "dimension": "躯体担忧"},
            {"content": "害怕动物或昆虫", "options": _SCARED3, "dimension": "恐惧"},
            {"content": "不愿意举手发言", "options": _SCARED3, "dimension": "社交焦虑"},
            {"content": "担心父母生气", "options": _SCARED3, "dimension": "广泛性焦虑"},
            {"content": "感到莫名的害怕", "options": _SCARED3, "dimension": "恐慌"},
        ],
    },
    {
        "code": "CES-DC",
        "name": "CES-DC 儿童抑郁量表",
        "target": "儿童抑郁筛查",
        "description": "过去一周，你的下列感受符合程度如何？",
        "interpretation": [
            {"min": 0, "max": 14, "level": "无明显抑郁", "color": "green", "advice": "心理状态良好"},
            {"min": 15, "max": 19, "level": "轻度抑郁", "color": "blue", "advice": "注意自我调节"},
            {"min": 20, "max": 29, "level": "中度抑郁", "color": "orange", "advice": "建议辅导干预"},
            {"min": 30, "max": 60, "level": "重度抑郁", "color": "red", "advice": "建议专业评估"},
        ],
        "questions": [
            {"content": "被一些小事烦扰", "options": _CESDC4},
            {"content": "吃不下饭", "options": _CESDC4},
            {"content": "感到不愉快、家人朋友都无法让我开心", "options": _CESDC4},
            {"content": "觉得自己比不上同学", "options": _CESDC4},
            {"content": "注意力难以集中", "options": _CESDC4},
            {"content": "感到沮丧", "options": _CESDC4},
            {"content": "做事比平时更费劲", "options": _CESDC4},
            {"content": "对未来没希望", "options": _CESDC4},
            {"content": "觉得生活失败", "options": _CESDC4},
            {"content": "感到害怕", "options": _CESDC4},
            {"content": "睡眠不好", "options": _CESDC4},
            {"content": "感到高兴", "options": _CESDC4, "reverse": True},
            {"content": "话比平时少", "options": _CESDC4},
            {"content": "感到孤独", "options": _CESDC4},
            {"content": "觉得别人不友好", "options": _CESDC4},
            {"content": "享受生活", "options": _CESDC4, "reverse": True},
            {"content": "想哭", "options": _CESDC4},
            {"content": "感到悲伤", "options": _CESDC4},
            {"content": "觉得别人不喜欢我", "options": _CESDC4},
            {"content": "做事没精神", "options": _CESDC4},
        ],
    },
    {
        "code": "MHT",
        "name": "MHT 心理健康诊断测验（演示版）",
        "target": "综合心理健康（8 维度）",
        "description": "以下情况与你近期是否相符？",
        "interpretation": [
            {"min": 0, "max": 20, "level": "心理健康", "color": "green", "advice": "继续保持"},
            {"min": 21, "max": 35, "level": "轻微心理困扰", "color": "blue", "advice": "自我调节即可"},
            {"min": 36, "max": 55, "level": "需要关注", "color": "orange", "advice": "建议教师与家长沟通"},
            {"min": 56, "max": 80, "level": "心理问题明显", "color": "red", "advice": "建议专业心理辅导"},
        ],
        "questions": [
            # 学习焦虑
            {"content": "考试前常常睡不好", "options": _YESNO, "dimension": "学习焦虑"},
            {"content": "一想到考试就紧张", "options": _YESNO, "dimension": "学习焦虑"},
            {"content": "担心自己考不好", "options": _YESNO, "dimension": "学习焦虑"},
            {"content": "考试时容易大脑空白", "options": _YESNO, "dimension": "学习焦虑"},
            # 对人焦虑
            {"content": "在陌生人面前不敢说话", "options": _YESNO, "dimension": "对人焦虑"},
            {"content": "担心同学嘲笑我", "options": _YESNO, "dimension": "对人焦虑"},
            {"content": "不敢与老师眼神接触", "options": _YESNO, "dimension": "对人焦虑"},
            {"content": "小组活动中不愿发言", "options": _YESNO, "dimension": "对人焦虑"},
            # 孤独倾向
            {"content": "觉得没有好朋友", "options": _YESNO, "dimension": "孤独倾向"},
            {"content": "更喜欢一个人呆着", "options": _YESNO, "dimension": "孤独倾向"},
            {"content": "没有人理解我", "options": _YESNO, "dimension": "孤独倾向"},
            {"content": "课间常常独自一人", "options": _YESNO, "dimension": "孤独倾向"},
            # 自责倾向
            {"content": "做错事总是很内疚", "options": _YESNO, "dimension": "自责倾向"},
            {"content": "觉得自己给家人添麻烦", "options": _YESNO, "dimension": "自责倾向"},
            {"content": "发生不好的事总觉得是自己的错", "options": _YESNO, "dimension": "自责倾向"},
            {"content": "讨厌自己", "options": _YESNO, "dimension": "自责倾向"},
            # 过敏倾向
            {"content": "别人的一句话就让我很在意", "options": _YESNO, "dimension": "过敏倾向"},
            {"content": "对声音/光线特别敏感", "options": _YESNO, "dimension": "过敏倾向"},
            {"content": "容易被小事激怒", "options": _YESNO, "dimension": "过敏倾向"},
            {"content": "情绪起伏很大", "options": _YESNO, "dimension": "过敏倾向"},
            # 身体症状
            {"content": "经常头疼", "options": _YESNO, "dimension": "身体症状"},
            {"content": "经常肚子疼", "options": _YESNO, "dimension": "身体症状"},
            {"content": "食欲不好", "options": _YESNO, "dimension": "身体症状"},
            {"content": "容易疲劳", "options": _YESNO, "dimension": "身体症状"},
            # 恐怖倾向
            {"content": "害怕黑暗", "options": _YESNO, "dimension": "恐怖倾向"},
            {"content": "担心意外发生", "options": _YESNO, "dimension": "恐怖倾向"},
            {"content": "害怕某些特定场所", "options": _YESNO, "dimension": "恐怖倾向"},
            {"content": "经常做噩梦", "options": _YESNO, "dimension": "恐怖倾向"},
            # 冲动倾向
            {"content": "有时候想摔东西", "options": _YESNO, "dimension": "冲动倾向"},
            {"content": "容易对朋友发脾气", "options": _YESNO, "dimension": "冲动倾向"},
            {"content": "做事不考虑后果", "options": _YESNO, "dimension": "冲动倾向"},
            {"content": "遇到挫折就想放弃", "options": _YESNO, "dimension": "冲动倾向"},
        ],
    },
]
