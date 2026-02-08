"""
客户端程序，包含了：
+ 自定义的UI组件
+ 各个界面的pygame func
+ 双线程设计
"""
# pylint: disable=W0221
# pylint: disable=R0903
# pylint: disable=W0603
# pylint: disable=W0718
# 抑制警告：
# + W0221:覆写方法与原方法参数数量不统一/出现不必要的可变参数。
# + R0903:类的公共方法太少(小于2)。
# + W0603:使用了global关键字，pylint不鼓励使用任何的global关键字以在函数内部更改全局变量。
# + W0718:过于宽松的except异常捕获。

# TODO: interface with server

import socket
import sys
from dataclasses import dataclass
from typing import Tuple, Callable, Any, Optional, List
from abc import ABCMeta, abstractmethod
from time import sleep
from collections import deque
from datetime import datetime
import asyncio
import os
import pygame
# -*- encoding: utf-8 -*-
ID = 0
CARD_QUEUE : List[Optional[Tuple[int, int]]]= []

# 运行路径初始化
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(application_path)

def logger(msg : str, t : str = "INFO", thread : str = "main", pipe : str = "file"):
    """
    客户端日志接口

    :param msg: 消息内容
    :type msg: str
    :param t: 消息等级(规定为INFO, TRACE, WARN, ERROR四种等级)
    :type t: str
    :param thread: 日志线程
    :type thread: str
    :param pipe: 日志输出管道(规定为cmd, file两种)
    :type pipe: str
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if pipe == "cmd":
        print(timestamp + f" [{thread}] {t} {msg}")
    elif pipe == "file":
        with open("client.log", "a") as f:
            if msg == "":
                f.write("\n")
            else:
                f.write(timestamp + f" [{thread}] {t} {msg}\n")

# 数据描述类
@dataclass
class Coord:
    """
    坐标描述类
    """
    x : float
    y : float

@dataclass
class Size:
    """
    尺寸描述类
    """
    length : float
    width : float

@dataclass
class Color:
    """
    颜色描述类
    """
    r : int
    g : int
    b : int
    def __iter__(self):
        return iter([self.r, self.g, self.b])

@dataclass
class Text:
    """
    基础文本描述类
    """
    text : str
    font : str|None
    size : int
    color : Color = Color(0, 0, 0)

@dataclass
class Border:
    """
    边框数据描述类
    """
    color : Color
    width : int

# UI组件
class DisplayArea(metaclass = ABCMeta):
    """
    UI显示组件抽象类
    """
    _content : Any = None
    _frame : pygame.Rect
    _displayed : bool = False

    @abstractmethod
    def _display(self, surface : pygame.Surface) -> None:...

    def run(self, surface : pygame.Surface) -> None:
        """
        在surface上启用显示组件

        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        self._display(surface)
        if not self._displayed:
            pygame.display.flip()
            self._displayed = True

