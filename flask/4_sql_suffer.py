# -*- coding: utf-8 -*-
# -------------------------------
# @软件：PyCharm 
# @PyCharm：2024.2.2
# @Python：3.12
# @项目：code

# -------------------------------

# @文件：4_sql_suffer.py
# @时间：2024/10/24 22:40:56
# @作者：Torloy
# @邮箱：528128687@qq.com

# -------------------------------
import sqlite3
import random
import re

##########打乱选项函数###############################
def process_options(option_string, answer_string):
    # 去掉空格
    cleaned_option_string = option_string.replace(" ", "")

    # 提取选项并去掉开头的大写字母和.
    o = [opt[2:].strip() for opt in re.findall(r'([A-Z]\.[^,]+)(?:,)?', cleaned_option_string)]

    # 创建 a 列表，长度与 options 相同，初始值为 0
    a = [0] * len(o)

    # 根据 answer 更新 a 列表
    for char in answer_string:
        index = ord(char) - ord('A')  # 获取字符的索引位置
        if 0 <= index < len(a):  # 确保索引在范围内
            a[index] = 1  # 将对应位置更新为 1

    # a 和 options 同时进行随机换位操作
    for _ in range(len(a)):
        i = random.randint(0, len(a) - 1)
        j = random.randint(0, len(a) - 1)
        a[i], a[j] = a[j], a[i]
        o[i], o[j] = o[j], o[i]

    # 给选项加上大写字母前缀
    o1 = [f"{chr(65 + i)}.{option}" for i, option in enumerate(o)]

    # 根据标记生成 a1 列表
    a1 = []
    for i in range(len(a)):
        z = chr(65 + i)
        if a[i] == 1:
            a1.append(z)  # 转换为对应的字母
        else:
            a1.append("")  # 用空字符串替代

    # 将列表转换为字符串
    options_string = ', '.join(o1) # 这里加了空格是为了还原：    options_string = ', '.join(o1)
    a2_string = ''.join([char for char in a1 if char])  # 只保留非空字符

    return options_string, a2_string


def shuffle_options_and_save(src_db_path, dest_db_path):
    try:
        # 连接到源数据库
        src_conn = sqlite3.connect(src_db_path)
        src_cursor = src_conn.cursor()

        # 连接到目标数据库
        dest_conn = sqlite3.connect(dest_db_path)
        dest_cursor = dest_conn.cursor()

        # 创建目标数据库的表（如果尚未存在）
        dest_cursor.execute('''
            CREATE TABLE IF NOT EXISTS single_answer_question (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                option TEXT,
                answer TEXT,
                class INT DEFAULT 1,
                is_used BOOLEAN DEFAULT FALSE
            )
        ''')

        dest_cursor.execute('''
            CREATE TABLE IF NOT EXISTS multiple_answer_question (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                option TEXT,
                answer TEXT,
                class INT DEFAULT 2,
                is_used BOOLEAN DEFAULT FALSE
            )
        ''')

        # 读取单项选择题
        src_cursor.execute("SELECT id, question, option, answer FROM single_answer_question")
        single_answer_question = src_cursor.fetchall()

        # 读取多项选择题
        src_cursor.execute("SELECT id, question, option, answer FROM multiple_answer_question")
        multiple_answer_question = src_cursor.fetchall()

        # 打乱单项选择题选项并保存到新数据库
        for question in single_answer_question:
            question_id, question_text, options, answer = question
            options_output, a2_output = process_options(options, answer)

            # 打印打乱前的选项
            print(f"单项选择题 ID:{question_id} 打乱前的选项:{options} 打乱前的答案:{answer}")
            # 打印打乱后的选项
            print(f"单项选择题 ID:{question_id} 打乱后的选项:{options_output.replace(' ','')} 打乱后的答案:{a2_output.replace(' ','')}")
            print('\n')
            # 检查目标数据库中是否已存在该数据
            dest_cursor.execute("SELECT COUNT(*) FROM single_answer_question WHERE id = ?", (question_id,))
            if dest_cursor.fetchone()[0] == 0:  # 不存在时插入
                dest_cursor.execute(
                    "INSERT INTO single_answer_question (id, question, option, answer) VALUES (?, ?, ?, ?)",
                    (question_id, question_text, options_output, a2_output))

        # 打乱多项选择题选项并保存到新数据库
        for question in multiple_answer_question:
            question_id, question_text, options, answer = question
            options_output, a2_output = process_options(options, answer)
            # 打印打乱前的选项
            print(f"多项选择题 ID:{question_id} 打乱前的选项:{options} 打乱前的答案:{answer}")
            # 打印打乱后的选项
            print(f"多项选择题 ID:{question_id} 打乱后的选项:{options_output.replace(' ','')} 打乱后的答案:{a2_output.replace(' ','')}")
            print('\n')
            # 检查目标数据库中是否已存在该数据
            dest_cursor.execute("SELECT COUNT(*) FROM multiple_answer_question WHERE id = ?", (question_id,))
            if dest_cursor.fetchone()[0] == 0:  # 不存在时插入
                dest_cursor.execute(
                    "INSERT INTO multiple_answer_question (id, question, option, answer) VALUES (?, ?, ?, ?)",
                    (question_id, question_text, options_output, a2_output))

        # 提交更改
        dest_conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")

    finally:
        # 确保关闭数据库连接
        if src_conn:
            src_conn.close()
        if dest_conn:
            dest_conn.close()


def copy_fill_in_the_blank_table(src_db_path, dest_db_path):
    """
    复制源数据库中的 fill_in_the_blank_question 表到目标数据库。
    """
    try:
        # 连接到源数据库
        src_conn = sqlite3.connect(src_db_path)
        src_cursor = src_conn.cursor()

        # 连接到目标数据库
        dest_conn = sqlite3.connect(dest_db_path)
        dest_cursor = dest_conn.cursor()

        # 读取 fill_in_the_blank_question 表
        src_cursor.execute("SELECT * FROM fill_in_the_blank_question;")
        rows = src_cursor.fetchall()
        columns = [column[0] for column in src_cursor.description]

        # 创建目标表
        dest_cursor.execute(f"CREATE TABLE IF NOT EXISTS fill_in_the_blank_question ({', '.join(columns)});")

        # 插入数据
        for row in rows:
            placeholders = ', '.join(['?'] * len(row))
            dest_cursor.execute(f"INSERT INTO fill_in_the_blank_question VALUES ({placeholders})", row)

        # 提交更改
        dest_conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")

    finally:
        # 确保关闭数据库连接
        if src_conn:
            src_conn.close()
        if dest_conn:
            dest_conn.close()

# 打乱单选表和多选表的选项和答案
# 调用函数并传入源数据库和目标数据库路径
shuffle_options_and_save('db/question.db', 'db/question_suffer.db')

copy_fill_in_the_blank_table('db/question.db', 'db/question_suffer.db')