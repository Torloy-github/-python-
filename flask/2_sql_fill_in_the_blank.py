import sqlite3
import re


class MultiChoiceDatabase:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS fill_in_the_blank_question (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT UNIQUE NOT NULL,
            option TEXT,
            answer TEXT,
            class int DEFAULT 3,
            is_used BOOLEAN DEFAULT FALSE
        )
        ''')
        self.conn.commit()

    def add_question(self, question, option, answer):
        # 将选项列表转换为字符串，以逗号分隔
        options_str = ','.join(option)
        try:
            self.cursor.execute(
                "INSERT INTO fill_in_the_blank_question (question, option, answer) VALUES (?, ?, ?)",
                (question, options_str, answer))
            self.conn.commit()  # 确保每次添加问题后提交
        except sqlite3.IntegrityError as e:
            print(f"Error inserting question '{question}': {e}")

    def get_random_question(self):
        self.cursor.execute("SELECT * FROM fill_in_the_blank_question WHERE is_used = FALSE ORDER BY RANDOM() LIMIT 1")
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()


def parse_file_and_add_to_db(file_path, db):
    # 读取答案
    answers = []
    questions = []
    opts = []
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        # 提取指定行范围的内容
        target_lines = lines[400:500]  # 294-304行是答案
        for line in target_lines:
            answer = re.sub(r'\d+\.', '', line) # 答案不需要数字点
            if answer:  # 只添加非空答案
                answers.append(answer)
                print(answer)
        print('打印输出答案长度个', len(answers))

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        # 提取指定行范围的内容
        target_lines = lines[0:399]  # 294-304行是答案
        for line in target_lines:
            line = line.strip()  # 移除首尾空格
            line = re.sub(r'^\d+\.', '', line)
            question = line
            # question = re.sub(r'\d+\.', '', line)
            if question:  # 只添加非空答案
                questions.append(question)  # 追加问题
                print(question)

        print('打印输出答案长度个', len(questions))
    # 添加问题到数据库
    for question, answer in zip(questions, answers):
        db.add_question(question, '', answer)



# 主程序
db = MultiChoiceDatabase('db/question.db')  # 初始化数据库
parse_file_and_add_to_db('question/fill_in_the_blank.txt', db)  # 解析文件并添加题目
parse_file_and_add_to_db('question/fill_in_the_blank_1.txt', db)  # 解析文件并添加题目

# 获取一道随机多选题进行测试
random_question = db.get_random_question()
if random_question:
    print(f"Question: {random_question[1]}")  # 打印题目
    print(f"Option :{random_question[2]}")  # 打印每个选项
    print(f"Correct Answers: {random_question[3]}")  # 打印正确答案
    print(f"class: {random_question[4]}")  # 打印使用状态
    print(f"is_used: {random_question[5]}")  # 打印使用状态

# 关闭数据库连接
db.close()