class Board(DisplayArea):
    """
    自定义Board类
    """
    def __init__(self,
                 rect : pygame.Rect,
                 color : Color,
                 apparency : int,
                 border : Border
                 ):
        """
        基于pygame.Rect的背景板组件

        :param rect: 组件框架
        :type rect: pygame.Rect
        :param color: 颜色
        :type color: Tuple[int, int, int]
        :param apparency: 透明度
        :type apparency: int
        :param border: 边框数据包
        :type border: Border
        """
        self._frame = rect
        self.color = tuple(color)
        self.apparency = apparency
        self.border_width = border.width
        self.border_color = tuple(border.color)

    def _display(self, surface: pygame.Surface) -> None:
        """
        从属于self.run，用来显示背景板组件

        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        temp_surf = pygame.Surface((self._frame.width, self._frame.height), pygame.SRCALPHA)
        r, g, b = self.color
        temp_surf.fill((r, g, b, self.apparency))
        surface.blit(temp_surf, self._frame.topleft)
        if self.border_width != 0:
            pygame.draw.rect(surface, self.border_color, self._frame, self.border_width)

class Label(DisplayArea):
    """
    自定义组件Label类
    """
    def __init__(self,
                 text : pygame.Surface,
                 text_area : pygame.Rect,
                 bg_apparent : bool,
                 bg_color : Tuple[int, int, int],
                 border : Border
                 ):
        """
        基于pygame.Rect与pygame.font.Font的文本显示组件

        :param text: 文本对象
        :type text: pygame.Surface
        :param text_area: 文本区域对象
        :type text_area: pygame.Rect
        :param bg_apparent: 背景透明化
        :type bg_apparent: bool
        :param bg_color: 背景颜色
        :type bg_color: Tuple[int, int, int]
        :param border: 边框数据包
        :type border: Border
        """
        self._content : pygame.Surface = text
        self._frame = text_area
        self.bg_apparent = bg_apparent
        self.bg_color = bg_color
        self.border_width = border.width
        self.border_color = tuple(border.color)

    def _display(self, surface: pygame.Surface) -> None:
        """
        从属于self.run，用来显示文本组件

        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        if not self.bg_apparent:
            pygame.draw.rect(surface, self.bg_color, self._frame)
        if self.border_width != 0:
            pygame.draw.rect(surface, self.border_color, self._frame, self.border_width)
        surface.blit(self._content,
                     (
                         self._frame.centerx - self._content.get_width() // 2,
                         self._frame.centery - self._content.get_height() // 2
                     ))

