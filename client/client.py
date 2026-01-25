import pygame
import socket
import threading
import sys
from typing import Tuple, Callable, Any
from abc import ABC, abstractmethod
from time import sleep
import os
# -*- encoding: utf-8 -*-
# 用“待”标明TODO事项
CARD_QUEUE = []

#-------------------------------------------------------------------------运行路径初始化----------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(application_path)

#-----------------------------------------------------------------------------UI组件--------------------------------------------------------------------------------
class DisplayArea(ABC):
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
                 color : Tuple[int, int, int],
                 apparency : int,
                 border_width : int,
                 border_color : Tuple[int, int, int]
                 ):
        """
        基于pygame.Rect的背景板组件
        
        :param rect: 组件框架
        :type rect: pygame.Rect
        :param color: 颜色
        :type color: Tuple[int, int, int]
        :param apparency: 透明度
        :type apparency: int
        :param border_width: 边框宽度
        :type border_width: int
        :param border_color: 边框颜色
        :type border_color: Tuple[int, int, int]
        """
        self._frame = rect
        self.color = color
        self.apparency = apparency
        self.border_width = border_width
        self.border_color = border_color
        
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
            
class Text(DisplayArea):
    """
    自定义组件Text类
    """
    def __init__(self, 
                 text : pygame.Surface, 
                 text_area : pygame.Rect, 
                 bg_apparent : bool,
                 bg_color : Tuple[int, int, int],
                 border_width : int, 
                 border_color : Tuple[int, int, int]
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
        :param border_width: 文本边框宽度
        :type border_width: int
        :param border_color: 文本边框颜色
        :type border_color: Tuple[int, int, int]
        """
        self._content : pygame.Surface = text
        self._frame = text_area
        self.bg_apparent = bg_apparent
        self.bg_color = bg_color
        self.border_width = border_width
        self.border_color = border_color
        
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

#---------------------------------------------------------------------------UI组件工厂------------------------------------------------------------------------------
class DisplayAreaFactory(ABC):
    """
    基于pygame传统组件的自定义显示组件工厂抽象类
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @abstractmethod
    def construct(self, *args, **kwargs):...

class BoardFactory(DisplayAreaFactory):
    """
    自定义组件Board的工厂类
    """
    def construct(self, 
                  start_pos : Tuple[float, float],
                  size : Tuple[float, float],
                  color : Tuple[int, int, int],
                  apparency : int = 256,
                  border_width : int = 1,
                  border_color : Tuple[int, int, int] = (0, 0, 0)
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
        :param border_width: Board边框宽度
        :type border_width: int
        :param border_color: Board边框颜色
        :type border_color: Tuple[int, int, int]
        :return: Board对象
        :rtype: Board
        """
        board_rect = pygame.Rect(start_pos[0], start_pos[1], size[0], size[1])
        return Board(board_rect, color, apparency, border_width, border_color)
        
class TextFactory(DisplayAreaFactory):
    """
    自定义组件Text的工厂类
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
                 border_width : int = 0,
                 border_color : Tuple[int, int, int] = (255, 255, 255),
                 antialias : bool = True #启用字体平滑     
                 ) -> Text:
        """
        构建一个Text对象  
        预处理相关零散数据，包装为Text初始化所需的参数
        
        :param text: Text文本内容
        :type text: str
        :param start_pos: Text左上角像素坐标
        :type start_pos: Tuple[float, float]
        :param size: Text的长和宽
        :type size: Tuple[float, float]
        :param text_font: Text文本字体
        :type text_font: str | None
        :param text_size: Text文本大小
        :type text_size: int
        :param text_color: Text文本颜色
        :type text_color: Tuple[int, int, int]
        :param bg_apparent: Text背景透明化
        :type bg_apparent: bool
        :param bg_color: Text背景颜色
        :type bg_color: Tuple[int, int, int]
        :param border_width: Text边框宽度
        :type border_width: int
        :param border_color: Text边框颜色
        :type border_color: Tuple[int, int, int]
        :param antialias: Text文本字体平滑
        :type antialias: bool
        :return: Text对象
        :rtype: Text
        """
        text_rect = pygame.Rect(start_pos[0], start_pos[1], size[0], size[1])
        text_obj = pygame.font.Font(text_font, text_size)
        text_surface = text_obj.render(text, antialias, text_color)
        return Text(text_surface, text_rect, bg_apparent, bg_color, border_width, border_color)
        

#-----------------------------------------------------------------------------UI控件--------------------------------------------------------------------------------
class InteractorArea(ABC):
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
                if res == 0:continue
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
                 border_width : int, 
                 border_color : Tuple[int, int, int],
                 text : pygame.Surface|None
                 ):
        """
        创建一个基于pygame.rect和pygame.text的按钮  
        这个按钮本质为基于pygame.rect检测交互并执行行为的ui容器
        
        :param button_rect: 按钮容器(规定为矩形容器pygame.Rect)
        :type button_rect: pygame.Rect
        :param button_color: 按钮颜色RGB
        :type button_color: Tuple[int, int, int]
        :param border_width: 边框宽度,
        :type border_width: int,
        :param border_color: 按钮边框颜色RGB
        :type border_color: Tuple[int, int, int]
        :param text: 按钮内文本对象(可设置为无)
        :type text: pygame.Surface | None
        """
        self._frame = button_rect
        self.color = button_color
        self.border_width = border_width
        self.border_color = border_color
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
        if self._content != None:
            surface.blit(self._content,
                         (self._frame.centerx - self._content.get_width() // 2,
                          self._frame.centery - self._content.get_height() // 2)
                         )
            
class ImageObject(InteractorArea):
    def __init__(self, 
                 image : pygame.Surface
                 ):
        """ 待注明
        __init__ 的 Docstring
        
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
        
#---------------------------------------------------------------------------UI控件工厂------------------------------------------------------------------------------
class InteractorAreaFactory(ABC):
    """
    基于pygame传统组件的自定义交互组件工厂抽象类
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @abstractmethod
    def construct(self, *args, **kwargs):...
    
class ButtonFactory(InteractorAreaFactory):
    """
    自定义组件Button的工厂类
    """
    def construct(self,
                  start_pos : Tuple[float, float],
                  size : Tuple[float, float],
                  text : str = "",
                  button_color : Tuple[int, int, int] = (255, 255, 255), 
                  border_width : int = 0, 
                  border_color : Tuple[int, int, int] = (0, 0, 0),
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
        :param border_width: Button边框宽度
        :type border_width: int
        :param border_color: Button边框颜色
        :type border_color: Tuple[int, int, int]
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
        if text == None:
            return Button(button_rect, button_color, border_width, border_color, None)
        text_obj = pygame.font.Font(text_font, text_size)
        button_text = text_obj.render(text, antialias, text_color)
        return Button(button_rect, button_color, border_width, border_color, button_text)

class ImageObjectFactory(InteractorAreaFactory):
    """
    自定义组件ImageObject的工厂类
    """
    def construct(self, 
                  src : str,
                  start_pos : Tuple[float, float]
                  ) -> ImageObject:
        """ 待注明
        construct 的 Docstring
        
        :param src: 说明
        :type src: str
        :param start_pos: 说明
        :type start_pos: Tuple[float, float]
        :param size: 说明
        :type size: Tuple[float, float]
        :return: 说明
        :rtype: ImageObject
        """
        image = pygame.image.load(src)
        return ImageObject(image)
#---------------------------------------------------------------------------UI界面设计------------------------------------------------------------------------------

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
        sk_main.send("1")
        UI_MAIN.switch_surfunc(waiting_screen)
        # 待添加socket交互
        
        pass
        
    WELCOME_BG = pygame.image.load("src\\bg\\welcome_bg.jpg")
    
    surface.blit(WELCOME_BG, (0, 0))
    start_board = BOARDFACTORY.construct((360, 150), (560, 420), (255, 255, 255), apparency = 240, border_width = 0) 
    start_board.run(surface)
    
    start_text = TEXTFACTORY.construct("斗地主", (400, 200), (480, 120), text_size = 70, bg_apparent = True, border_width = 0, text_font = "src\\fonts\\No.400-ShangShouZhaoPaiTi-2.ttf")
    start_text.run(surface)
    
    start_button = BUTTONFACTORY.construct((520, 360), (240, 60), "开始", border_width = 1, text_font = "src\\fonts\\MicrosoftYaHei.ttf")
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
        sk_main.send("0")
        
    WELCOME_BG = pygame.image.load("src\\bg\\welcome_bg.jpg")
    
    surface.blit(WELCOME_BG, (0, 0))
    waiting_board = BOARDFACTORY.construct((360, 150), (560, 420), (255, 255, 255), apparency = 240, border_width = 0) 
    waiting_board.run(surface)
    
    waiting_text = TEXTFACTORY.construct("等待其他玩家...", (400, 200), (480, 120), text_size = 70, bg_apparent = True, border_width = 0, text_font = "src\\fonts\\MicrosoftYaHei.ttf")
    waiting_text.run(surface)
    
    return_button = BUTTONFACTORY.construct((520, 360), (240, 60), "返回", border_width = 1, text_font = "src\\fonts\\MicrosoftYaHei.ttf")
    return_button.bind(return_buttons_job)
    return_button.run(surface)
    
    # socket接受处理阶段
    
    

def game_screen(surface: pygame.Surface):
    """
    游戏界面
    
    :param surface: pygame主窗口
    :type surface: pygame.Surface
    """
    pass
#---------------------------------------------------------------------------特殊类型UI------------------------------------------------------------------------------
class Card(ImageObject):pass

class CardFactory(ImageObjectFactory):pass

#--------------------------------------------------------------------------客户端主程序-----------------------------------------------------------------------------
TESTADDR = ("127.0.0.1", 8888)
WELCOMEFLAG = True
GAMEFLAG = False
RUNNING = True    # 程序运行标识
SOCKETRUNNING = True
BUTTONFACTORY = ButtonFactory()
TEXTFACTORY = TextFactory()
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
        
    def _run(self):
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
                
                # 如果窗口被强制关闭（某些系统可能不发送QUIT事件）
                if not pygame.display.get_init():
                    RUNNING = False
                
                screen.fill((255, 255, 255))            
                pygame.display.flip()
                
                # ui 绘制 start
                self._surfunc(screen, SOCKET_MAIN)
                # ui 绘制 end
                
                clock.tick(120)
                
        except Exception as e:
            print(f"程序异常: {e}")
        finally:
            # 确保资源被正确释放
            pygame.quit()
    
    def start(self):
        """
        将self._run交给单独的线程运行  
        
        """
        ui_thread = threading.Thread(target = self._run, name = "UI thread")
        ui_thread.start()

class SocketMain():
    """
    线程socket_thread负责的socket主程序，负责与server交换数据
    """
    def __init__(self, addr : Tuple[str, int]): #初始化逻辑待完善
        self._ADDR = addr
        self._listenmsg = []
        self._sendmsg = []
        self._flag = 0
        self._listenflag = 1
        self._sendflag = 1
    
    def _send(self) -> None:
        while True:
            try:
                if self._flag:break
                if self._sendmsg == []:continue
                if self._flag:break
                if not RUNNING:self._flag = 1
                self._socket.sendall(self._sendmsg.pop(0).encode("utf-8"))
            except BaseException:
                self._flag = 1
                continue
        self._sendflag = 0
    
    def _listen(self) -> None:
        while True:
            try:
                if self._flag:break
                cache = self._socket.recv(2048).decode("utf-8")
                if cache != None:
                    self._listenmsg.append(cache)
            except BaseException:
                self._flag = 1
                continue
        self._listenflag = 0
    
    def recv(self, t: int = 1) -> str:
        """使用事件机制等待消息"""
        # 如果已经有消息，直接返回
        if self._listenmsg:
            return self._listenmsg.pop(0)
        
        # 创建一个事件对象
        msg_event = threading.Event()
        
        # 定时器线程：t秒后触发事件
        def timer():
            sleep(t)
            msg_event.set()
        
        timer_thread = threading.Thread(target=timer, daemon=True)
        timer_thread.start()
        
        # 等待事件被触发（有消息到达或超时）
        msg_event.wait()
        
        # 检查是否有消息
        if self._listenmsg:
            return self._listenmsg.pop(0)
        return ""
        
    def send(self, msg : str) -> None:
        self._sendmsg.append(msg)
        
    def start(self) -> None:
        """
        将self._run交给单独的线程运行  
        
        """
        self._socket = socket.socket()
        self._socket.connect(self._ADDR)
        
        listen_thread = threading.Thread(target = self._listen, name = "listen thread")
        send_thread = threading.Thread(target = self._send, name = "send thread")
        lifemanager_thread = threading.Thread(target = self.isalive, name = "life_manager")
        listen_thread.start()
        send_thread.start()
        lifemanager_thread.start()
        
    def isalive(self):
        global RUNNING, SOCKETRUNNING
        while True:
            if not RUNNING:
                self._flag = 1
                break
        while True:
            if not self._sendflag:
                SOCKETRUNNING = False
                self._socket.close()
                break
        
SOCKET_MAIN = SocketMain(TESTADDR)
SOCKET_MAIN.start()

connect_status = SOCKET_MAIN.recv()
if connect_status == "":
    print("连接超时")
    sys.exit(0)
if connect_status == "failed":
    print("连接已满")
    sys.exit(0)

UI_MAIN = UIMain(welcome_screen)
UI_MAIN.start()

while True:
    if not RUNNING and not SOCKETRUNNING:
        break