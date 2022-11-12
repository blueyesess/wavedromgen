![logo](asset/md/logo.png "logo")
### WaveDromGen是什么？

WaveDromGen 基于 [wavedrom](https://wavedrom.com) 开发的图形化时序绘图工具，相比 wavedrom 代码式画图，WaveDromGen **所见即所得**，更适合绘制、调整复杂的时序图。

### 支持特性
- 图像化绘图，代码绘图、ascii图
- 绘制 wavedrom 支持内容，输出 json 与 wavedrom 相同
- 支持数据保存（json，svg，png）和读取（json）

### 目录架构
```commandline
│  main.py                  main 函数入口
│  package2exe.py           打包文件，将代码转换为 exe
├─asset                     图片素材
└─WaveDromGen
        language.py         ui 语言字典
        WavedromASCII.py    wavedrom 生成 ascii 波形
        WaveDromCtrl.py     控制模块
        WaveDromDB.py       模型模块
        WaveDromUI.py       ui 顶层
        WaveImageDB.py      将图标转二进制码后写入此文件，便于打包 exe
        WaveNote.py         代码块编辑模块
        __init__.py
```
![软件架构](asset/md/struct.png "软件架构")

### 使用方法
- 方法 1：[下载发行版](https://gitee.com/sjkpy/WaveDromGen/releases)（仅支持windows版），点击.exe运行
- 方法 2：下载 python 源码：
- 1. git clone https://gitee.com/sjkpy/WaveDromGen.git
  2. pip install -r requirement
  3. run main.py

### 界面说明
#### 绘图器
![ui](asset/md/ui.png "ui")

1. 菜单栏，基本编辑功能
2. 视图模式：
	- 绘图器：点击波形绘图
	- 编辑器：使用代码进行绘图
	- 字符图：不可编辑，实时将波形准换为ascii图
3. 绘图器工具栏，从上至下依次为：
	- **clk：时钟**，点击后在波形区点击任意位置，将产生时钟波形，再次点击相同位置将改变值，值为依次为正时钟 -> 上升沿 -> 负时钟 -> 下降沿；
    - **sig：单比特信号**，点击后在波形区点击任意位置，将产生0电平，再次点击相同位置将改变值为1;
    - **bus：总线信号**，点击后在波形区点击任意位置，将产生总线标识，再次点击相同位置将恢复；
    - **x：不定态**，点击后在波形区点击任意位置，将产生不定标识，再次点击相同位置将恢复；
    - **z：高阻态**，点击后在波形区点击任意位置，将产生高阻标识，再次点击相同位置将恢复；
    - **sel：选择**，点击后在波形区点击无波形区域，将增加行列数；上下拖动波形将调整波形位置；上下拖动波形时按住 ctrl 将复制对应波形；左右拖动波形将横向移动波形；
    - **t：文本框**，点击后在波形区点击信号名或总线标识，可修改对应名称；
    - **clr：清除**，点击后在波形区点击信号，将清除信号数据；
4. 状态栏

#### 编辑器

![ui2](asset/md/ui2.png "ui2")

1. 编辑器工具栏，从左至右依次为：
   - **渲染：** 将编辑器内容渲染为波形图；
   - **复制：** 复制选中内容；
   - **粘贴：** 粘贴复制内容；
   - **撤销**；撤销上一步操作；
   - **重做**；重做撤销操作；
   - **搜索**；搜索关键字
2. **编辑区：** 编辑波形代码，语法遵循 [wavedrom](https://wavedrom.com/tutorial.html) 定义

### 演示
![demo](asset/md/demo.gif "demo")


### 捐赠
如果WaveDromGen有帮助到你，可以请我喝杯咖啡哦~

![pay](asset/md/pay.png "pay")