# UI组件工厂
class DisplayAreaFactory(metaclass = ABCMeta):
    """
    基于pygame传统组件的自定义显示组件工厂抽象类
    """
    _instance = None

    def __new__(cls, *_args, **_kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @abstractmethod
    def construct(self, *args, **kwargs):
        """抽象构造方法，用于构建组件
        Returns:
            DisplayArea: 返回构建好的UI组件
        """
        return

class BoardFactory(DisplayAreaFactory):
    """
    自定义组件Board的工厂类
    """
    def construct(self,
                  start_pos : Coord,
                  size : Size,
                  color : Color,
                  apparency : int = 256,
                  border : Border = Border(Color(0,0,0),1)
                  ) -> Board:
        """
        构建一个Board对象
        预处理相关零散数据，包装为Board初始化所需的参数

        :param start_pos: Board左上角像素坐标
        :type start_pos: Tuple[float, float]
        :param size: Board的长和宽
        :type size: Tuple[float, float]
        :param color: Board颜色
        :type color: Tuple[int, int, int]
        :param apparency: Board透明度(0-256)
        :type apparency: int
        :param border: 边框数据包
        :type border: Border
        :return: Board对象
        :rtype: Board
        """
        board_rect = pygame.Rect(start_pos.x, start_pos.y, size.length, size.width)
        return Board(board_rect, color, apparency, border)

class LabelFactory(DisplayAreaFactory):
    """
    自定义组件Label的工厂类
    """
    def construct(self,
                 text : Text,
                 start_pos : Tuple[float, float],
                 size : Tuple[float, float],
                 bg_apparent : bool = False,
                 bg_color : Tuple[int, int, int] = (255, 255, 255),
                 border : Border = Border(Color(255, 255, 255), 0),
                 antialias : bool = True #启用字体平滑
                 ) -> Label:
        """
        构建一个Label对象
        预处理相关零散数据，包装为Label初始化所需的参数

        :param text: Text数据包
        :type text: str
        :param start_pos: Label左上角像素坐标
        :type start_pos: Tuple[float, float]
        :param size: Label的长和宽
        :type size: Tuple[float, float]
        :param bg_apparent: Label背景透明化
        :type bg_apparent: bool
        :param bg_color: Label背景颜色
        :type bg_color: Tuple[int, int, int]
        :param border: 边框数据包
        :type border: Border
        :param antialias: Label文本字体平滑
        :type antialias: bool
        :return: Label对象
        :rtype: Label
        """
        text_rect = pygame.Rect(start_pos[0], start_pos[1], size[0], size[1])
        text_obj = pygame.font.Font(text.font, text.size)
        text_surface = text_obj.render(text.text, antialias, tuple(text.color))
        return Label(text_surface, text_rect, bg_apparent, bg_color, border)

# UI控件
class InteractorArea(metaclass = ABCMeta):
    """
    UI交互控件抽象类
    """
    _frame = None
    _content = None
    _func = None
    _displayed : bool = False
    _surface : Optional[pygame.Surface] = None

    @abstractmethod
    def _display(self, surface : pygame.Surface) -> None:...

    @abstractmethod
    def _events(self, event : pygame.event.Event) -> int:...

    def _handle(self) -> int:
        """
        从属于self.run，用self._events来处理交互事件
        规定若无匹配事件，需返回0以continue

        :return: 返回状态值
        :rtype: int
        """
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return -1
                res = self._events(event)
                if res == 0:
                    continue
                return res

    def run(self, surface : pygame.Surface) -> None:
        """
        在surface上启用交互组件，是self._display与self._handle的联合体

        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        global RUNNING
        self._display(surface)
        if not self._displayed:
            pygame.display.flip()
            self._displayed = True
        if self._handle() == -1:
            RUNNING = False

    def bind(self, job : Callable[["InteractorArea"], None]) -> None:
        """
        将组件与Func绑定
        规定func为有self类型参数无返回值类型

        :param job: 绑定的方法
        :type job: Callable[["InteractorArea"], None]
        """
        self._func = job

class Button(InteractorArea):
    """
    自定义控件Button类
    """
    def __init__(self,
                 button_rect : pygame.Rect,
                 button_color : Tuple[int, int, int],
                 border : Border,
                 text : pygame.Surface|None
                 ):
        """
        创建一个基于pygame.rect和pygame.text的按钮
        这个按钮本质为基于pygame.rect检测交互并执行行为的ui容器

        :param button_rect: 按钮容器(规定为矩形容器pygame.Rect)
        :type button_rect: pygame.Rect
        :param button_color: 按钮颜色RGB
        :type button_color: Tuple[int, int, int]
        :param border: 边框数据包
        :type border: Border
        :param text: 按钮内文本对象(可设置为无)
        :type text: pygame.Surface | None
        """
        self._frame = button_rect
        self.color = button_color
        self.border_width = border.width
        self.border_color = tuple(border.color)
        self._content = text
        self._func = None

    def _events(self, event: pygame.event.Event):
        """
        从属于_handle，用于自定义对单一特定交互事件的处理

        :param event: 本次处理的事件
        :type event: pygame.event
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._frame.collidepoint(event.pos) and self._func:
                self._func(self)
                return 1
        return 0

    def _display(self, surface : pygame.Surface) -> None:
        """
        从属于self.run，用来显示按钮

        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        pygame.draw.rect(surface, self.color, self._frame)
        if self.border_width != 0:
            pygame.draw.rect(surface, self.border_color, self._frame, self.border_width)
        if self._content is not None:
            surface.blit(self._content,
                         (self._frame.centerx - self._content.get_width() // 2,
                          self._frame.centery - self._content.get_height() // 2)
                         )

class CardImageObject(InteractorArea):
    """
    增强版图片交互对象（整合了test.py的CardImageObject功能）
    """
    def __init__(self,
                 image: pygame.Surface,
                 id: Tuple[int, int],
                 pos: Coord
                 ):
        """
        创建增强版图片交互对象

        :param image: 图片对象
        :type image: pygame.Surface
        :param id: 卡牌ID（花色，点数）
        :type id: Tuple[int, int]
        :param pos: 初始位置
        :type pos: Coord
        """
        self._content = image
        self._frame = image.get_rect()
        self._func = None
        self._pos = pos
        self._frame.left = int(pos.x)
        self._frame.top = int(pos.y)
        self._id = id
        self._choosen: bool = False
        self._move_up_next: bool = True  # 交替移动方向

    def _events(self, event: pygame.event.Event):
        """
        处理交互事件

        :param event: 本次处理的事件
        :type event: pygame.event
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._frame.collidepoint(event.pos) and self._func:
                self._func(self)
                self._choosen = not self._choosen
                return 1
        return 0

    def _display(self, surface: pygame.Surface) -> None:
        # 绘制图像
        surface.blit(self._content, (self._frame.x, self._frame.y))

    @property
    def id(self) -> Tuple[int, int]:
        return self._id
            
    def movetoCoord(self, coord: Coord) -> None:
        """
        移动到指定坐标
        """
        self._frame.x = int(coord.x)
        self._frame.y = int(coord.y)
        self._pos = coord
        
        if self._surface:
            self._display(self._surface)
            pygame.display.update(self._frame)
    
    def movetowards(self, direc: str, dis: float) -> None:
        """
        向指定方向移动
        
        :param direc: 方向('u'为向上, 'd'为向下, 'l'为向左, 'r'为向右)
        :type direc: str
        :param dis: 移动距离
        :type dis: float
        """
        old_rect = self._frame.copy()
        
        match direc:
            case 'u':
                self._frame.move_ip(0, -dis)
            case 'd':
                self._frame.move_ip(0, dis)
            case 'l':
                self._frame.move_ip(-dis, 0)
            case 'r':
                self._frame.move_ip(dis, 0)
            case _:
                return
        
        self._pos = Coord(self._frame.x, self._frame.y)
        
        if self._surface:
            # 清除旧位置
            pygame.draw.rect(self._surface, (255, 255, 255), old_rect)
            # 绘制新位置
            self._display(self._surface)
            # 更新显示区域
            pygame.display.update([old_rect, self._frame])
    
    def move_alternating(self, dis: float) -> None:
        """
        交替移动：第一次向上，第二次向下，以此类推
        
        :param dis: 移动距离
        :type dis: float
        """
        if self._move_up_next:
            self.movetowards('u', dis)
            logger(f"ID {self._id}: 向上移动", t="TRACE", thread="CardImageObject")
        else:
            self.movetowards('d', dis)
            logger(f"ID {self._id}: 向下移动", t="TRACE", thread="CardImageObject")
        
        # 切换下一次的方向
        self._move_up_next = not self._move_up_next
    
    @property
    def ischoosen(self) -> bool:
        return self._choosen
    
    def get_position(self) -> Coord:
        """
        获取当前坐标
        """
        return Coord(self._frame.x, self._frame.y)

# UI控件工厂
class InteractorAreaFactory(metaclass = ABCMeta):
    """
    基于pygame传统组件的自定义交互组件工厂抽象类
    """
    _instance = None

    def __new__(cls, *_args, **_kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @abstractmethod
    def construct(self, *_args, **_kwargs):
        """
        构建InteractorArea组件
        """
        return

class ButtonFactory(InteractorAreaFactory):
    """
    自定义组件Button的工厂类
    """
    def construct(self,
                  start_pos : Tuple[float, float],
                  size : Tuple[float, float],
                  text : Text = Text("", None, 18),
                  button_color : Tuple[int, int, int] = (255, 255, 255),
                  border : Border = Border(Color(0, 0, 0), 0),
                  antialias : bool = True #启用字体平滑
                  ) -> Button:
        """
        构建一个Button对象
        预处理相关零散数据，包装为Button初始化所需的参数

        :param start_pos: Button左上角像素坐标
        :type start_pos: Tuple[float, float]
        :param size: Button的长和宽
        :type size: Tuple[float, float]
        :param text: Text数据包
        :type text: Text
        :param button_color: Button的颜色
        :type button_color: Tuple[int, int, int]
        :param border: 边框数据包
        :type border: Border
        :param antialias: Button文本平滑
        :type antialias: bool
        :return: Button对象
        :rtype: Button
        """
        button_rect = pygame.Rect(start_pos[0], start_pos[1], size[0], size[1])
        if text is None:
            return Button(button_rect, button_color, border, None)
        text_obj = pygame.font.Font(text.font, text.size)
        button_text = text_obj.render(text.text, antialias, tuple(text.color))
        return Button(button_rect, button_color, border, button_text)

class CardImageObjectFactory(InteractorAreaFactory):
    """
    增强版CardImageObject的工厂类
    """
    def construct(self,
                  type: Tuple[int, int],
                  start_pos: Coord,
                  ) -> Optional[CardImageObject]:
        """
        构建组件CardImageObject

        :param type: 卡牌类型（花色，点数）
        :type type: Tuple[int, int]
        :param start_pos: 图片左上角坐标
        :type start_pos: Coord
        :return: CardImageObject对象或空(如果type非法)
        :rtype: Optional[CardImageObject]
        """
        # 根据花色确定图片文件名
        match type[0]:
            case 0:
                src = "heart_"
            case 1:
                src = "spade_"
            case 2:
                src = "club_"
            case 3:
                src = "diamond_"
            case _:
                return None
        
        # 构建图片路径
        image_path = os.path.join("src", "cards", f"{src}{type[1]}.png")
        
        try:
            image = pygame.image.load(image_path)
            # 缩放图像到合适大小
            image = pygame.transform.scale(image, (80, 120))
            return CardImageObject(image, type, start_pos)
        except pygame.error as e:
            logger(f"加载图片失败: {e}", t="ERROR", thread="CardImageObjectFactory")
            logger(f"尝试加载的路径: {os.path.abspath(image_path)}", t="TRACE", thread="CardImageObjectFactory")
            # 创建替代图像（红色背景白色边框）
            image = pygame.Surface((80, 120))
            image.fill((255, 0, 0))
            pygame.draw.rect(image, (255, 255, 255), (5, 5, 70, 110), 2)
            return CardImageObject(image, type, start_pos)

# UI界面设计
def welcome_screen(surface: pygame.Surface, sk_main : "SocketMain") -> None:
    """
    欢迎界面

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    """
    global RUNNING, UI_MAIN, FRENDERWELCOME
    
    if FRENDERWELCOME:
        logger("Rendering welcome_screen.", t = "TRACE", thread = "welcome_screen/self._surfunc")
        FRENDERWELCOME = False
        
    def start_buttons_job(button : InteractorArea):
        """
        start_button绑定的方法
        """
        asyncio.create_task(sk_main.send("1")) # -> server.server._client_run
        UI_MAIN.switch_surfunc(waiting_screen)

    welcome_bg = pygame.image.load("src\\bg\\welcome_bg.jpg")

    surface.blit(welcome_bg, (0, 0))
    start_board = BOARDFACTORY.construct(Coord(360, 150),
                                         Size(560, 420),
                                         Color(255, 255, 255),
                                         apparency = 240,
                                         border = Border(
                                             Color(0, 0, 0),
                                             0
                                             )
                                         )
    start_board.run(surface)

    start_text = LABELFACTORY.construct(Text("斗地主",
                                             "src\\fonts\\No.400-ShangShouZhaoPaiTi-2.ttf",
                                             70
                                             ),
                                       (400, 200),
                                       (480, 120),
                                       bg_apparent = True
                                       )
    start_text.run(surface)

    start_button = BUTTONFACTORY.construct((520, 360),
                                           (240, 60),
                                           Text("开始",
                                                "src\\fonts\\MicrosoftYaHei.ttf",
                                                18
                                                ),
                                           border = Border(Color(0, 0, 0), 1)
                                           )
    start_button.bind(start_buttons_job)
    start_button.run(surface)
    
    # pygame.display.flip()

def waiting_screen(surface : pygame.Surface, sk_main: "SocketMain") -> None:
    """
    等待连接界面

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    """
    global UI_MAIN, RUNNING, FRENDERWAITING
    if FRENDERWAITING:
        logger("Rendering waiting_screen.", t = "TRACE", thread = "waiting_screen/self._surfunc")
        FRENDERWAITING = False
    
    waiting_bg = pygame.image.load("src\\bg\\welcome_bg.jpg")
    surface.blit(waiting_bg, (0, 0))
    
    waiting_board = BOARDFACTORY.construct(Coord(360, 150),
                                           Size(560, 420),
                                           Color(255, 255, 255),
                                           apparency = 240,
                                           border = Border(
                                               Color(0,0,0),
                                               0
                                               )
                                           )
    waiting_board.run(surface)

    waiting_text = LABELFACTORY.construct(Text("等待其他玩家...",
                                               "src\\fonts\\MicrosoftYaHei.ttf",
                                               70
                                               ),
                                          (400, 200),
                                          (480, 120),
                                          bg_apparent = True,
                                          border = Border(Color(255, 255, 255), 1)
                                          )
    waiting_text.run(surface)

def game_screen(surface: pygame.Surface, sk_main : "SocketMain") -> None:
    """
    游戏界面 待添加

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    """
    
    global UI_MAIN, RUNNING, CARD_QUEUE
    logger("Rendering game_screen.", t = "TRACE", thread = "game_screen/self._surfunc")
    
    game_bg = pygame.image.load("src\\bg\\game_bg.jpg")
    surface.blit(game_bg, (0, 0))
    
    while not CARD_QUEUE:
        waiting_text = LABELFACTORY.construct(
            Text("等待发牌...", "src\\fonts\\MicrosoftYaHei.ttf", 36),
            (500, 300),
            (280, 50),
            bg_apparent=True
        )
        waiting_text.run(surface)
        return
 
# 客户端主程序
TESTADDR = ("127.0.0.1", 8888)
WELCOMEFLAG = True
GAMEFLAG = False
RUNNING = True    # 程序运行标识
SOCKETRUNNING = True
FRENDERWELCOME = True
FRENDERWAITING = True
BUTTONFACTORY = ButtonFactory()
LABELFACTORY = LabelFactory()
BOARDFACTORY = BoardFactory()
CardImageObjectFACTORY = CardImageObjectFactory()

class UIMain():
    """
    存有线程ui_thread负责的ui主程序，主管ui绘制
    """
    _screen : pygame.Surface
    def __init__(self, start_surfunc : Callable[[pygame.Surface, "SocketMain"], None]):
        """
        用一个界面方法初始化一个UIMain对象

        :param start_surfunc: 初始界面((pygame.Surface) -> None)
        :type start_surfunc: Callable[[pygame.Surface], None]
        """
        self._surfunc : Callable[[pygame.Surface, SocketMain], None] = start_surfunc

    def switch_surfunc(self, new_surfunc : Callable[[pygame.Surface, "SocketMain"], None]) -> None:
        """
        切换界面方法

        :param new_surfunc: 新的界面((pygame.Surface) -> None)
        :type new_surfunc: Callable[[pygame.Surface], None]
        """
        self._screen.fill((255, 255, 255))
        pygame.display.flip()
        self._surfunc : Callable[[pygame.Surface, SocketMain], None] = new_surfunc

    async def _run(self) -> None:
        """
        UIMain主要运行逻辑

        """
        global RUNNING, SOCKET_MAIN

        pygame.font.init()
        pygame.init()
        self._screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("斗地主")
        clock = pygame.time.Clock()
        self._screen.fill((255, 255, 255))
        logger("Entering render loop", thread = "UI_MAIN")
        try:
            while RUNNING:
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        RUNNING = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            RUNNING = False
                    # 可选：处理窗口大小变化等其他事件

                if not pygame.display.get_init():
                    RUNNING = False

                # ui 绘制 start
                if self._surfunc and SOCKET_MAIN:
                    self._surfunc(self._screen, SOCKET_MAIN)
                # ui 绘制 end

                await asyncio.sleep(0)
                clock.tick(60)

        except KeyboardInterrupt as e:
            print(f"程序异常: {e}")
        finally:
            # 确保资源被正确释放
            pygame.quit()

    async def start(self) -> None:
        """
        转入self._run运行

        """
        logger("UI starts", t = "INFO", thread = "UI_MAIN")
        await self._run()

class SocketMain():
    """
    线程socket_thread负责的socket主程序，负责与server交换数据
    """
    id = "0"
    def __init__(self, addr : Tuple[str, int]):
        self._addr = addr
        self._listenmsg = asyncio.Queue()
        self._sendmsg = asyncio.Queue()
        self._running = False
        self._reader : Optional[asyncio.StreamReader] = None
        self._writer : Optional[asyncio.StreamWriter] = None
        self._socket : Optional[socket.socket] = None

    async def _connect(self, timeout: float = 2.0) -> bool:
        """
        异步连接
        """
        logger("Start connect tasks.", thread="lambda/self._connect")
        
        try:
            self._socket = socket.socket()
            self._socket.setblocking(False)
            
            # 设置局域网优化选项
            self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # 禁用Nagle算法
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # 启用保活
            
            logger("Connecting...", thread="lambda/self._connect")
            await asyncio.wait_for(
                asyncio.get_running_loop().sock_connect(self._socket, self._addr),
                timeout=timeout  # 使用参数化的超时时间
            )
            
            return True
            
        except (ConnectionError, OSError, asyncio.TimeoutError) as e:
            logger(f"Connection failed: {e}", thread="lambda/self._connect")
            if self._socket:
                try:
                    self._socket.close()
                except OSError:
                    pass  # 忽略关闭时的错误
                finally:
                    self._socket = None
            return False

    async def _send(self) -> None:
        """
        发送协程

        """
        logger("Send tasks starts", thread = "send_task/self._send")
        loop = asyncio.get_event_loop()

        logger("Entering loop.", thread = "send_task/self._send")
        while self._running:
            try:
                msg = await self._sendmsg.get()
                logger(f"Message '{msg}' ready to be sent.", t = "TRACE", thread = "send_task/self._send")
                
                if self._socket:
                    await loop.sock_sendall(self._socket, (self.id + " " + msg).encode("utf-8"))
                    logger(f"Message {msg} has been sent.", t = "TRACE", thread = "send_task/self._send")
                    
                self._sendmsg.task_done()

            except (ConnectionError, OSError) as e:
                logger(str(e), t = "ERROR", thread = "send_task/self._send")
                self._running = False
                break
            except asyncio.CancelledError as e:
                logger(f"Tasks cancelled : {e}", t = "WARN", thread = "send_task/self._send")
                break

    async def _listen(self) -> None:
        """
        监听协程

        """
        logger("Listen task starts", thread = "listen_task/self._listen")
        loop = asyncio.get_event_loop()

        logger("Entering loop.", thread = "listen_task/self._listen")
        while self._running and self._socket:
            try:
                if self._socket:
                    data = await loop.sock_recv(self._socket, 2048)
                    if data:
                        message = data.decode("utf-8")
                        logger(f"One message received:{data.decode}", t = "TRACE", thread = "listen_task/self._listen")
                        
                        await self._listenmsg.put(message)

            except (ConnectionError, OSError) as e:
                logger(str(e), t = "ERROR", thread = "listen_task/self._listen")
                self._running = False
                break
            except asyncio.CancelledError as e:
                logger(f"Tasks cancelled : {e}", t = "WARN", thread = "send_task/self._send")
                break

    async def recv(self, t: int = 1) -> str:
        """
        从接受消息队列读取消息

        :param t: 接受时限(默认1s)
        :type t: int
        :return: 接受到的消息
        :rtype: str
        """
        try:
            msg = await asyncio.wait_for(
                self._listenmsg.get(),
                timeout = t
            )
            return msg

        except asyncio.TimeoutError:
            return ""

    async def send(self, msg : str) -> None:
        """
        发送消息，
        将消息送入发送序列

        :param msg: 要发送的消息
        :type msg: str
        """
        await self._sendmsg.put(msg)

    async def isalive(self):
        """
        管理listen_thread和send_thread生命周期的函数
        交由lifemanager_thread管理

        """
        logger("life manager task starts.", thread = "life_task/self.isalive")
        while self._running:
            await asyncio.sleep(0.1)

            if not RUNNING:
                logger("Stop RUNNING!", t = "TRACE", thread = "life_task/self.isalive")
                self._running = False
                break

    async def _run(self) -> None:
        """
        客户端游戏逻辑的socket线程 待完善

        """
        global CARD_QUEUE
        logger("Game task starts.", thread = "game_task/self._run")
        
        connect_status = await self.recv() # <- server.server._handle_client
        if connect_status == "":
            logger("Connection timeout.", t = "WARN", thread = "game_task/self._run")
            return
        if connect_status == "failed":
            logger("Connection already full.", t = "WARN", thread = "game_task/self._run")
            return
        self.id = connect_status
        logger(f"Connected successfully, id is {id}.", thread = "game_task/self._run")
        
        ifbegin = await self.recv() # <- server.server._game_run
        
        if ifbegin:
            if ifbegin != "begin":return
            
        logger("Game started.", t = "TRACE", thread = "game_task/self._run")
        UI_MAIN.switch_surfunc(game_screen)
        
        CARD_QUEUE = eval(await self.recv()) # <- server.server._client_run
        
        
        try:
            input("self._run debug,enter to finish task")
        except BaseException:
            pass

    async def start(self) -> None:
        """
        socket总逻辑管理

        """
        global RUNNING
        try:
            logger("Socket starts", thread = "SOCKET_MAIN")
            
            result = await self._connect()
            if not result:
                raise TimeoutError("Connection timeout.")
            logger("Connection established.", thread = "SOCKET_MAIN")
            
            send_task = asyncio.create_task(self._send())
            listen_task = asyncio.create_task(self._listen())
            game_task = asyncio.create_task(self._run())
            life_task = asyncio.create_task(self.isalive())
        
            logger("All socket tasks started.", thread = "SOCKET_MAIN")
            await asyncio.gather(send_task, listen_task, life_task, game_task)
            
        except asyncio.CancelledError as e:
            logger(str(e), t = "ERROR", thread = "SOCKET_MAIN")
            
            game_task.cancel()
            send_task.cancel()
            listen_task.cancel()
            life_task.cancel()
            
            logger("Waiting all tasks free.", t = "TRACE", thread = "SOCKET_MAIN")
            await asyncio.gather(
                game_task, send_task, listen_task, life_task,
                return_exceptions = True
                )
        except TimeoutError as e:
            logger(str(e), t = "ERROR", thread = "SOCKET_MAIN")
            RUNNING = False
            
        finally:
            if self._socket:
                self._socket.close()
            self.close()
            logger("Socket close, SOCKET_MAIN finished!", thread = "SOCKET_MAIN")

    def close(self) -> None:
        """
        关闭连接

        """
        self._running = False


SOCKET_MAIN = SocketMain(TESTADDR)
UI_MAIN = UIMain(welcome_screen)

async def main():
    """
    并发式主函数
    """
    logger("Client starts.")
    await asyncio.gather(SOCKET_MAIN.start(), UI_MAIN.start())

asyncio.run(main())

logger("")