# coding=utf-8
import json
import os
import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import filedialog
from tkinter.messagebox import showinfo
from PIL import ImageTk, Image
from WaveDromGen.WaveDromCtrl import WaveDromCtrl
from WaveDromGen.WaveNote import WaveNote
from WaveDromGen.WaveImageDB import WaveImageDB
import WaveDromGen.language as language_dict


class WaveDromUI:
    def __init__(self):
        title = 'WaveDromGen'
        width, height = 1080, 720  # 窗口尺寸
        self.version = 'V1.3.0'  # 版本号

        self.inity = 30  # 初始 stepy
        self.initx = 40  # 初始 stepx

        self.stepy = 30  # 实际 stepy
        self.stepx = 40  # 实际 stepx

        self.scale_ratio = 1  # 缩放值（整数）

        # 建立临时文件夹
        self.tmp_dir = 'tmp/'  # 临时文件夹
        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)

        # 建立图片文件
        self.asset_dir = 'tmp/asset/'
        if not os.path.isdir(self.asset_dir):
            os.mkdir(self.asset_dir)
        WaveImageDB(self.asset_dir)

        # 建立 GUI 窗口
        root = Tk()
        root.title(title)
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        align_str = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        root.geometry(align_str)
        # root.resizable(width=False, height=False)
        # 图标
        root.iconbitmap(self.asset_dir + 'app.ico')

        # UI 全局变量
        self.root = root
        self.img_view = None  # 绘图区 canvas
        self.skin = None  # 皮肤
        self.scale = None  # 缩放
        self.editmenu = None  # 编辑菜单（为了动态改变undo/redo态设置为全局）
        self.x_line = None  # 指针水平线
        self.y_line = None  # 指针垂直线
        self.mini_img = None  # 缩略图，移动行时显示缩略图动画
        self.ctrl_press = IntVar()  # 检测是否按压ctrl，实现按住ctrl完成复制

        # 颜色图标缓存
        self.red = None
        self.green = None
        self.light = None
        self.blue = None
        self.orange = None
        self.yellow = None
        self.white = None

        self.icon_pool = []  # 图片池，将用到的图标设置为全局变量，防止图标资源被释放
        self.ctrl = WaveDromCtrl()  # 例话控制单元
        self.ascii_note = None  # 文本编辑器对象
        self.img = {}  # 图片dict，存放没行对应图片缓存
        self.cursor = IntVar()  # 开启光标
        self.cursor.set(1)  # 默认开启
        self.mode = StringVar()  # 工作模式
        self.mode.set('sig')  # 默认 singal mode
        self.position = StringVar()  # 指针所在位置
        self.busColor = StringVar()  # 总线颜色
        self.busColor.set('=')  # 默认白色
        self.x_name_offset = 1  # 由于信号名变长后波形图将向右拓展，此变量根据信号名长度变化
        # 保存文件类型
        self.filetype = [
            ('Json Files', '*.json'),
            ('PNG Files', '*.png'),
            ('SVG Files', '*.svg'),
        ]
        self.lastPos = (0, 0)  # 上一次坐标
        self.savefile = None  # 保存文件名，为 None 则打开文件夹选择
        self.language = StringVar()  # ui菜单语言

        # 设置语言，通过在tmp下生产en/cn文件实现，切换时，删除其他语言文件
        if os.path.isfile(self.tmp_dir + 'en'):
            self.language.set('en')
        elif os.path.isfile(self.tmp_dir + 'cn'):
            self.language.set('cn')
        else:
            self.language.set('en')

        # 菜单栏
        self.menubar_view(root)

        # 选项视图
        sheet = ttk.Notebook(root)
        wave_frame = Frame()
        note_frame = Frame()
        ascii_frame = Frame()
        sheet.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # 建立sheet
        sheet.add(wave_frame, text=self.lang('wave'))
        sheet.add(note_frame, text=self.lang('editor'))
        sheet.add(ascii_frame, text=self.lang('ascii'))

        self.sheet = sheet
        self.wave_frame = wave_frame

        self.statusbar_view(wave_frame)  # 状态栏
        self.buttonbar_view(wave_frame)  # 按钮栏
        self.wave_view(wave_frame)  # 绘图区
        # 编辑器区
        self.note = WaveNote(frame=note_frame, asset_dir=self.asset_dir, update_wave=self.restore_json,
                             language=self.language.get())
        self.ascii_view(ascii_frame)  # ascii区

        # 绑定快捷事件
        root.bind("<Control-o>", lambda x: self.load())
        root.bind("<Control-s>", lambda x: self.saveas(self.savefile))
        root.bind("<Control-n>", lambda x: self.new())
        root.bind("<Control-z>", lambda x: self.operate('undo'))
        root.bind("<Control-Z>", lambda x: self.operate('redo'))
        root.bind("<Control-l>", lambda x: self.operate('addRow'))
        root.bind("<Control-w>", lambda x: self.operate('SWAP'))
        root.bind("<Control-t>", lambda x: self.set_phase_period())
        root.bind('<KeyPress-Control_L>', lambda x: self.ctrl_press.set(1))
        root.bind('<KeyRelease-Control_L>', lambda x: self.ctrl_press.set(0))

        # 生成全局图标缓存（yes/no，使用居多）
        icon_y = Image.open(self.asset_dir + "y.gif")
        icon_y = icon_y.resize((20, 20), Image.ANTIALIAS)
        self.icon_y = ImageTk.PhotoImage(icon_y)

        icon_n = Image.open(self.asset_dir + "n.gif")
        icon_n = icon_n.resize((20, 20), Image.ANTIALIAS)
        self.icon_n = ImageTk.PhotoImage(icon_n)

        self.update()
        root.mainloop()

    def ascii_view(self, root):
        """
        创建ascii view
        :param root: 上级 frame
        :return: None
        """

        def copy_ascii():
            """
            将 ascii note内容拷贝至 clipboard
            :return: None
            """
            txt = ascii_note.get('1.0', tk.END)
            root.clipboard_clear()
            root.clipboard_append(txt)

        btn = Button(root, text=self.lang('copy'), relief=tk.GROOVE, bg='white', command=copy_ascii)
        x_scroll = tk.Scrollbar(root, orient=tk.HORIZONTAL)
        y_scroll = tk.Scrollbar(root)

        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        btn.pack(side=BOTTOM, fill=tk.X)  # 布局顺序影响界面效果
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        ascii_note = Text(root, wrap='none', font=("Courier", 10, tk.font.ROMAN))
        self.ascii_note = ascii_note

        ascii_note.pack(side=TOP, fill=tk.BOTH, expand=True)

        x_scroll.config(command=self.ascii_note.xview)
        y_scroll.config(command=self.ascii_note.yview)

        ascii_note.config(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    def menubar_view(self, root):
        """
        菜单栏 view
        :param root: 上层 fram
        :return: None
        """
        menubar = Menu(root)
        lang = self.lang
        #  文件栏
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label=lang('new'), accelerator='Ctrl+N', command=self.new)
        filemenu.add_command(label=lang('open'), accelerator='Ctrl+O', command=self.load)
        filemenu.add_command(label=lang('save'), accelerator='Ctrl+S', command=lambda: self.saveas(self.savefile))
        filemenu.add_command(label=lang('save_as'), command=self.saveas)

        filemenu.add_separator()
        filemenu.add_command(label=lang('exit'), accelerator='Alt+F4', command=root.quit)
        menubar.add_cascade(label=lang('file'), menu=filemenu)

        editmenu = Menu(menubar, tearoff=0)
        self.editmenu = editmenu
        editmenu.add_command(label=lang('undo'), accelerator='Ctrl+Z', command=lambda: self.operate('undo'),
                             state=tk.DISABLED)
        editmenu.add_command(label=lang('redo'), accelerator='Ctrl+Shift+Z', command=lambda: self.operate('redo'),
                             state=tk.DISABLED)
        editmenu.add_separator()

        editmenu.add_command(label=lang('add_row'), accelerator='Ctrl+L', command=lambda: self.operate('addRow'))
        editmenu.add_command(label=lang('add_col'), command=lambda: self.operate('addCol'))
        editmenu.add_separator()

        editmenu.add_command(label=lang('del_row'), command=lambda: self.mode.set('delROW'))
        editmenu.add_command(label=lang('del_col'), command=lambda: self.mode.set('delCol'))
        editmenu.add_separator()

        menubar.add_cascade(label=lang('edit'), menu=editmenu)

        editmenu.add_command(label=lang('copy_row'), command=lambda: self.mode.set('COPY'))
        editmenu.add_command(label=lang("swap_row"), accelerator='Ctrl+W', command=lambda: self.operate('SWAP'))
        editmenu.add_separator()

        editmenu.add_command(label=lang('sig_early'), command=lambda: self.mode.set('earlyWave'))
        editmenu.add_command(label=lang('sig_delay'), command=lambda: self.mode.set('delayWave'))

        # 显示
        display_menu = Menu(menubar, tearoff=0)

        def set_color(x):
            """
            设置总线颜色
            :param x: 可选'=', '3', '4', '5', '6', '7', '8', '9'，对应 wavedrom 语法
            :return: None
            """
            [st.set(0) for st in color_status]  # 复位
            color_status[color_tag.index(x)].set(1)  # 更新选中值
            self.busColor.set(x)
            self.mode.set('bus')

        # 选择总线颜色
        color_tag = ['=', '3', '4', '5', '6', '7', '8', '9']
        color_status = [IntVar() for i in range(len(color_tag))]
        color_status[0].set(1)  # 默认为白色（=）
        bus_color_menu = Menu(display_menu, tearoff=0)

        self.white = ImageTk.PhotoImage(Image.open(self.asset_dir + "white.gif"))
        self.yellow = ImageTk.PhotoImage(Image.open(self.asset_dir + "yellow.gif"))
        self.orange = ImageTk.PhotoImage(Image.open(self.asset_dir + "orange.gif"))
        self.blue = ImageTk.PhotoImage(Image.open(self.asset_dir + "blue.gif"))
        self.light = ImageTk.PhotoImage(Image.open(self.asset_dir + "light.gif"))
        self.green = ImageTk.PhotoImage(Image.open(self.asset_dir + "green.gif"))
        self.red = ImageTk.PhotoImage(Image.open(self.asset_dir + "red.gif"))
        bus_color_menu.add_checkbutton(image=self.white, variable=color_status[0], command=lambda: set_color('='))
        bus_color_menu.add_checkbutton(image=self.yellow, variable=color_status[1], command=lambda: set_color('3'))
        bus_color_menu.add_checkbutton(image=self.orange, variable=color_status[2], command=lambda: set_color('4'))
        bus_color_menu.add_checkbutton(image=self.blue, variable=color_status[3], command=lambda: set_color('5'))
        bus_color_menu.add_checkbutton(image=self.light, variable=color_status[4], command=lambda: set_color('6'))
        bus_color_menu.add_checkbutton(image=self.green, variable=color_status[5], command=lambda: set_color('7'))
        bus_color_menu.add_checkbutton(image=self.red, variable=color_status[6], command=lambda: set_color('9'))
        display_menu.add_cascade(label=lang('bus_color'), menu=bus_color_menu)

        def set_skin(x):
            """
            设置皮肤
            :param x: 'default', 'lowkey', 'narrow'
            :return: None
            """
            [st.set(0) for st in skin_status]  # 复位
            skin_status[skin_tag.index(x)].set(1)  # 更新选中值
            if x == 'narrow':  # 重设比例系数
                self.stepx = self.initx * 0.5
                self.scale_ratio = 0.5
            else:
                set_scale(1)
            self.ctrl.set_skin(x)
            self.update()

        skin_tag = ['default', 'lowkey', 'narrow']
        skin_status = [IntVar() for i in range(len(skin_tag))]
        skin_status[0].set(1)
        self.skin = set_skin
        skin_menu = Menu(display_menu, tearoff=0)
        skin_menu.add_checkbutton(label=lang('default'), variable=skin_status[0], command=lambda: set_skin('default'))
        skin_menu.add_checkbutton(label=lang('lowkey'), variable=skin_status[1], command=lambda: set_skin('lowkey'))
        skin_menu.add_checkbutton(label=lang('narrow'), variable=skin_status[2], command=lambda: set_skin('narrow'))

        display_menu.add_cascade(label=lang('skin'), menu=skin_menu)

        def set_scale(x):
            """
            设置缩放系数
            :param x: int
            :return: None
            """
            [st.set(0) for st in scale_status]  # 复位
            scale_status[scale_tag.index(x)].set(1)  # 更新选中值
            self.img_view.delete(ALL)
            # 调整比例更改带来的偏移
            self.stepx = self.initx * x
            self.scale_ratio = x
            # 更新图像
            self.ctrl.set_scale_ratio(x)
            self.update()

        scale_tag = [1, 2, 3]
        scale_status = [IntVar() for i in range(len(scale_tag))]
        scale_status[0].set(1)
        self.scale = set_scale
        scale_menu = Menu(display_menu, tearoff=0)
        scale_menu.add_checkbutton(label="1x", variable=scale_status[0], command=lambda: set_scale(1))
        scale_menu.add_checkbutton(label="2x", variable=scale_status[1], command=lambda: set_scale(2))
        scale_menu.add_checkbutton(label="3x", variable=scale_status[2], command=lambda: set_scale(3))

        display_menu.add_cascade(label=lang('scale'), menu=scale_menu)

        display_menu.add_separator()
        display_menu.add_command(label=lang('period'), accelerator='Ctrl+T', command=self.set_phase_period)

        annotate_menu = Menu(display_menu, tearoff=0)
        annotate_menu.add_command(label=lang('edge'), command=lambda: self.mode.set('Node'))

        def node_relation():
            """
            打开边沿关系面板，设置各个边沿关系
            """
            node = ''
            for y in range(self.ctrl.get_row_len()):
                node += ''.join(self.ctrl.read_node(y=y))
            node_list = list(node.replace('.', ''))
            style_list = (
                '~', '-~', '<~>', '<-~>', '~>', '-~>', '~->', '-', '-|',
                '-|-', '<->', '<-|>', '<-|->', '->', '-|>', '-|->', '|->', '+'
            )  # 由 wavedrom 定义
            relation_list = []

            def add_relative(edge1=None, edge2=None, text=None):
                """
                添加沿到沿关系标注
                :param edge1:
                :param edge2:
                :param text: char，标注文字
                :return: None
                """
                edge1_str = StringVar()
                edge2_str = StringVar()
                text_str = StringVar()

                # 如果设置值，将字符变量初始化
                if edge1:
                    edge1_str.set(edge1)
                if edge2:
                    edge2_str.set(edge2)
                if text:
                    text_str.set(text)

                frame_edit = Frame(top)
                frame_edit.pack(side=TOP)
                edge1 = ttk.Combobox(frame_edit, width=10, textvariable=edge1_str)
                edge2 = ttk.Combobox(frame_edit, width=10, textvariable=edge2_str)
                entry = Entry(frame_edit, width=10, textvariable=text_str)
                edge1.pack(side=LEFT)
                edge2.pack(side=LEFT)
                entry.pack(side=LEFT)

                edge1['value'] = node_list
                edge2['value'] = node_list

                relation_list.append([edge1_str, edge2_str, text_str])

            def commit():
                """
                提交结果
                :return: None
                """
                ret = []
                sign = style_com.get()
                for relation in relation_list:
                    edge1, edge2, arrow = [j.get() for j in relation]
                    if edge1 and edge2 and arrow and sign:  # 不存在空值时
                        ret.append('{0}{1}{2} {3}'.format(edge1, sign, edge2, arrow))
                self.ctrl.write_edge(ret)
                top.destroy()

            # 创建弹出窗口
            top = Toplevel()
            top.title(lang('annotate'))
            screenwidth = root.winfo_screenwidth()
            screenheight = root.winfo_screenheight()
            width, height = 400, 400
            align_str = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
            top.geometry(align_str)

            self.style = StringVar()
            frame_tip = Frame(top)
            frame_tip.pack(side=TOP)
            Label(frame_tip, text=lang('style')).pack(side=LEFT)
            style_com = ttk.Combobox(frame_tip, width=5, textvariable=self.style)
            style_com.pack(side=LEFT)
            Button(frame_tip, text=lang('add'), command=add_relative).pack(side=LEFT)
            Button(frame_tip, text=lang('yes'), command=commit).pack(side=LEFT)
            Button(frame_tip, text=lang('cancel'), command=lambda: top.destroy()).pack(side=LEFT)
            style_com["value"] = style_list
            style_com.current(4)  # 默认风格4

            # 加载已有 edge
            edge_list = self.ctrl.read_edge()
            for i in edge_list:
                tmp, rel = i.split(' ')
                tmp = list(tmp)
                e1, e2 = tmp[0], tmp[-1]
                add_relative(edge1=e1, edge2=e2, text=rel)

        annotate_menu.add_command(label=lang('relation'), command=node_relation)
        display_menu.add_cascade(label=lang('annotate'), menu=annotate_menu)
        menubar.add_cascade(label=lang('display'), menu=display_menu)

        # 帮助栏
        help_menu = Menu(menubar, tearoff=0)
        lang_menu = Menu(help_menu, tearoff=0)
        help_menu.add_checkbutton(label=lang('display_cursor'), variable=self.cursor, onvalue=1)

        lang_menu.add_checkbutton(label=lang('en'), variable=self.language, onvalue='en',
                                  command=lambda: self.set_language('en'))
        lang_menu.add_checkbutton(label=lang('cn'), variable=self.language, onvalue='cn',
                                  command=lambda: self.set_language('cn'))
        help_menu.add_cascade(label=lang('language'), menu=lang_menu)

        def doc():
            """
            打开帮助文档
            :return: None
            """
            url = 'https://gitee.com/sjkpy/WaveDromGen'
            import webbrowser
            webbrowser.open(url, new=0, autoraise=True)

        help_menu.add_command(label=lang('doc'), command=doc)
        help_menu.add_separator()

        def about():
            """
            关于应用
            :return: None
            """
            # 创建弹出窗口
            top = Toplevel(background='white')
            top.title(self.lang('about'))
            top.iconbitmap(self.asset_dir + 'app.ico')
            screenwidth = root.winfo_screenwidth()
            screenheight = root.winfo_screenheight()
            width, height = 300, 300
            alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
            top.geometry(alignstr)

            image = Image.open(self.asset_dir + 'app.ico')
            image = image.resize((128, 128), Image.ANTIALIAS)
            self.app = ImageTk.PhotoImage(image)

            Label(top, image=self.app, background='white').pack(side=tk.TOP, pady=10)
            Label(top, text='WaveDromGen', background='white', font=("Courier", 18, tk.font.ROMAN)).pack()
            Label(top, text='Version: ' + self.version, background='white', font=("Courier", 10, tk.font.ROMAN)).pack()
            Label(top, text='  By Henson', background='white', font=("Courier", 8, tk.font.ROMAN)).pack()
            Button(top, text=self.lang('ok'), width=10, background='white', relief='groove',
                   command=lambda: top.destroy()).pack(pady=16)

        help_menu.add_command(label=lang('about'), command=about)
        menubar.add_cascade(label=lang('help'), menu=help_menu)
        root.config(menu=menubar)

    def buttonbar_view(self, root):
        """
        生成按钮栏
        :param root: 上层 frame
        :return: None
        """
        button_view_root = Frame(root, bg='white')
        button_view_root.pack(side=LEFT, fill=Y, padx=2)

        items = ['clk', 'sig', 'bus', 'x', 'gap', 'z', 'SEL', 't', 'clr']

        # 空白 label，用于占位
        Label(button_view_root, bg='white', height=1).pack()
        # 创建 button
        for itm in items:
            image = Image.open(self.asset_dir + "%s.gif" % itm)
            image = image.resize((22, 22), Image.ANTIALIAS)
            icon = ImageTk.PhotoImage(image)
            # Button(button_view_root, image=icon).pack(anchor='w')
            Radiobutton(button_view_root, bg='white', image=icon, variable=self.mode, value=itm,
                        indicatoron=False).pack(anchor='w', pady=2)
            self.icon_pool.append(icon)  # 防止图片被释放

    def statusbar_view(self, root):
        """
        生成状态栏
        :param root: 上层 frame
        :return: None
        """
        status_view = Frame(root, bg='white')
        status_view.pack(side=BOTTOM, fill=X, pady=2)
        Label(status_view, bg='white', text='  status:').pack(side=LEFT)
        Label(status_view, bg='white', textvariable=self.mode, anchor=NW).pack(side=LEFT, fill=X, pady=2)
        Label(status_view, bg='white', textvariable=self.position, anchor=NW).pack(side=RIGHT, fill=X, pady=2)

    def wave_view(self, root):
        """
        生成绘图区
        :param root: 上层 frame
        :return: None
        """

        # 由缩放改变产生偏移变化
        # k:scale系数，v:偏移值
        scale_offset = {
            0.5: -3,
            1: -1.5,
            2: -0.2,
            3: 0.3
        }

        def create_rectangle(x1, y1, x2, y2, fill, alpha):
            """
            绘制透明框
            :param x1:
            :param y1:
            :param x2:
            :param y2:
            :param fill: 填充色
            :param alpha: 透明度
            :return: tk object
            """
            alpha = int(alpha * 255)
            fill = root.winfo_rgb(fill) + (alpha,)
            image = Image.new('RGBA', (x2 - x1, y2 - y1), fill)
            self.bbox = ImageTk.PhotoImage(image)
            return img_view.create_image(x1, y1, image=self.bbox, anchor='nw')

        def get_pos(event):
            """
            获取当前触摸行列
            :param event:
            :return: tuple,(x, y)
            """
            cal = event.x / self.stepx - self.x_name_offset * 0.5 + scale_offset[self.scale_ratio]
            x = -1 if cal < 0 else int(cal)  # x 有名字的 offset
            if x < -1:
                x = -1
            y = event.y // self.stepy
            self.position.set('(X:%2s, Y:%2s)  ' % (x, y))
            return x, y

        def gen_edit_box(event, x, y, b1_motion=False, node_mode=None):
            """
            产生悬浮的编辑框
            :param event: 事件位置，获取原始点击位置
            :param x: 点击列
            :param y: 点击行
            :param b1_motion: 按下左键拖动时，触发响应操作
            :param node_mode: 进入编辑 node 属性
            :return: None
            """

            # 确认提交
            def submit(event=None):
                value = edit_box.get(0.0, "end").replace('\n', '')
                self.ctrl.t_mode(x=x, y=y, val=value, node_mode=node_mode)
                self.update()
                editbox_view.destroy()

            # 按住 b1 拖动时，不进行操作
            if b1_motion:
                return
            # -1 列为信号名，选中时读取信号名属性
            elif x == -1:
                val = self.ctrl.read_name(y=y)
            # 当为标注模式时，访问 node 属性
            elif node_mode:
                val = self.ctrl.read_node(x=x, y=y)
            else:
                val = self.ctrl.read_data(x=x, y=y)
            editbox_view = Frame(wave_view, bg='white')
            editbox_view.place(x=event.x-self.stepx, y=y * self.stepy)  # 当 x 为负数时，将坐标指向 0

            # 编辑框
            edit_box = Text(editbox_view, width=15, height=1)
            edit_box.pack(side=LEFT)
            edit_box.insert('end', val)
            edit_box.bind("<Return>", submit)
            # 确认按钮
            Button(editbox_view, width=12, relief='groove', image=self.icon_y, command=submit).pack(side=LEFT)
            Button(editbox_view, width=12, relief='groove', image=self.icon_n,
                   command=lambda: editbox_view.destroy()).pack(side=LEFT)

            edit_box.tk_focusFollowsMouse()  # 将鼠标聚焦到编辑框


        def click(event, b1_motion=False):
            """
            点击事件
            :param event:
            :param b1_motion: 当按住左键移动时触发
            :return: None
            """
            mode = self.mode.get()

            # 当按照b1移动时，不更新当前坐标
            if b1_motion:
                x, y = event.x, event.y
            else:
                x, y = get_pos(event)
            # 超出db长度时，除了mode为SEL，都不执行
            if y >= self.ctrl.get_row_len() or x >= self.ctrl.get_col_len():
                if mode == 'SEL':
                    if y >= self.ctrl.get_row_len():
                        self.ctrl.add_row(y - self.ctrl.get_row_len() + 1)
                    if x >= self.ctrl.get_col_len():
                        self.ctrl.add_col(x - self.ctrl.get_col_len() + 1)
                else:
                    return None

            # 模式与对应处理函数
            if mode == 'sig':
                self.ctrl.sig_mode(x, y, b1_motion=b1_motion)
            elif mode == 'clk':
                self.ctrl.clk_mode(x, y)
            elif mode == 'bus':
                self.ctrl.bus_mode(x, y, val=self.busColor.get())
            elif mode == 'x':
                self.ctrl.x_mode(x, y)
            elif mode == 'z':
                self.ctrl.z_mode(x, y)
            elif mode == 'gap':
                self.ctrl.gap_mode(x, y)
            elif mode == 't':
                gen_edit_box(event=event, x=x, y=y, b1_motion=b1_motion)
            elif mode == 'Node':
                gen_edit_box(event=event, x=x, y=y, b1_motion=b1_motion, node_mode=True)
            elif mode == 'delROW':
                self.img_view.delete(ALL)
                self.ctrl.del_row(y=y)
            elif mode == 'delCol':
                self.img_view.delete(ALL)
                self.ctrl.del_col(x=x)
            elif mode == 'clr':
                self.ctrl.clear(y=y)
            elif mode == 'earlyWave':
                self.ctrl.early_wave(x=x, y=y)
            elif mode == 'delayWave':
                self.ctrl.delay_wave(x=x, y=y)

            self.update()
            if not b1_motion:
                self.lastPos = (x, y)

        def b1motion(event):
            """
            按住 b1 拖动事件
            :param event:
            :return: None
            """
            x, y = get_pos(event)
            # 超出范围
            if y >= self.ctrl.get_row_len():
                return None
            # 当mode为SWAP或COPY时，绘制动画
            elif self.mode.get() in ['SWAP', 'COPY', 'SEL']:
                if self.mini_img:  # 移动缩略图
                    img_view.moveto(self.mini_img, x=(event.x - self.lastPos[0]), y=event.y - self.stepy // 2)
                    img_view.moveto(self.x_line, x=0, y=event.y - self.stepy // 2)
                else:  # 创建缩略图
                    self.mini_img = self.img_view.create_image(0, event.y + self.stepy // 2, image=self.img[y],
                                                               anchor='nw')
                    self.lastPos = (event.x, self.lastPos[1])
            elif not self.lastPos == (x, y):  # 拖到时操作判定
                # 按住 b1 拖动时只改变 x 值不改变 y 值
                event.x, event.y = x, self.lastPos[1]
                click(event, b1_motion=True)
                self.lastPos = (x, y)

            # 更新纵轴
            img_view.moveto(self.y_line, x=event.x)

        def release(event):
            """
            释放 b1 事件
            :param event:
            :return: None
            """
            mode = self.mode.get()
            x, y = get_pos(event)
            if y >= self.ctrl.get_row_len():  # 超出范围
                pass
            elif mode == 'SEL':
                if not y == self.lastPos[1]:  # 纵向移动
                    if self.ctrl_press.get():
                        self.ctrl.copy_line(src=self.lastPos[1], dst=y)
                    else:
                        self.ctrl.swap_line(src=self.lastPos[1], dst=y)
                else:  # 横向移动
                    x_offset = (event.x - self.lastPos[0]) // self.stepx
                    if x_offset > 0:
                        self.ctrl.delay_wave(x=x - 1, y=y, num=x_offset)
                    elif x_offset < 0:
                        self.ctrl.early_wave(x=x - 1, y=y, num=abs(x_offset))
                    self.update()
            elif mode == 'SWAP':
                self.ctrl.swap_line(src=self.lastPos[1], dst=y)
            elif mode == 'COPY':
                self.ctrl.copy_line(src=self.lastPos[1], dst=y)
            # 删除缩略图图片
            self.img_view.delete(self.mini_img)
            self.mini_img = None
            self.update()

        def motion(event):
            """
            鼠标移动事件
            :param event:
            :return: None
            """
            x, y = get_pos(event)
            img_view.moveto(self.x_line, y=y * self.stepy)
            img_view.moveto(self.y_line, x=event.x)

        def enter(event):
            """
            鼠标进入事件
            :param event:
            :return: None
            """
            x, y = get_pos(event)
            width_x = img_view.winfo_screenwidth()
            width_y = img_view.winfo_screenheight()
            if self.cursor.get():
                self.y_line = img_view.create_line(event.x, 0, event.x, width_y, fill='lightgray', dash=(6, 6))
                self.x_line = create_rectangle(0, y * self.stepy, width_x, (y + 1) * self.stepy, fill='black',
                                               alpha=0.1)

        def leave(event):
            """
            鼠标离开时触发
            :param event:
            :return:
            """
            img_view.delete(self.x_line)
            img_view.delete(self.y_line)

        # 构建绘图窗口
        wave_view = Frame(root, bg='white')
        wave_view.pack(fill=BOTH, expand=True)
        img_view = Canvas(wave_view, bg='white')
        img_view.pack(side=LEFT, anchor=N, fill=BOTH, expand=True)
        self.img_view = img_view

        # 事件绑定
        img_view.bind('<Button-1>', click)
        img_view.bind('<B1-Motion>', b1motion)
        img_view.bind('<ButtonRelease-1>', release)
        img_view.bind('<Motion>', motion)
        img_view.bind('<Enter>', enter)
        img_view.bind('<Leave>', leave)

    def restore_json(self, json_db):
        """
        将编辑框 json db 内容保存
        :param json_db:
        :return:
        """
        self.ctrl.restore_json(json_db)
        self.update()
        self.sheet.select(self.wave_frame)

    def update(self):
        """
        更新内部变量和图像
        :return: None
        """
        # self.ctrl.query()
        # 计算信号名长度带来的偏移量
        self.x_name_offset = ((self.ctrl.get_name_len() - 4) / 2.5) + 1

        for k, v in self.ctrl.imgDB.items():
            # im = Image.open(v)
            im = v
            w, h = im.size
            self.img[k] = ImageTk.PhotoImage(im)
            # 绘制空白矩形删除原图像
            self.img_view.create_rectangle(0, k * self.stepy, w, h + k * self.stepy, fill='white', outline='white')
            # 更新图片内容
            self.img_view.create_image(0, k * self.stepy, image=self.img[k], anchor=NW)

        # 更新文本
        self.note.set(self.ctrl.read_all())
        self.set_ascii(self.ctrl.to_ascii())

        # 更新undo/redo状态
        undo_len, redo_len = self.ctrl.get_history_len()
        self.editmenu.entryconfig(0, state=tk.DISABLED if undo_len == 0 else tk.ACTIVE)
        self.editmenu.entryconfig(1, state=tk.DISABLED if redo_len == 0 else tk.ACTIVE)

        # 将光标移到顶层
        if self.x_line:
            self.img_view.tag_raise(self.x_line)
            self.img_view.tag_raise(self.y_line)
        if self.mini_img:  # 移动缩略图
            self.img_view.tag_raise(self.mini_img)
            self.img_view.tag_raise(self.y_line)

    def new(self):
        """
        新建窗口
        :return: None
        """
        self.skin('default')
        self.scale(1)
        self.ctrl.init()
        self.img_view.delete(ALL)
        self.update()
        self.busColor.set('=')

    def saveas(self, fname=None):
        """
        保存为
        :param fname: 文件名，若未指定文件名，开启选择窗口
        :return: None
        """
        if fname is None:
            f = filedialog.asksaveasfile(initialdir=".", filetypes=self.filetype, defaultextension=self.filetype)
        else:
            f = open(fname, 'w')
        # 保存文件
        if f is None:
            return
        else:
            self.ctrl.save(handle=f)
        self.savefile = f.name

    def load(self, filename=None):
        """
        载入 json 文件
        :param filename: 文件名，不指定时打开选择菜单
        :return: None
        """
        if filename is None:
            filename = filedialog.askopenfilename(initialdir=".", filetypes=self.filetype)
        if not filename:
            return
        self.img_view.delete(ALL)
        self.ctrl.restore(filename=filename)
        self.update()

    def set_phase_period(self):
        """
        设置相位和周期
        :return: None
        """
        # 创建弹出窗口
        root = self.root
        top = Toplevel()
        top.title(self.lang('period'))
        top.iconbitmap(self.asset_dir + 'app.ico')
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        width, height = 400, 400
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        top.geometry(alignstr)

        frame_tip = Frame(top)
        frame_btn = Frame(top)

        frame_tip.pack(side=TOP)
        frame_btn.pack(side=BOTTOM)

        old_phase = []
        old_period = []
        new_phase = []
        new_period = []
        Label(frame_tip, text=self.lang('signal'), anchor=W, width=30).grid(row=0, column=0, padx=10)
        Label(frame_tip, text=self.lang('phase'), anchor=W, width=5).grid(row=0, column=1, padx=10)
        Label(frame_tip, text=self.lang('period'), anchor=W, width=5).grid(row=0, column=2, padx=10)
        for i in range(self.ctrl.get_row_len()):
            nu = i + 1
            name = self.ctrl.read_name(i)
            phase = self.ctrl.get_phase(i)
            period = self.ctrl.get_period(i)

            phase_text = DoubleVar()
            phase_text.set(phase)
            period_text = IntVar()
            period_text.set(period)

            old_period.append(period)
            old_phase.append(phase)
            new_period.append(period_text)
            new_phase.append(phase_text)

            Label(frame_tip, text=name, anchor=W, width=30).grid(row=nu, column=0, padx=10)
            Entry(frame_tip, width=5, textvariable=phase_text).grid(row=nu, column=1, padx=10)
            Entry(frame_tip, width=5, textvariable=period_text).grid(row=nu, column=2, padx=10)

        def commit():
            """
            提交编辑框结果
            :return: None
            """
            period_change = [not new_period[j].get() == old_period[j] for j in range(self.ctrl.get_row_len())]
            phase_change = [not new_phase[j].get() == old_phase[j] for j in range(self.ctrl.get_row_len())]
            # 写回db
            for j in range(self.ctrl.get_row_len()):
                if period_change[j]:
                    self.ctrl.set_period(j, new_period[j].get())
                if phase_change[j]:
                    self.ctrl.set_phase(j, new_phase[j].get())
            change_line = [period_change[j] or phase_change[j] for j in range(self.ctrl.get_row_len())]
            # 记录更新的行号
            line = 0
            ret = []
            for change in change_line:
                if change:
                    ret.append(line)
                line += 1
            # 重新渲染
            self.ctrl.renderLine(ret)
            self.update()
            top.destroy()

        Button(frame_btn, text=self.lang('yes'), command=commit).pack(side=LEFT, padx=10)
        Button(frame_btn, text=self.lang('cancel'), command=lambda: top.destroy()).pack(side=LEFT, padx=10)

    def operate(self, cmd, num=5):
        """
        解析命令执行对应操作
        :param num: 增加行/列数量
        :param cmd:操作命令
        :return: None
        """
        if cmd == 'addRow':
            self.ctrl.add_row(num=num)
        elif cmd == 'addCol':
            self.ctrl.add_col(num=num)
        elif cmd == 'undo':
            self.ctrl.undo()
        elif cmd == 'redo':
            self.ctrl.redo()
        elif cmd == 'SWAP':
            self.mode.set('SWAP')

        self.update()

    def set_ascii(self, txt):
        """
        将ascii字符串写入界面
        :param txt: ascii字符串
        :return: None
        """
        self.ascii_note.delete('1.0', END)
        self.ascii_note.insert(END, txt)

    def set_language(self, language):
        """
        设置系统语言
        :param language: 语言类型
        :return: None
        """
        # 删除旧缓存文件
        for i in language_dict.language:
            filename = self.tmp_dir + i
            if os.path.isfile(filename):
                os.remove(filename)
        f = open(self.tmp_dir + language, 'w')
        f.close()
        # 反馈
        tip = self.lang('tip')
        text = self.lang('restart_assert')
        showinfo(tip, text)

    def lang(self, id):
        """
        从语言库中获取UI文字
        :param id:
        :return:
        """
        sel = language_dict.language[self.language.get()]
        return language_dict.lib[id][sel]


if __name__ == "__main__":
    wg = WaveDromUI()
