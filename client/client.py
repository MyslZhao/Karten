import pygame # 后续要拆分pygame导入
import socket # 后续拆分socket导入
import threading
import sys
from typing import Tuple, Callable, Any
from abc import ABC, abstractmethod
# -*- encoding: utf-8 -*-

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
    
class Text(DisplayArea):
    """
    自定义组件Text类
    """
    def __init__(self, 
                 text : pygame.Surface, 
                 text_area : pygame.Rect, 
                 bg_color : Tuple[int, int, int],
                 border_width : int, 
                 border_color : Tuple[int, int, int]
                 ):
        self._content : pygame.Surface = text
        self._frame = text_area
        self.bg_color = bg_color
        self.border_width = border_width
        self.border_color = border_color
        
    def _display(self, surface: pygame.Surface) -> None:
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
    @abstractmethod
    def construct(self, *args, **kwargs):...

class ImageFactory(DisplayAreaFactory):
    pass

class TextFactory(DisplayAreaFactory):
    """
    自定义组件Text的工厂类
    """
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def construct(self,
                 text : str,
                 start_pos : Tuple[float, float], 
                 size : Tuple[float, float],
                 text_font : str|None = None,
                 text_size : int = 18,
                 text_color : Tuple[int, int, int] = (0, 0, 0),
                 bg_color : Tuple[int, int, int] = (255, 255, 255),
                 border_width : int = 0,
                 border_color : Tuple[int, int, int] = (255, 255, 255),
                 text_bold : bool = False,
                 text_italic : bool = False,
                 antialias : bool = True #启用字体平滑     
                 ) -> Text:
        text_rect = pygame.Rect(start_pos[0], start_pos[1], size[0], size[1])
        text_obj = pygame.font.SysFont(text_font, text_size, bold=text_bold, italic=text_italic) # 采用系统字体，注意可能的兼容问题
        text_surface = text_obj.render(text, antialias, text_color)
        return Text(text_surface, text_rect, bg_color, border_width, border_color)
        

#-----------------------------------------------------------------------------UI控件--------------------------------------------------------------------------------
class InteractorArea(ABC):
    """
    UI交互控件抽象类
    """
    _func = None
    
    @abstractmethod
    def _display(self, surface : pygame.Surface) -> None:...
    
    @abstractmethod
    def _events(self, event : pygame.event) -> int:...
    
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
            RUNNING = 0
            
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
        :param text: 按钮内文本(可设置为无)
        :type text: pygame.Surface | None
        """
        self.rect = button_rect
        self.color = button_color
        self.border_width = border_width
        self.border_color = border_color
        self.text = text
        self._func = lambda : print("clicked")
    
    def _events(self, event: pygame.event):
        """
        从属于_handle，用于自定义对单一特定交互事件的处理
        
        :param event: 本次处理的事件
        :type event: pygame.event
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self._func()
                return 1
        return 0
    
    def _display(self, surface : pygame.Surface) -> None:
        """
        从属于self.run，用来显示按钮
        
        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        pygame.draw.rect(surface, self.color, self.rect)
        if self.border_width != 0:
            pygame.draw.rect(surface, self.border_color, self.rect, self.border_width)
        if self.text != None:
            surface.blit(self.text,
                         (self.rect.centerx - self.text.get_width() // 2,
                          self.rect.centery - self.text.get_height() // 2)
                         )
            
#---------------------------------------------------------------------------UI控件工厂------------------------------------------------------------------------------
class InteractorAreaFactory(ABC):
    """
    基于pygame传统组件的自定义交互组件工厂抽象类
    """
    @abstractmethod
    def construct(self, *args, **kwargs):...
    
class ButtonFactory(InteractorAreaFactory):
    """
    自定义组件Button的工厂类
    """
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
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
                  text_bold : bool = False,
                  text_italic : bool = False,
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
        :param text_bold: Button字体加粗
        :type text_bold: bool
        :param text_italic: Button字体斜体
        :type text_italic: bool
        :param antialias: Button文本平滑
        :type antialias: bool
        :return: Button对象
        :rtype: Button
        """
        button_rect = pygame.Rect(start_pos[0], start_pos[1], size[0], size[1])
        if text == None:
            return Button(button_rect, button_color, border_width, border_color, None)
        text_obj = pygame.font.SysFont(text_font, text_size, bold=text_bold, italic=text_italic) # 采用系统字体，注意可能的兼容问题
        button_text = text_obj.render(text, antialias, text_color)
        return Button(button_rect, button_color, border_width, border_color, button_text)

#---------------------------------------------------------------------------UI界面设计------------------------------------------------------------------------------

def welcome_screen(surface: pygame.Surface):
    # 欢迎界面
    global RUNNING
    button_factory = ButtonFactory()
    text_factory = TextFactory()
    
    start_text = text_factory.construct("斗地主", (400, 200), (480, 120), border_width=1, text_font="Microsoft YaHei UI")
    start_text.run(surface)
    
    start_button = button_factory.construct((520, 330), (240, 60), "开始", border_width=1, text_font = "Microsoft YaHei UI")
    start_button.bind(lambda : print("hello"))
    start_button.run(surface)
    surface.fill((255, 255, 255))

def game_screen(surface: pygame.Surface):
    # 游戏界面
    pass

WELCOMEFLAG = True
GAMEFLAG = False
RUNNING = True    # 程序运行标识
def main():
    # 主程序
    global RUNNING
    
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
            welcome_screen(screen)
            # ui 绘制 end
            clock.tick(60)
            
    except Exception as e:
        print(f"程序异常: {e}")
    finally:
        # 确保资源被正确释放
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()