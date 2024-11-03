import sqlite3
import re


class MultiChoiceDatabase:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS multiple_answer_question (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT UNIQUE NOT NULL,
            option TEXT,
            answer TEXT,
            class int DEFAULT 2,
            is_used BOOLEAN DEFAULT FALSE
        )
        ''')
        self.conn.commit()

    def add_question(self, question, options, answer):
        # 将选项列表转换为字符串，以逗号分隔
        options_str = ', '.join(options)
        try:
            self.cursor.execute("INSERT INTO multiple_answer_question (question, option, answer) VALUES (?, ?, ?)",(question, options_str, answer))
            self.conn.commit()  # 确保每次添加问题后提交
        except sqlite3.IntegrityError as e:
            print(f"Error inserting question '{question}': {e}")


    def get_random_question(self):
        self.cursor.execute("SELECT * FROM multiple_answer_question WHERE is_used = FALSE ORDER BY RANDOM() LIMIT 1")
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()


def parse_file_and_add_to_db(file_path, db):
    # 读取题目和选项
    question = ''
    questions = []
    options = []
    opt=''
    # 读取答案
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        # 提取指定行范围的内容
        target_lines = lines[400:500]  # 295-305行是答案
        answers = []
        for line in target_lines:
            line = re.sub(r'\s+', '', line)  # 移除所有空格
            line_answers = re.findall(r'(\d+)\.([A-Z]+)', line)  # 提取题号和答案
            print(line_answers)
            for answer in line_answers:  # 遍历答案
                answers.append(answer[1])  # 追加答案
        print('打印输出答案个数:', len(answers))
        print('打印输出答案:', answers)


    target_lines = lines[0:399]  # 读取题目行

    for line in target_lines:
        line = line.strip()  # 移除首尾空格

        # 判断是否为题目行
        if re.match(r'^\d+\..*', line):
            line = re.sub(r'^\d+\.', '', line) # 移除 22.
            if question:  # 如果已经有题目，保存当前题目和选项
                questions.append((question, options))  # 保存题目和选项
                print(f"保存题目: {question} | 选项: {options}")  # 打印保存的题目和选项
            question = line  # 更新当前题目
            options = []  # 清空选项列表

        # 判断是否为选项行
        elif re.match(r'^[A-F]\..*', line):
            options.append(line)  # 添加选项到列表

    if question:  # 如果已经有题目，保存当前题目和选项
        questions.append((question, options))  # 保存题目和选项
        print(f"保存题目: {question} | 选项: {options}")  # 打印保存的题目和选项

    # 添加问题到数据库
    for index in range(len(questions)):
        question = questions[index][0]
        opt = questions[index][1]
        answers[index]
        db.add_question(question, opt, answers[index])
    # for index, (question, options) in enumerate(questions):
    #     # correct_answer = answers[index] if index < len(answers) else ''
    #     db.add_question(question, options, answers[index])


# 主程序
db = MultiChoiceDatabase('db/question.db')  # 初始化数据库
parse_file_and_add_to_db('question/multiple_answer_question.txt', db)  # 解析文件并添加题目
parse_file_and_add_to_db('question/multiple_answer_question_1.txt', db)  # 解析文件并添加题目
parse_file_and_add_to_db('question/multiple_answer_question_2.txt', db)  # 解析文件并添加题目


# 获取一道随机多选题进行测试
random_question = db.get_random_question()
if random_question:
    print(f"Question: {random_question[1]}")  # 打印题目
    options = random_question[2].split(', ')  # 分割选项
    for i, option in enumerate(options):
        print(f"Option {chr(65 + i)}: {option.strip()}")  # 打印每个选项
    print(f"Correct Answers: {random_question[3]}")  # 打印正确答案
    print(f"class: {random_question[4]}")  # 打印使用状态
    print(f"is_used: {random_question[5]}")  # 打印使用状态

# 关闭数据库连接
db.close()
