import sqlite3
import random
import threading
import time
import tkinter as tk
from tkinter import ttk
from turtledemo.penrose import start

import pygame
from PIL import Image, ImageTk
from tkinter import messagebox
from time import sleep
from playsound import playsound

# conda create --name flask python=3.12
# 设置抽题数量的全局变量
# 复赛题目类型
single_choice_num_revival = 6
multiple_choice_num_revival = 3
fill_in_the_blank_num_revival = 0
# 决赛题目类型
single_choice_num_final = 7
multiple_choice_num_final = 5
fill_in_the_blank_num_final = 1

# 定义全局变量 answered_question
global answered_questions
global timer_running
global time_sound_thread
timer_running = False
answered_questions = []
num_all_question = -1  # 当前题目数量
#########################测试部分#########################
# 设置抽题数量的全局变量
# 复赛题目类型
# single_choice_num_revival = 1
# multiple_choice_num_revival = 1
# fill_in_the_blank_num_revival = 1
# # 决赛题目类型
# single_choice_num_final = 2
# multiple_choice_num_final = 1
# fill_in_the_blank_num_final = 0
##################仅供测试使用###############################

# 存储抽取出的题目列表
revival_question_list = []  # 复活赛题目列表
final_question_list = []  # 决赛题目列表

# 初始化 Pygame
pygame.mixer.init()  # 初始化 Pygame，音乐播放效果
correct_sound = pygame.mixer.Sound('music/回答正确.mp3')
wrong_sound = pygame.mixer.Sound('music/回答错误.mp3')
hint_sound = pygame.mixer.Sound('music/蜡笔小新.mp3')
start_sound = pygame.mixer.Sound('music/20s倒计时最佳版本.mp3')
# 创建一个锁
sound_lock = threading.Lock()

# 设置字体样式
topic_font_style = ("Arial", 28, "bold")
answer_font_style = ("Arial", 28)


# 定义按钮样式
def create_button(text, command, relx, style):
    button = ttk.Button(root, text=text, command=command, style=style,width=5)
    button.place(relx=relx, rely=0.9, anchor='center')


def play_sound(sound):
    """播放音效，确保音效不会重叠"""
    with sound_lock:
        sound.play()


