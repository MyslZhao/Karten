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
import socket
import threading
import sys
from dataclasses import dataclass
from typing import Tuple, Callable, Any, Optional
from abc import ABCMeta, abstractmethod
from time import sleep
from collections import deque
import asyncio
import os
import pygame
# -*- encoding: utf-8 -*-
# 用“待”标明TODO事项
CARD_QUEUE = []

# 运行路径初始化
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(application_path)

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
class Text: # 待应用
    """
    基础文本描述类
    """
    text : str
    font : pygame.font.Font
    size : int
    color : Color

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

    @abstractmethod
    def _display(self, surface : pygame.Surface) -> None:...

    def run(self, surface : pygame.Surface) -> None:
        """
        在surface上启用显示组件

        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        self._display(surface)
        pygame.display.flip()

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
                 text : str,
                 start_pos : Tuple[float, float],
                 size : Tuple[float, float],
                 text_font : str|None = None,
                 text_size : int = 18,
                 text_color : Tuple[int, int, int] = (0, 0, 0),
                 bg_apparent : bool = False,
                 bg_color : Tuple[int, int, int] = (255, 255, 255),
                 border : Border = Border(Color(255, 255, 255), 0),
                 antialias : bool = True #启用字体平滑
                 ) -> Label:
        """
        构建一个Label对象
        预处理相关零散数据，包装为Label初始化所需的参数

        :param text: Label文本内容
        :type text: str
        :param start_pos: Label左上角像素坐标
        :type start_pos: Tuple[float, float]
        :param size: Label的长和宽
        :type size: Tuple[float, float]
        :param text_font: Label文本字体
        :type text_font: str | None
        :param text_size: Label文本大小
        :type text_size: int
        :param text_color: Label文本颜色
        :type text_color: Tuple[int, int, int]
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
        text_obj = pygame.font.Font(text_font, text_size)
        text_surface = text_obj.render(text, antialias, text_color)
        return Label(text_surface, text_rect, bg_apparent, bg_color, border)


# UI控件
class InteractorArea(metaclass = ABCMeta):
    """
    UI交互控件抽象类
    """
    _frame = None
    _content = None
    _func = None

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
        pygame.display.flip()
        if self._handle() == -1:
            RUNNING = False

    def bind(self, job : Callable[[], None]) -> None:
        """
        将组件与Func绑定
        规定func为无参数无返回值类型

        :param job: 绑定的方法
        :type job: function
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
        self._func = lambda : print("clicked")

    def _events(self, event: pygame.event.Event):
        """
        从属于_handle，用于自定义对单一特定交互事件的处理

        :param event: 本次处理的事件
        :type event: pygame.event
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._frame.collidepoint(event.pos):
                self._func()
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

