# coding=utf-8
import os
import json
import wavedrom
from PIL import Image
import time
import cairosvg
from WaveDromGen.WaveDromDB import WaveDromDB
from WaveDromGen.WavedromASCII import WavedromASCII


class WaveDromCtrl:
    def __init__(self):
        # 可配置参数
        self.tmpDir = 'tmp/'  # 临时文件夹

        # 外部访问变量, 每次数据改变时更新
        self.__wdb = None  # 底层数据库
        self.__lineChange = []  # 记录数据更改的行索引
        self.imgDB = {}  # 存储分布渲染图片
        self.lastNameLen = 0
        self.stepy = 30
        self.curVal = 0  # 当前操作值

        # 初始化
        self.init()

    def init(self):
        """
        初始化
        :return: None
        """
        if not os.path.isdir(self.tmpDir):
            os.mkdir(self.tmpDir)

        self.__wdb = WaveDromDB()
        self.__render_dispatch(full_render=True)  # 完全渲染
        self.lastNameLen = self.__wdb.nameLen

    def write_wave(self, x, y, val):
        """
        写值到 wave
        :param x: 列索引
        :param y: 行索引
        :param val: 写入值
        :return: None
        """
        # print(self.__wdb.read(typ='signal', k='wave', y=y))
        self.__wdb.write(typ='signal', k='wave', x=x, y=y, val=val)
        # if val in self.__wdb.special:  # 写入为 bus 时，将创建 data
        #     self.write_data(x=x, y=y, val='0')
        # print(self.readAll())
        # print(self.__wdb.read(typ='signal', k='wave', y=y))

    def delay_wave(self, x, y, num=1):
        """
        将波形延迟num拍
        :param x: 行号
        :param y: 列号
        :param num: 延迟拍数,为1时，可以展宽信号，大于1时，信号将整体延迟num
        :return: None
        """
        self.__wdb.record()

        if num == 1:
            self.__wdb.read(typ='signal', k='wave', x=self.get_col_len(), y=y, pop_mode=True)
            self.__wdb.write(typ='signal', k='wave', x=x, y=y, val='.', insert_mode=True)
        else:
            for i in range(num):
                # 弹出最后一个后再插入，确保总长度不变
                self.__wdb.read(typ='signal', k='wave', x=self.get_col_len(), y=y, pop_mode=True)
                self.__wdb.write(typ='signal', k='wave', x=1, y=y, val='.', insert_mode=True)
        self.__lineChange.append(y)
        self.__update()

    def early_wave(self, x, y, num=1):
        """
        将波形延迟num拍
        :param x: 行号
        :param y: 列号
        :param num: 提前拍数,为1时，可以展宽信号，大于1时，信号将整体提前num
        :return: None
        """
        self.__wdb.record()

        if num == 1:
            self.__wdb.write(typ='signal', k='wave', x=self.get_col_len(), y=y, val='.', insert_mode=True)
            line = self.__wdb.read(typ='signal', k='wave', y=y)
            line = line[:x] + line[x + 1:]
            self.__wdb.write(typ='signal', k='wave', y=y, val=line)
        else:
            line = self.__wdb.read(typ='signal', k='wave', y=y)
            for i in range(num):
                line = line[0:1] + line[2:] + '.'
            self.__wdb.write(typ='signal', k='wave', y=y, val=line)
        self.__lineChange.append(y)
        self.__update()

    def write_data(self, x, y, val):
        """
        写入值到 data
        :param x: 列索引
        :param y: 行索引
        :param val: 写入值
        :return: None
        """
        wave = self.__wdb.read(typ='signal', k='wave', y=y)
        try:
            data = self.__wdb.read(typ='signal', k='data', y=y).split(' ')
        except KeyError:
            data = []
        # 找到可设置 data 的索引
        idx = [i for i in range(self.get_col_len()) if wave[i] in self.__wdb.special]
        # 记录 ’=‘ 的数据量
        num = len(idx)
        # 当 ’=‘ 数量不等于 data 时，增加 '0'
        # if not len(data) == num:
        #     data.append('0')
        # 找到 x 前最近的索引
        index = [i for i in range(x, -1, -1) if i in idx]
        if index:  # 当前有 '=' 时，才允许写入
            i = idx.index(index.pop(0))
            # print(self.readAll())
            try:
                data[i] = val
            except IndexError:
                data.append(val)
        # 写回
        self.__wdb.write(typ='signal', k='data', y=y, val=' '.join(data))

    def read_data(self, x, y):
        """
        读取 data
        :param x: 列索引
        :param y: 行索引
        :return: str
        """
        wave = self.__wdb.read(typ='signal', k='wave', y=y)
        data = self.__wdb.read(typ='signal', k='data', y=y).split(' ')
        # 找到可设置 data 的索引
        idx = [i for i in range(self.get_col_len()) if wave[i] in self.__wdb.special]
        # 找到 x 前最近的索引
        idx = idx.index([i for i in range(x, -1, -1) if i in idx].pop(0))
        try:
            return data[idx]
        except IndexError:
            return ''

    def read_wave(self, x, y):
        """
        读取 wave
        :param x: 列索引
        :param y: 行索引
        :return: str
        """
        return self.__wdb.read(typ='signal', k='wave', x=x, y=y)

    def write_name(self, y, val):
        """
        写值到 name
        :param y: 行索引
        :param val: 写入值
        :return: None
        """
        self.__wdb.write(typ='signal', k='name', y=y, val=val)

    def read_name(self, y):
        """
        读取 name
        :param y: 行索引
        :return: None
        """
        return self.__wdb.read(typ='signal', k='name', y=y)

    # 写1个 node值
    def write_node(self, x, y, val):
        """
        写入值到 node
        :param x: 列索引
        :param y: 行索引
        :param val: 写入值
        :return: None
        """
        self.__wdb.write(typ='signal', k='node', y=y, x=x, val=val)

    def read_node(self, y, x=None):
        """
        读取 node
        :param y: 行索引
        :param x: 列索引，为 None 时读取整行
        :return: str
        """
        ret = self.__wdb.read(typ='signal', k='node', y=y, x=x)
        return '' if ret == '.' else ret

    def read_edge(self):
        """
        读取 edge
        :return: str
        """
        return self.__wdb.read(typ='edge')

    def write_edge(self, val):
        """
        写入值到 edge
        :param val: 写入值
        :return: None
        """
        self.__wdb.write(typ='edge', val=val)
        self.__render_dispatch(full_render=True)  # 完全渲染

    def read_all(self):
        """
        读取整个数据库
        :return: dict
        """
        return self.__wdb.read_all()

    def get_col_len(self):
        """
        获取列数
        :return: int
        """
        return self.__wdb.colLen

    def get_row_len(self):
        """
        获取行数
        :return: int
        """
        return self.__wdb.rowLen

    def get_name_len(self):
        """
        获取名字长度
        :return: int
        """
        return self.__wdb.nameLen

    def set_scale_ratio(self, val):
        """
        设置缩放比例值
        :param val: int, 比例数
        :return: None
        """
        self.__wdb.record()

        self.__wdb.write(typ='config', k='hscale', val=val)
        self.__render_dispatch(full_render=True)  # 完全渲染

    def set_skin(self, skin):
        """
        设置波形皮肤
        :param skin: str，皮肤名
        :return: None
        """
        self.__wdb.record()

        self.__wdb.write(typ='config', k='skin', val=skin)
        self.__render_dispatch(full_render=True)  # 完全渲染

    def set_phase(self, y, val):
        """
        设置相位
        :param y: 行索引
        :param val: 设置值
        :return: None
        """
        self.__wdb.record()

        self.__wdb.write(typ='signal', k='phase', y=y, val=val)

    def get_phase(self, y):
        """
        获取相位
        :param y: 行索引
        :return: int
        """
        return self.__wdb.read(typ='signal', k='phase', y=y)

    def set_period(self, y, val):
        """
        设置周期
        :param y: 行索引
        :param val: int 周期值
        :return: None
        """
        self.__wdb.record()
        self.__wdb.write(typ='signal', k='period', y=y, val=val)

    def get_period(self, y):
        """
        获取周期
        :param y: 行索引
        :return: int
        """
        return self.__wdb.read(typ='signal', k='period', y=y)

    def sig_mode(self, x, y, b1_motion=False):
        """
        单比特信号模式，触发时若当前值是0则写入1，若为1则写入0
        :param x: 列索引
        :param y: 行索引
        :param b1_motion: 安装b1拖动，按住b1拖动时将连续写入
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return
        if not b1_motion:
            self.curVal = self.read_wave(x=x, y=y)
        nxt_val = '1' if self.curVal == '0' else '0'

        self.write_wave(x=x, y=y, val=nxt_val)
        self.__lineChange.append(y)
        self.__update()

    def clk_mode(self, x, y):
        """
        时钟模式
        :param x: 行索引
        :param y: 列索引
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return
        cur_val = self.read_wave(x=x, y=y)
        # 值状态切换 p -> P -> n -> N
        if cur_val == 'p':
            self.write_wave(x=x, y=y, val='P')
        elif cur_val == 'P':
            self.write_wave(x=x, y=y, val='n')
        elif cur_val == 'n':
            self.write_wave(x=x, y=y, val='N')
        elif cur_val == 'N':
            self.write_wave(x=x, y=y, val='p')
        else:
            self.write_wave(x=x, y=y, val='p')

        # 当前行所有点都将变为 ‘.’
        for i in range(x + 1, self.__wdb.colLen):
            self.write_wave(x=i, y=y, val='.')

        self.__lineChange.append(y)
        self.__update()

    def bus_mode(self, x, y, val='='):
        """
        总线模式(多比特信号)
        :param 列索引:
        :param 行索引:
        :param 写入值:
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return

        cur_val = self.read_wave(x=x, y=y)
        self.write_wave(x=x, y=y, val='.' if cur_val == val else val)

        self.__lineChange.append(y)
        self.__update()

    def x_mode(self, x, y):
        """
        x模式处（产生不定态）
        :param x: 列索引
        :param y: 行索引
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return

        # preVal = self.__forwardQuery(x=x, y=y, val='x')
        cur_val = self.read_wave(x=x, y=y)
        self.write_wave(x=x, y=y, val='.' if cur_val == 'x' else 'x')

        self.__lineChange.append(y)
        self.__update()

    def z_mode(self, x, y):
        """
        z模式处（产生高阻态）
        :param x: 列索引
        :param y: 行索引
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return

        # preVal = self.__forwardQuery(x=x, y=y, val='x')
        cur_val = self.read_wave(x=x, y=y)
        self.write_wave(x=x, y=y, val='.' if cur_val == 'z' else 'z')

        self.__lineChange.append(y)
        self.__update()

    def gap_mode(self, x, y):
        """
        gap模式处(插入|)
        :param x: 行索引
        :param y: 列索引
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return

        # preVal = self.__forwardQuery(x=x, y=y, val='|')
        cur_val = self.read_wave(x=x, y=y)
        self.write_wave(x=x, y=y, val='.' if cur_val == '|' else '|')

        self.__lineChange.append(y)
        self.__update()

    def t_mode(self, x, y, val, node_mode=None):
        """
        文本模式
        :param x: 列索引
        :param y: 行索引
        :param val: 写入值
        :param node_mode: 节点模式，写入值为 node
        :return: None
        """
        self.__wdb.record()

        if x == -1:  # 编辑名字
            self.write_name(y=y, val=val)
        elif node_mode:  # edit node
            self.write_node(x=x, y=y, val=val)
        else:  # 编辑数据
            self.write_data(x=x, y=y, val=val)

        # 当信号名长度变化超过2时，全内容重新渲染
        if abs(self.__wdb.nameLen - self.lastNameLen) > 0:
            self.__lineChange.append((0, self.__wdb.rowLen))
            self.lastNameLen = self.__wdb.nameLen
        else:
            self.__lineChange.append(y)
        self.__update()

    def add_row(self, num):
        """
        在行尾增加行
        :param num: 增加行数
        :return: None
        """
        self.__wdb.record()

        row_len = self.get_row_len()
        self.__wdb.insert_row(num=num)
        self.__lineChange.append((row_len, row_len + num))
        self.__update()

    def add_col(self, num):
        """
        在列尾增加列
        :param num: 增加列数
        :return: None
        """
        self.__wdb.record()

        self.__wdb.insert_col(num=num)
        self.__render_dispatch(full_render=True)
        self.__update()

    def del_row(self, y):
        """
        删除指定行
        :param y: 指定行索引
        :return: None
        """
        self.__wdb.record()

        self.__wdb.del_row(typ='signal', y=y)
        self.__render_dispatch(full_render=True)
        self.__update()

    def del_col(self, x):
        """
        删除指定列
        :param x: 列索引
        :return: None
        """
        self.__wdb.record()

        self.__wdb.del_col(typ='signal', x=x)
        self.__render_dispatch(full_render=True)
        self.__update()

    def swap_line(self, src, dst):
        """
        将 src 行与 dst 行交换
        :param src: source 行索引
        :param dst: destination 行索引
        :return: None
        """
        self.__wdb.record()
        self.__wdb.swap_line(typ='signal', src=src, dst=dst)
        self.__lineChange = range(min(src, dst), max(src, dst) + 1)
        self.__update()

    def copy_line(self, src, dst):
        """
        复制行，将 src 行内容复制到 dst 位置
        :param src: source 行
        :param dst: destination 行
        :return: None
        """
        self.__wdb.record()
        self.__wdb.swap_line(typ='signal', src=src, dst=dst, copy_mode=True)
        self.__render_dispatch(full_render=True)
        self.__update()

    def clear(self, y):
        """
        清除指定行所有数据，不删除行
        :param y: 行索引
        :return: None
        """
        self.__wdb.record()

        # 当清除行信号名称为最大name_len时，进行全局渲染
        name_len = len(self.read_name(y))

        val = '.' * self.__wdb.colLen
        self.__wdb.write(typ='signal', k='name', y=y, val='')
        self.__wdb.write(typ='signal', k='data', y=y, val='')
        self.__wdb.write(typ='signal', k='node', y=y, val=val)
        self.__wdb.write(typ='signal', k='wave', y=y, val=val)

        if name_len > self.get_name_len():
            self.__render_dispatch(full_render=True)
        else:
            self.__lineChange.append(y)
        self.__update()

    def __update(self):
        """
        若有行更新，将调用渲染器渲染图片
        :return:
        """
        if len(self.__lineChange) > 0:
            self.__render_dispatch()

    def save(self, handle):
        """
        保存
        :param handle: 文件句柄，根据句柄后缀决定保存类型
        :return: None
        """
        out = self.__wdb.read_all()
        fname = handle.name
        if fname.endswith('.png'):
            fname = fname.rstrip('.png')
            self.__render(dic=self.read_all(), fname=fname)
            os.remove(fname + '.svg')
        elif fname.endswith('.svg'):
            fname = fname.rstrip('.svg')
            self.__render(dic=self.read_all(), fname=fname)
            os.remove(fname + '.png')
        else:
            json.dump(out, handle)
        handle.close()

    def restore(self, filename):
        """
        恢复数据
        :param filename: 存档文件位置
        :return: None
        """
        f = open(filename)
        db = json.load(f)
        self.init()
        self.__wdb.write_all(db)
        self.__render_dispatch(full_render=True)
        self.__update()

    def restore_json(self, json_db):
        """
        将 json db 渲染为波形，由编辑器调用，实现文本编辑后渲染
        :param json_db: 波形 dict
        :return: None
        """
        self.init()
        self.__wdb.write_all(json_db)
        self.__render_dispatch(full_render=True)
        self.__update()

    def renderLine(self, lineList):
        """
        渲染指定行，供外部调用
        :param lineList: list，待渲染行索引
        :return: None
        """
        self.__lineChange = lineList
        self.__update()

    def __render(self, dic, fname):
        """
        渲染器，pywavedrom 生成 svg 文件后，使用 cairosvg 转换为 png
        :param dic: wavedrom dict
        :param fname: 生成文件名
        :return: None
        """
        svg = str(dic)
        wavedrom.render(svg).saveas(fname + ".svg")
        # print(svg)
        # convert svg to png
        from_img = fname + ".svg"
        to_img = fname + '.png'
        cairosvg.svg2png(url=from_img, write_to=to_img)

    # 渲染分配器，分割数据，无更新内容的将不渲染
    # fullRender: 全局渲染，从头至尾都渲染
    def __render_dispatch(self, full_render=False):
        """
        渲染分配，根据列表 __lineChange 记录数据渲染图片，支持3种模式：
            完全渲染：渲染所有行内容
            合并渲染：待渲染行为连续行时（__lineChange 内容为 tuple），将把待渲染行一并渲染
            单独渲染：待渲染行为单独行时（__lineChange 内容为 int），将单独渲染一行
        渲染完成后结果保存至 self.imgDB
        :param full_render: bool，True时将进入完全渲染模式
        :return: None
        """
        st = time.time()
        self.imgDB.clear()
        array = self.read_all()['signal']
        # 渲染时为防止不同长度信号名影响渲染结果，将在行首插入dummy行，待imgSplit分割后删除dummy行
        dummy = {"name": ("Q" * self.__wdb.nameLen)}
        if full_render:  # 完全渲染
            db = self.read_all()
            wave = db['signal'].copy()  # 重新映射句柄
            wave.append(dummy)
            db['signal'] = wave

            fname = self.tmpDir + 'tmp0'
            self.__render(dic=db, fname=fname)  # 执行渲染
            sub_img_list = self.__img_split(fname + '.png')  # 分割图片
            sub_img_list.pop(-1)  # 删除 dummy 行
            for sub_idx in range(self.get_row_len()):
                self.imgDB[sub_idx] = sub_img_list.pop(0)
        else:
            for i in self.__lineChange:
                if type(i) == tuple:  # 合并渲染
                    # 多行合并渲染时 i 是元组，如（1，10）分别代表开始行和结束行
                    start_idx = i[0]
                    end_idx = i[1]
                    db = self.read_all()
                    db['signal'] = array[start_idx:end_idx] + [dummy]
                    fname = self.tmpDir + 'tmp%s' % start_idx

                    self.__render(dic=db, fname=fname)  # 执行渲染
                    sub_img_list = self.__img_split(fname + '.png')  # 分割图片
                    sub_img_list.pop(-1)  # 删除 dummy 行
                    for sub_idx in range(start_idx, end_idx):
                        self.imgDB[sub_idx] = sub_img_list.pop(0)
                else:  # 单独渲染
                    # 单行渲染时 i 是数字，如 1 代表当前渲染行
                    db = self.read_all()
                    db['signal'] = [array[i], dummy]
                    fname = self.tmpDir + 'tmp%s' % i
                    self.__render(dic=db, fname=fname)  # 执行渲染
                    sub_img_list = self.__img_split(fname + '.png')  # 分割图片
                    sub_img_list.pop(-1)  # 删除 dummy 行
                    self.imgDB[i] = sub_img_list.pop(0)

        print('操作行', self.__lineChange, '; 渲染时间 %.2fs' % (time.time() - st))
        self.__lineChange = []

    def __img_split(self, fname):
        """
        图片分割，将渲染完成的图片分割为单独1行图片
        :param fname: 输入文件名
        :return: list
        """
        ret = []
        img = Image.open(fname)
        width, height = img.size
        for i in range(height // self.stepy):  # 根据图片高度和 step 高分割图片
            cropped = img.crop((0, i * self.stepy, width, (i + 1) * self.stepy))  # (left, upper, right, lower)
            ret.append(cropped.copy())
        return ret

    def undo(self):
        """
        撤销
        :return: None
        """
        self.__wdb.undo()
        self.__render_dispatch(full_render=True)
        self.__update()

    def redo(self):
        """
        重做
        :return: None
        """
        self.__wdb.redo()
        self.__render_dispatch(full_render=True)
        self.__update()

    def get_history_len(self):
        """
        获取undo/redo列表长度
        :return:tuple，（undo列表长度，redo列表长度）
        """
        return self.__wdb.undoLen, self.__wdb.redoLen

    def to_ascii(self):
        """
        将波形图转化为 ascii字符
        :return: str
        """
        wave = self.read_all()
        return WavedromASCII.from_dict(wave)


if __name__ == '__main__':
    wdc = WaveDromCtrl()
    ret = wdc.to_ascii()