class DatabaseManager:
    def __init__(self, db_name):
        self.conn = self.create_connection(db_name)
        self.setup_database()

    def create_connection(self, db_name):
        """创建数据库连接"""
        try:
            conn = sqlite3.connect(db_name)
            return conn
        except sqlite3.Error as e:
            print(f"数据库连接错误: {e}")
            return None

    def setup_database(self):
        """设置数据库表结构"""
        try:
            with self.conn:
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS single_answer_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question TEXT,
                        option TEXT,
                        answer TEXT,
                        class int DEFAULT 1,
                        is_used BOOLEAN DEFAULT FALSE
                )''')

                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS multiple_answer_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question TEXT,
                        option TEXT,
                        answer TEXT,
                        class int DEFAULT 2,
                        is_used BOOLEAN DEFAULT FALSE
                )''')
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS fill_in_the_blank_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question TEXT,
                        option TEXT,
                        answer TEXT,
                        class int DEFAULT 3,
                        is_used BOOLEAN DEFAULT FALSE
                )''')
        except sqlite3.Error as e:
            print(f"设置数据库表结构错误: {e}")

    def mark_question_used(self, table_name, question_id):
        """标记题目为已使用"""
        try:
            with self.conn:
                self.conn.execute(f"UPDATE {table_name} SET is_used = TRUE WHERE id =?", (question_id,))
        except sqlite3.Error as e:
            print(f"标记题目为已使用错误: {e}")

    def get_random_question(self, table_name):
        """从数据库中随机抽取未使用的题目"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} WHERE is_used = 0 ORDER BY RANDOM() LIMIT 1")
            return cursor.fetchone()  #  cursor.fetchone() 返回一个包含结果行的元组，如果没有结果，则返回 None。
        except sqlite3.Error as e:
            print(f"随机抽取题目错误: {e}")
            return None


def generate_random_questions(round_type):
    """根据轮次生成随机题目"""
    global single_choice_num_revival, multiple_choice_num_revival, fill_in_the_blank_num_revival, single_choice_num_final, multiple_choice_num_final, fill_in_the_blank_num_final
    if round_type == "复赛":
        single_answer_num = single_choice_num_revival
        multiple_answer_num = multiple_choice_num_revival
        fill_in_the_blank_num = fill_in_the_blank_num_revival
    if round_type == "决赛":
        single_answer_num = single_choice_num_final
        multiple_answer_num = multiple_choice_num_final
        fill_in_the_blank_num = fill_in_the_blank_num_final
        print('fill_in_the_blank_num',fill_in_the_blank_num)

    # single_answer_num = single_choice_num_revival if round_type == "复活赛" else single_choice_num_final
    # multiple_answer_num = multiple_choice_num_revival if round_type == "复活赛" else multiple_choice_num_final
    # fill_in_the_blank_num = fill_in_the_blank_num_revival if round_type == "复活赛" else multiple_choice_num_final
    #
    question_types = []
    for _ in range(single_answer_num):
        question_types.append('single_answer')
    for _ in range(multiple_answer_num):
        question_types.append('multiple_answer')

    random.shuffle(question_types) # 这样改进的目的是保证最后一道题是填空题
    for _ in range(fill_in_the_blank_num):
        question_types.append('fill_in_the_blank')

    # random.shuffle(question_types)

    questions = []
    for question_type in question_types:
        question = db_manager.get_random_question(f"{question_type}_question")
        if question:
            db_manager.mark_question_used(f"{question_type}_question", question[0])
            questions.append(question)
    print('questions:', questions)
    return questions


# 答题界面的轮播加载
def handle_round(round_type):  # round_type: 轮次
    """处理特定轮次的逻辑"""
    global revival_question_list, final_question_list,answered_questions  # 引入全局变量
    if round_type == "复赛" :
        question_list=final_question_list  # 选择题目列表
    else:
        question_list=revival_question_list
    # question_list = revival_question_list if round_type == "复赛" else final_question_list  # 选择题目列表
    question_list.clear()  # 清空题目列表
    answered_questions=[] # 清空专属 bgm 记录值
    questions = generate_random_questions(round_type)  # 创建数据库连接
    global num_all_question
    num_all_question = len(questions)
    question_list.extend(questions)  # 添加题目到题目列表
    show_questions_in_main_window(round_type, question_list)  # 打开特定轮次的题目窗口


def show_questions_in_main_window(round_type, questions):
    """在主窗口中显示题目"""
    global root
    for widget in root.winfo_children():
        widget.destroy()
    root.title(f"{round_type}答题界面")
    global num_all_question
    # num_all_questions = len(questions)  # 记录题目数
    now_num_question = num_all_question - len(questions) + 1  # 记录题目数
    print(f"题目数now_num_question: {now_num_question}")
    if questions:  # 确保问题列表不为空
        load_background_image('image/题目.png')  # 背景加载 F5F5F5
        root.configure(bg='#F5F5F5')  # 设置题目背景颜色
        question_data = questions.pop(0)
        # num_now_question=num_now_question-1  # 当前题号减一
        show_single_question(question_data, root, now_num_question, questions)  # 传递 questions
        # 传递当前题号
    else:
        back_button = tk.Button(root, text="返回主界面",font=answer_font_style, command=create_main_interface,relief='flat', borderwidth=0,highlightthickness=0)
        back_button.pack(pady=400)


def show_single_question(question_data, root, question_number, questions):
    """显示单个题目"""
    root.title(f"第{question_number}题")  # 设置窗口标题
    question_label = tk.Label(root, text=question_data[1], padx=100, pady=5, anchor='w')  # 左对齐
    question_label.configure(bg='#F5F5F5', font=topic_font_style)  # 设置题目背景颜色
    question_label.pack(pady=(20, 10), anchor='w')  # 设置题目间距

    options = [option.strip() for option in question_data[2].split(',')]  # 选项列表
    correct_answers = question_data[3]  # 正确选项的字符，例如 'A', 'AB' 等
    question_type = question_data[4]  # 题型（1：单选，2：多选，3：填空）
    selected_options = []  # 存储选择的选项字符

    ##########################倒计时部分##########################
    # # 创建倒计时标签
    # timer_label = tk.Label(root, text="20", font=("Arial", 24, "bold"), fg="red", bg='#F5F5F5')
    # timer_label.place(x=1300, y=20)
    #
    # # 计时相关变量
    # global timer_running
    # timer_running = True
    #
    # def countdown(t):
    #     """倒计时函数"""
    #     global timer_running
    #     if timer_running:
    #         if t >= 0:
    #             mins, secs = divmod(t, 60)
    #             if timer_label.winfo_exists():
    #                 timer_label.config(text=f"{mins:02}:{secs:02}")
    #             root.after(1000, countdown, t - 1)
    #         else:
    #             stop_music()
    #             timer_running = False
    #     else:
    #         return
    #
    # def start_timer():
    #     """启动倒计时和音乐"""
    #     filename='music/20s倒计时最佳版本.mp3'
    #     pygame.mixer.music.load(filename)
    #     pygame.mixer.music.play()
    #     countdown(20)
    #
    # def stop_timer():
    #     """停止计时"""
    #     global timer_running
    #     timer_running = False
    #
    # def stop_music():
    #     """停止音乐"""
    #     pygame.mixer.music.stop()
    #     pygame.mixer.music.stop()
    #
    # # 调用开始计时
    # start_timer()

    ##########################倒计时部分##########################

    def toggle_option(option_char, button):
        """切换选项的选择状态"""
        if option_char in selected_options:
            selected_options.remove(option_char)
            button.configure(bg="white")
        else:
            selected_options.append(option_char)
            button.configure(bg="red")

    def check_answer():
        global timer_running
        timer_running = False
        # stop_music()
        """检查用户选择的答案"""
        if question_type in [1, 2]:  # 单选或多选题
            user_answer = ''.join(sorted(selected_options))  # 用户选择的答案
            correct_answer_string = ''.join(sorted(correct_answers))  # 正确答案
            if user_answer == correct_answer_string:
                global answered_questions
                answered_questions.append(True)  # 标记为回答正确-bgm
                result_text = f"回答正确！正确答案是: {correct_answers}"
                result_fg = "green"
                threading.Thread(target=play_sound, args=(correct_sound,)).start()  # 播放音效
            else:
                answered_questions.append(False)  # 标记为回答错误-bgm
                result_text = f"回答错误！正确答案是: {correct_answers}"
                result_fg = "red"
                threading.Thread(target=play_sound, args=(wrong_sound,)).start()  # 播放音效

        else:  # 填空题
            answered_questions.append(True)  # 标记为回答正确-bgm
            result_text = f"填空题的答案是: {correct_answers}"
            result_fg = "blue"

        # 显示结果标签
        result_label = tk.Label(root, text=result_text, fg=result_fg)  # 设置结果标签
        result_label.configure(bg='#F5F5F5')  # 设置结果标签背景颜色
        result_label.pack(pady=10)
        print('answered_questions', answered_questions)
        print('num_all_question', num_all_question)
        # 弹窗特效+专属 bgm
        if len(answered_questions) == num_all_question and all(answered_questions):
            ########################特效1#############################################
            # top = tk.Toplevel(root)
            # top.title("恭喜！")
            # label = tk.Label(top, text="选择题答案全对，恭喜你获得专属 BGM 奖励一首！", fg="gold", bg='red', font=("Arial", 20, "bold"))
            # label.pack(pady=20)
            # # threading.Thread(target=play_sound, args=(special_bgm,)).start()
            # threading.Thread(target=play_sound, args=(hint_sound,)).start()  # 播放专属 bgm
            #########################################################################

            ########################特效2##############################################
            # 创建冒泡弹窗并左右晃动
            # 创建冒泡弹窗并从左至右抖动
            top = tk.Toplevel(root)
            top.title("恭喜！选择题答案全对，解锁史诗级奖励！！！！")
            label = tk.Label(top, text="恭喜你获得专属 BGM 奖励一首！", fg="gold", bg='red', font=("Arial", 20, "bold"))
            label.pack(pady=20)
            threading.Thread(target=play_sound, args=(hint_sound,)).start()

            def shake_window():
                left_pos = 0
                right_pos = root.winfo_screenwidth() - top.winfo_width()
                current_pos = left_pos
                step = 5
                direction = 1
                while current_pos < right_pos:
                    top.geometry(f"+{current_pos}+{top.winfo_y()}")
                    current_pos += step * direction
                    if current_pos >= right_pos or current_pos <= left_pos:
                        direction *= -1
                    root.update()
                    time.sleep(0.05)

            threading.Thread(target=shake_window).start()

            def shake_window():
                current_x = top.winfo_x()
                direction = 5
                for _ in range(10):
                    top.geometry(f"+{current_x}+{top.winfo_y()}")
                    current_x += direction
                    if current_x >= root.winfo_screenwidth() - top.winfo_width() or current_x <= 0:
                        direction *= -1
                    root.update()
                    time.sleep(0.05)

            threading.Thread(target=shake_window).start()

    # 创建选项按钮
    if question_type in [1, 2]:  # 单选或多选题
        for index, option in enumerate(options):
            option_char = chr(65 + index)
            frame = tk.Frame(root)
            frame.pack(anchor='w', padx=100, pady=5)

            button = tk.Button(frame, bg="white", font=("Arial", 14),
                               command=lambda char=option_char: toggle_option(char, button))
            button.pack(side='left')  # 按钮在左侧

            option_label = tk.Label(frame, text=f"{option}", anchor='w',font=answer_font_style)
            option_label.pack(side='left', padx=(5, 0))  # 选项文本在右侧

    elif question_type == 3:  # 填空题
        fill_label = tk.Label(root, text="请选手口头作答，核对答案点击提交:", anchor='w')
        fill_label.pack(padx=100, pady=(20, 10), anchor='w')


    create_button("提交", lambda: check_answer(), 0.4,'TButton')
    create_button("下题", lambda: show_questions_in_main_window("复活赛" if len(revival_question_list) > 0 else "决赛",questions), 0.6,'TButton')


# 背景加载函数
def load_background_image(image_path = "image/副本主背景.png"):
    """加载背景图像"""
    # image_path = "image/副本主背景.png"

    try:
        img = Image.open(image_path)
        window_width = root.winfo_screenwidth()
        window_height = root.winfo_screenheight()
        img_ratio = img.width / img.height
        window_ratio = window_width / window_height

        if img_ratio > window_ratio:
            new_width = window_width
            new_height = int(window_width / img_ratio)
        else:
            new_height = window_height
            new_width = int(window_height * img_ratio)

        img = img.resize((new_width, new_height), Image.LANCZOS)
        img = ImageTk.PhotoImage(img)
        background_label = tk.Label(root, image=img)
        background_label.image = img
        background_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"加载背景图错误: {e}")
        messagebox.showerror("错误", f"加载背景图错误：{e}")


def create_main_interface():
    """创建主界面"""
    global root
    if root is None:
        root = tk.Tk()
        root.state('zoomed')
        root.title("济南大学“我心系党，理论润心”知识问答竞赛暨第九届“学宪法，讲宪法”理论知识大赛")
    else:
        for widget in root.winfo_children():
            widget.destroy()
    load_background_image()  # 背景加载

    # 创建按钮样式
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TButton', font=('Arial', 18), background='#9C191E', foreground='black')


    create_button("复赛", lambda: handle_round("复赛"), 0.4,'TButton')
    create_button("决赛", lambda: handle_round("决赛"), 0.6,'TButton')

# 确保在程序中调用 create_main_interface() 函数

if __name__ == "__main__":
    # 初始化主窗口和数据库管理器
    root = None
    db_manager = DatabaseManager('db/question_suffer.db')
    create_main_interface()
    root.mainloop()