class ImageObject(InteractorArea):
    """
    图片交互对象
    """
    def __init__(self,
                 image : pygame.Surface
                 ):
        """
        创建图片交互对象

        :param image: 说明
        :type image: pygame.Surface
        """
        self._frame = image.get_rect()
        self._content = image
        self._func = lambda : print("clicked")

    def _events(self, event: pygame.event.Event):
        """
        从属于_handle，用于自定义对单一特定交互事件的处理

        :param event: 本次处理的事件
        :type event: pygame.event
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._frame.collidepoint(event.pos):
                self._func()
                return 1
        return 0

    def _display(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (0, 0, 0), self._frame)
        surface.blit(self._content,
                     (self._frame.centerx - self._content.get_width() // 2,
                      self._frame.centery - self._content.get_height() // 2)
                     )

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
                  text : str = "",
                  button_color : Tuple[int, int, int] = (255, 255, 255),
                  border : Border = Border(Color(0, 0, 0), 0),
                  text_color : Tuple[int, int, int] = (0, 0, 0),
                  text_font : str|None = None,
                  text_size : int = 18,
                  antialias : bool = True #启用字体平滑
                  ) -> Button:
        """
        构建一个Button对象
        预处理相关零散数据，包装为Button初始化所需的参数

        :param start_pos: Button左上角像素坐标
        :type start_pos: Tuple[float, float]
        :param size: Button的长和宽
        :type size: Tuple[float, float]
        :param button_color: Button的颜色
        :type button_color: Tuple[int, int, int]
        :param border: 边框数据包
        :type border: Border
        :param text_color: Button文本颜色
        :type text_color: Tuple[int, int, int]
        :param text_font: Button文本字体
        :type text_font: str | None
        :param text_size: Button文本大小
        :type text_size: int
        :param text: Button文本内容
        :type text: str
        :param antialias: Button文本平滑
        :type antialias: bool
        :return: Button对象
        :rtype: Button
        """
        button_rect = pygame.Rect(start_pos[0], start_pos[1], size[0], size[1])
        if text is None:
            return Button(button_rect, button_color, border, None)
        text_obj = pygame.font.Font(text_font, text_size)
        button_text = text_obj.render(text, antialias, text_color)
        return Button(button_rect, button_color, border, button_text)

class ImageObjectFactory(InteractorAreaFactory):
    """
    自定义组件ImageObject的工厂类
    """
    def construct(self,
                  src : str,
                  _start_pos : Tuple[float, float] # 待使用
                  ) -> ImageObject:
        """
        构建组件ImageObject

        :param src: 图片相对路径
        :type src: str
        :param start_pos: 图片左上角坐标
        :type start_pos: Tuple[float, float]
        :return: ImageObject对象
        :rtype: ImageObject
        """
        image = pygame.image.load(src)
        return ImageObject(image)
# UI界面设计

def welcome_screen(surface: pygame.Surface, sk_main : "SocketMain") -> None:
    """
    欢迎界面

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    """
    global RUNNING, UI_MAIN

    def start_buttons_job():
        """
        start_button绑定的方法
        """
        asyncio.run(sk_main.send("1"))
        UI_MAIN.switch_surfunc(waiting_screen)
        # 待添加socket交互

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

    start_text = LABELFACTORY.construct("斗地主",
                                       (400, 200),
                                       (480, 120),
                                       text_size = 70,
                                       bg_apparent = True,
                                       text_font = "src\\fonts\\No.400-ShangShouZhaoPaiTi-2.ttf"
                                       )
    start_text.run(surface)

    start_button = BUTTONFACTORY.construct((520, 360),
                                           (240, 60),
                                           "开始",
                                           border = Border(Color(0, 0, 0), 1),
                                           text_font = "src\\fonts\\MicrosoftYaHei.ttf"
                                           )
    start_button.bind(start_buttons_job)
    start_button.run(surface)
    # surface.fill((255, 255, 255))

def waiting_screen(surface : pygame.Surface, sk_main: "SocketMain"):
    """
    等待连接界面

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    """
    global UI_MAIN, RUNNING
    def return_buttons_job():
        """
        return_button绑定的方法
        """
        UI_MAIN.switch_surfunc(welcome_screen)
        asyncio.run(sk_main.send("0"))

    welcome_bg = pygame.image.load("src\\bg\\welcome_bg.jpg")

    surface.blit(welcome_bg, (0, 0))
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

    waiting_text = LABELFACTORY.construct("等待其他玩家...",
                                         (400, 200),
                                         (480, 120),
                                         text_size = 70,
                                         bg_apparent = True,
                                         border = Border(Color(255, 255, 255), 0),
                                         text_font = "src\\fonts\\MicrosoftYaHei.ttf"
                                         )
    waiting_text.run(surface)

    return_button = BUTTONFACTORY.construct((520, 360),
                                            (240, 60),
                                            "返回",
                                            border = Border(Color(255, 255, 255), 1),
                                            text_font = "src\\fonts\\MicrosoftYaHei.ttf"
                                            )
    return_button.bind(return_buttons_job)
    return_button.run(surface)

    # socket接受处理阶段



def game_screen(surface: pygame.Surface):
    """
    游戏界面

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    """
    return
# 特殊类型UI
class Card(ImageObject):... # 待注释(C0115)，待实现

class CardFactory(ImageObjectFactory):... # 待注释(C0115)，待实现

# 客户端主程序
TESTADDR = ("127.0.0.1", 8888)
WELCOMEFLAG = True
GAMEFLAG = False
RUNNING = True    # 程序运行标识
SOCKETRUNNING = True
BUTTONFACTORY = ButtonFactory()
LABELFACTORY = LabelFactory()
BOARDFACTORY = BoardFactory()

class UIMain():
    """
    存有线程ui_thread负责的ui主程序，主管ui绘制
    """

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
        self._surfunc : Callable[[pygame.Surface, SocketMain], None] = new_surfunc

    async def _run(self) -> None:
        """
        UIMain主要运行逻辑

        """
        global RUNNING, SOCKET_MAIN

        pygame.font.init()
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("斗地主")
        clock = pygame.time.Clock()

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

                screen.fill((255, 255, 255))
                pygame.display.flip()

                # ui 绘制 start
                if self._surfunc and SOCKET_MAIN:
                    self._surfunc(screen, SOCKET_MAIN)
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
        await self._run()

class SocketMain():
    """
    线程socket_thread负责的socket主程序，负责与server交换数据
    """
    def __init__(self, addr : Tuple[str, int]): #初始化逻辑待完善
        self._addr = addr
        self._listenmsg = asyncio.Queue()
        self._sendmsg = asyncio.Queue()
        self._running = False
        self._reader : Optional[asyncio.StreamReader] = None
        self._writer : Optional[asyncio.StreamWriter] = None
        self._socket : Optional[socket.socket] = None

    async def _connect(self) -> bool:
        """
        异步连接

        """
        loop = asyncio.get_event_loop()

        try:
            self._socket = socket.socket()
            self._socket.setblocking(False)

            await asyncio.wait_for(
                loop.sock_connect(self._socket, self._addr),
                timeout = 5
                )

            return True

        except (ConnectionError, OSError, asyncio.TimeoutError):
            if self._socket:
                self._socket.close()
                self._socket = None
            return False

    async def _send(self) -> None:
        """
        发送协程

        """
        loop = asyncio.get_event_loop()

        while self._running:
            try:
                msg = await self._sendmsg.get()

                if self._socket:
                    await loop.sock_sendall(self._socket, msg.encode("utf-8"))
                self._sendmsg.task_done()

            except (ConnectionError, OSError):
                self._running = False
                break
            except asyncio.CancelledError:
                break

    async def _listen(self) -> None:
        """
        监听协程

        """
        loop = asyncio.get_event_loop()

        while self._running and self._socket:
            try:
                if self._socket:
                    data = await loop.sock_recv(self._socket, 2048)

                    if data:
                        message = data.decode("utf-8")
                        await self._listenmsg.put(message)

            except (ConnectionError, OSError):
                self._running = False
                break
            except asyncio.CancelledError:
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
        while self._running:
            await asyncio.sleep(0.1)

            if not RUNNING:
                self._running = False
                break

    async def _run(self) -> None:
        """
        客户端游戏逻辑的socket线程

        """
        await self._connect()

        send_task = asyncio.create_task(self._send())
        listen_task = asyncio.create_task(self._listen())
        life_task = asyncio.create_task(self.isalive())

        try:
            await asyncio.gather(send_task, listen_task, life_task)
        except asyncio.CancelledError:
            send_task.cancel()
            listen_task.cancel()
            life_task.cancel()

            await asyncio.gather(
                send_task, listen_task, life_task,
                return_exceptions = True
                )

            # 进入游戏阶段
            connect_status = SOCKET_MAIN.recv()
            if connect_status == "":
                print("连接超时")
                sys.exit(0)
            if connect_status == "failed":
                print("连接已满")
                sys.exit(0)
        finally:
            if self._socket:
                self._socket.close()

    async def start(self) -> asyncio.Task:
        """
        转入self._run运行

        """
        return asyncio.create_task(self._run())

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
    await asyncio.gather(SOCKET_MAIN.start(), UI_MAIN.start())

asyncio.run(main())
