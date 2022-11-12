# 导入tkinter类库
import tkinter.font
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Scrollbar, Checkbutton, Label, Button  # tkk里面的组件会有所优化
from PIL import Image, ImageTk
import json
import idlelib.colorizer as idc
import idlelib.percolator as idp
import WaveDromGen.language as language_dict

class WaveNote:
    # 工具栏所用图片的名称
    icons = ["render", "copy", "paste",
             "undo", "redo", "find_text"]
    icon_res = []

    # 初始化操作
    def __init__(self, frame, asset_dir, update_wave, language):
        """
        :param frame: 上层 frame
        :param asset_dir: 素材路径
        :param update_wave: 更新波形函数
        :param language: ui语言
        """
        self.asset_dir = asset_dir
        self.root = frame
        self.language = language

        # 调用方法
        self.context_text = None  # 当前文本
        self.line_number_bar = None  # 行号
        self.update_wave = update_wave  # 更新波形图

        self.create_tool_bar()  # 工具栏

        self.create_body()  # 文本输入区域

    def render(self):
        """
        将当前内容渲染
        :return: None
        """
        json_db = self.get()
        try:
            db = json.loads(json_db)
            self.update_wave(db)
        except json.decoder.JSONDecodeError as e:
            messagebox.showerror('Error', e.msg)

    def find_text_dialog(self):
        """
        生成查找对话框
        :return: None
        """
        search_dialog = Toplevel(self.root)
        search_dialog.title(self.lang('find'))
        search_dialog.iconbitmap(self.asset_dir + 'app.ico')

        # 居中
        max_width, max_height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()  # 宽高
        align_center = "300x80+%d+%d" % ((max_width - 300) / 2, (max_height - 80) / 2)
        search_dialog.geometry(align_center)
        search_dialog.resizable(False, False)
        Label(search_dialog, text=self.lang('find_text'), width=8).grid(row=0, column=0)
        search_text = Entry(search_dialog, width=25)
        search_text.grid(row=0, column=1, padx=2, pady=2, sticky="we")
        search_text.focus_set()
        # 忽略大小写
        ignore_case_value = IntVar()
        Checkbutton(search_dialog, text=self.lang('ignore_case'), variable=ignore_case_value).grid(
            row=1, column=1, sticky='e', padx=2, pady=2
        )
        Button(search_dialog, width=5, text=self.lang('find'),
               command=lambda: self.search_result(search_text.get(), ignore_case_value.get(), search_dialog,
                                                  search_text)).grid(row=0, column=2, sticky="w" + "e", padx=10, pady=1)

        def close_search_dialog():
            """
            关闭查找文本对话框
            :return: None
            """
            self.context_text.tag_remove('match', 1.0, END)
            search_dialog.destroy()

        search_dialog.protocol("WM_DELETE_WINDOW", close_search_dialog)
        return "break"

    def search_result(self, key, ignore_case, search_dialog, search_box):
        """
        查找的方法
        :param key:
        :param ignore_case:
        :param search_dialog:
        :param search_box:
        :return:
        """
        self.context_text.tag_remove('match', 1.0, END)
        matches_found = 0
        if key:
            start_pos = 1.0
            while True:
                start_pos = self.context_text.search(key, start_pos,
                                                     nocase=ignore_case,
                                                     stopindex=END)
                if not start_pos:
                    break
                end_pos = "{}+{}c".format(start_pos, len(key))
                self.context_text.tag_add('match', start_pos, end_pos)
                matches_found += 1
                start_pos = end_pos
            self.context_text.tag_config('match', foreground='white',
                                         background='green')
        search_box.focus_set()
        search_dialog.title(self.lang('match_found') % matches_found)

    def select_all(self):
        """
        全选
        :return:
        """
        self.context_text.tag_add('sel', 1.0, END)
        return "break"

    def create_tool_bar(self):
        """
        创建工具栏
        :return: None
        """
        tool_bar = Frame(self.root, height=25, background="#ffffff")  # 容器Frame，白色
        # 填充x轴
        tool_bar.pack(fill="x")
        # Label(tool_bar, width=4, background='white').pack(side="left")
        # 生成图片文件放到对应的位置
        for icon in self.icons:
            tool_icon = Image.open(self.asset_dir + "%s.gif" % icon)  # 因为是元组所以有个逗号
            tool_icon = tool_icon.resize((16, 16), Image.ANTIALIAS)
            tool_icon = ImageTk.PhotoImage(tool_icon)
            tool_btn = Button(tool_bar, image=tool_icon, command=self.tool_bar_action(icon))
            tool_btn.pack(side="left")  # 图片左对齐
            # 将tool_icon添加到icon_res里
            self.icon_res.append(tool_icon)

    def tool_bar_action(self, action_type):
        """
        工具栏行为映射
        :param action_type:
        :return:
        """
        def handle():
            if action_type == "render":
                self.render()
            elif action_type == "copy":
                self.context_text.event_generate("<<Copy>>")
            elif action_type == "paste":
                self.context_text.event_generate("<<Paste>>")
            elif action_type == "undo":
                self.context_text.event_generate("<<Undo>>")
            elif action_type == "redo":
                self.context_text.event_generate("<<Redo>>")
            elif action_type == "find_text":
                self.find_text_dialog()

        # handle返回处理
        return handle

    def create_body(self):
        """
        创建编辑区
        :return:
        """
        # 左：行号；右：滚动条；中：文本编辑区
        # 行号区域

        self.line_number_bar = Text(self.root, width=3, padx=3, takefocus=0, border=0, background="#f0f0f0",
                                    state="disabled", font=("Courier", 12, tkinter.font.ROMAN))  # state="disable"不能编辑状态
        # 左边填充整个y轴
        self.line_number_bar.pack(side='left', fill='y')
        # 文本编辑区
        # undo=True是否具备文本取消功能，wrap:如何换行，word:按照单词自动换行,expand：可以拉伸
        self.context_text = Text(self.root, wrap="word", undo=True, font=("Courier", 12, tkinter.font.ROMAN))

        # 热键绑定
        self.context_text.bind('<Any-KeyPress>', lambda e: self.update_line_num())
        self.context_text.pack(fill='both', expand=True)

        # 设置文本输入区
        self.context_text.tag_config("active_line", background="#ffffff")

        # 滚动条
        scroll_bar = Scrollbar(self.context_text)
        scroll_bar['command'] = self.context_text.yview
        self.context_text["yscrollcommand"] = scroll_bar.set
        scroll_bar.pack(side="right", fill="y")

        # 高亮语法
        p = idp.Percolator(self.context_text)
        d = idc.ColorDelegator()
        d.recolorize()
        p.insertfilter(d)

    def update_line_num(self):
        """
        行号处理
        :return:
        """
        # 获取所有行
        row, col = self.context_text.index(END).split('.')
        # 列举每行的行号
        line_num_content = "\n".join([str(i) for i in range(1, int(row))])
        self.line_number_bar.config(state="normal")
        self.line_number_bar.delete(1.0, END)
        self.line_number_bar.insert(1.0, line_num_content)
        self.line_number_bar.config(state='disabled')

    def set(self, dic):
        # 排版
        txt = json.dumps(dic, indent=1)
        self.context_text.delete('1.0', END)
        self.context_text.insert(END, txt)
        # 更新行号
        self.update_line_num()

    def get(self):
        return self.context_text.get('1.0', END)

    def lang(self, id):
        """
        从语言库中获取UI文字
        :param id:
        :return:
        """
        sel = language_dict.language[self.language]
        return language_dict.lib[id][sel]
