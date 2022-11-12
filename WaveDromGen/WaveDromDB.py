# coding=utf-8
import json


class WaveDromDB:
    def __init__(self):
        init_colum = 20

        # 供外部访问变量
        self.rowLen = 0
        self.colLen = 0
        self.nameLen = 0
        self.undoLen = 0
        self.redoLen = 0

        # 私密变量
        self.special = ['=', '2', '3', '4', '5', '6', '7', '8', '9']  # 特殊变量，用于总线描述
        self.__undo_list = []
        self.__redo_list = []
        self.history_depth = 5  # history buffer深度
        self.__db = {}  # 核心数据库
        # 初始数据库内容
        self.__init_db = {
            'signal': [
                {
                    'name': 'clk',
                    'wave': 'p' + '.' * (init_colum - 1),
                    'node': '.' * init_colum,
                    'data': '',
                    'phase': 0,
                    'period': 1
                },
                {
                    'name': 'rstn',
                    'wave': '01' + '.' * (init_colum - 2),
                    'node': '.' * init_colum,
                    'data': '',
                    'phase': 0,
                    'period': 1
                },
                {
                    'name': 'signal',
                    'wave': '0' + '.' * (init_colum - 1),
                    'node': '.' * init_colum,
                    'data': '',
                    'phase': 0,
                    'period': 1
                },

            ],
            'edge': [],
            'config': {
                'hscale': 1,
                'skin': 'default'
            },
            # 'head': {
            #     'text': '',
            #     'tick': 0,
            #     'every': 1
            # },
        }

        # 初始化
        self.init()

    def init(self):
        """
        初始化
        :return: None
        """
        self.write_all(self.__init_db)
        self.__update()

    def write(self, typ, val, k=None, y=None, x=None, insert_mode=False):
        """
        写入数据，写入wave时自动进行虚拟数据到真是数据转换
        :param typ: 配置类型signal，edge，config
        :param val: 写入值
        :param k: key
        :param y: 行号
        :param x: 列号
        :param insert_mode: 在指定位置插入元素，否则，将替换该位置元素
        :return: None
        """
        if typ == 'signal':
            db = self.__db['signal'][y][k]
            if x is None:  # 没有 x 时写入整行
                self.__db['signal'][y][k] = val
            else:  # 有 x 时写入具体数
                if insert_mode:
                    self.__db['signal'][y][k] = db[:x] + val + db[x:]
                else:
                    self.__db['signal'][y][k] = db[:x] + val + db[x + 1:]

            if k == 'name':  # 写入信号名时，更新名字长度
                self.nameLen = max(len(i['name']) for i in self.__db['signal'])
            elif k == 'wave':  # 写入波形时，进行 virtual -> physical 转换
                self.__db['signal'][y][k] = self.__decode(y)
                # print(111, self.__db[typ][y][k])
        elif typ == 'edge':
            self.__db['edge'] = val
        elif typ == 'config':
            self.__db['config'][k] = val

    def read(self, typ, k=None, y=None, x=None, pop_mode=False):
        """
        读取数据
      :param typ: 配置类型signal，edge，config
        :param k: key
        :param y: 行号
        :param x: 列号
        :param pop_mode: 弹出指定位置的元素，否则，将读取该位置元素
        :return: str
        """
        if typ == 'signal':
            if k == 'wave':  # 写入波形时，进行 physical -> virtual  转换
                if pop_mode:
                    if x == 0:
                        self.__db['signal'][y][k] = self.__db['signal'][y][k][x + 1:]
                    else:
                        self.__db['signal'][y][k] = self.__db['signal'][y][k][:x - 1] + self.__db['signal'][y][k][x:]
                else:
                    virtual = self.__code(y)
                    return virtual if x is None else virtual[x]
            else:
                return self.__db['signal'][y][k] if x is None else self.__db['signal'][y][k][x]
        elif typ == 'edge':
            return self.__db['edge']
        elif typ == 'config':
            return self.__db['config'][k]

    def write_all(self, val):
        """
        写入整个数据库
        :param val: 数据字典
        :return: None
        """
        self.__db = val
        self.__update()

    def read_all(self):
        """
        读取整个数据库
        :return: dict
        """
        return self.__db.copy()

    def insert_row(self, num):
        """
        在行尾插入行
        :param num: 插入行数
        :return:
        """
        new = {
            'name': 'signal',
            'wave': '0' + '.' * (self.colLen - 1),
            'node': '.' * self.colLen,
            'data': '',
            'phase': 0,
            'period': 1
        }
        for i in range(num):
            self.__db['signal'].append(new.copy())
        self.rowLen += num

    def insert_col(self, num):
        """
        在列尾插入列
        :param num: 插入列数
        :return: None
        """
        for i in range(self.rowLen):
            wave = self.__init_db['signal'][i]['wave']
            node = self.__init_db['signal'][i]['node']
            self.__init_db['signal'][i]['wave'] = wave + '.' * num
            self.__init_db['signal'][i]['node'] = node + '.' * num
        self.colLen += num
        self.__update()

    def swap_line(self, typ, src, dst, copy_mode=False):
        """
        将src行内容与dst行内容交换
        :param typ: 数据种类
        :param src: source行索引
        :param dst: destination行索引
        :param copy_mode: 将复制src行到dst行，将额外增加1行
        :return: None
        """
        if copy_mode:
            tmp = self.__db[typ][src].copy()
        else:
            tmp = self.__db[typ].pop(src)
        self.__db[typ].insert(dst, tmp)
        self.__update()

    def del_row(self, typ, y):
        """
        删除行
        :param typ: 数据种类
        :param y: 行索引
        :return: None
        """
        self.__db[typ].pop(y)
        self.__update()

    def del_col(self, typ, x):
        """
        删除列
        :param typ:数据种类
        :param x: 列索引
        :return: None
        """
        for i in range(self.rowLen):
            wave = self.__db[typ][i]['wave']
            node = self.__db[typ][i]['node']
            self.__db[typ][i]['wave'] = wave[:x] + wave[x + 1:]
            self.__db[typ][i]['node'] = node[:x] + node[x + 1:]
        self.__update()

    def __update(self):
        """
        更新类成员变量
        :return:
        """
        self.rowLen = len(self.__db['signal'])
        self.colLen = len(self.__db['signal'][0]['wave'])
        self.nameLen = max(len(i['name']) for i in self.__db['signal'])

    def __code(self, y):
        """
        对wave数据从真实向虚拟转换，即把“."转换为真实值
        例： 实际     -> 虚拟
            1..0..1 -> 1110001
        :param y: 行索引
        :return: str
        """
        wave = self.__db['signal'][y]['wave']
        sign = '.'
        ret = ''
        for i in wave:
            if not i == '.':
                sign = i
            ret += i if sign in self.special else sign
        return ret

    def __decode(self, y):
        """
        对wave数据从虚拟向真实转换，即把重复值转换为'.'
        例： 虚拟     -> 真实
            1110011 -> 1.。0.1.
        :param y: 行索引
        :return: str
        """
        wave = self.__code(y)
        sign = '.'
        ret = ''
        for i in wave:
            if sign in self.special and i in ['.'] + self.special:
                ret += i
            elif i == sign:
                ret += '.'
            else:
                sign = i
                ret += sign
        return ret

    def record(self):
        """
        将当前db记录至history buffer，用于实现undo逻辑
        """
        self.__redo_list.clear()  # 记录上一步时清空redo列表
        self.__undo_list.append(json.dumps(self.__db))
        while len(self.__undo_list) > self.history_depth:
            self.__undo_list.pop(0)
        # 更新成员状态，通过长度可知是否能undo/redo
        self.undoLen = len(self.__undo_list)
        self.redoLen = len(self.__redo_list)

    def undo(self):
        """
        撤销操作，恢复到之前状态
        :return:
        """
        last = self.__undo_list.pop(-1)
        self.__redo_list.append(json.dumps(self.__db))
        json_db = json.loads(last)
        self.write_all(json_db)
        # 更新成员状态，通过长度可知是否能undo/redo
        self.undoLen = len(self.__undo_list)
        self.redoLen = len(self.__redo_list)

    def redo(self):
        """
        重做上次操作
        :return: None
        """
        last = self.__redo_list.pop(-1)
        self.__undo_list.append(json.dumps(self.__db))
        json_db = json.loads(last)
        self.write_all(json_db)
        # 更新成员状态，通过长度可知是否能undo/redo
        self.undoLen = len(self.__undo_list)
        self.redoLen = len(self.__redo_list)


if __name__ == '__main__':
    wdb = WaveDromDB()
    # print(wdb.colLen)

    # print(wdb.readAll())

    wdb.write(typ='signal', k='wave', y=0, val='xxxxxx=.=xxxxxxx')
    print(wdb.read_all())
