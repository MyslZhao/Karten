import pygame # 后续要拆分pygame导入
import socket # 后续拆分socket导入
import threading
import sys
from multipledispatch import dispatch
from typing import Tuple, Any, overload
from abc import ABC, abstractmethod
# -*- encoding: utf-8 -*-

class Button:
    """
    自定义组件Button类
    """
    def __init__(self, 
                 button_rect : pygame.Rect, 
                 button_color : Tuple[int, int, int],
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
        :param border_color: 按钮边框颜色RGB
        :type border_color: Tuple[int, int, int]
        :param text: 按钮内文本(可设置为无)
        :type text: pygame.Surface | None
        """
        self.rect = button_rect
        self.color = button_color
        self.border_color = border_color
        self.text = text
    
    def _display(self, surface : pygame.Surface) -> None:
        """
        从属于self.run，用来显示按钮
        
        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2) # 2 为border宽度
        if self.text != None:
            surface.blit(self.text,
                         (self.rect.centerx - self.text.get_width() // 2,
                          self.rect.centery - self.text.get_height() // 2)
                         )
    
    def _handle(self) -> int:
        """
        从属于self.run，用来处理按钮交互事件
        
        :return: 返回状态值
        :rtype: int
        """
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return -1
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.rect.collidepoint(event.pos):
                        print("Button clicked!")
                        return 1
                    
    def run(self, surface : pygame.Surface) -> None:
        """
        在surface上启用button，是self._display与self._handle的联合体
        
        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        global RUNNING
        self._display(surface)
        pygame.display.flip()
        if self._handle() == -1:
            RUNNING = 0
        

class InteractorAreaFactory(ABC):
    """
    基于pygame传统组件的自定义交互组件工厂抽象类
    """
    @abstractmethod
    def construct():...
    
class ButtonFactory(InteractorAreaFactory):
    """
    自定义组件Button的工厂类
    """
    @overload
    def construct(self,
                  start_pos : Tuple[float, float],
                  size : Tuple[float, float],
                  button_color : Tuple[int, int, int] = (255, 255, 255),
                  border_color : Tuple[int, int, int] = (0, 0, 0)
                  ) -> Button:...
    
    @overload
    def construct(self, 
                  start_pos : Tuple[float, float],
                  size : Tuple[float, float],
                  button_color : Tuple[int, int, int] = (255, 255, 255), 
                  border_color : Tuple[int, int, int] = (0, 0, 0),
                  text_color : Tuple[int, int, int] = (0, 0, 0),
                  text_font : str|None = None,
                  text_size : int = 18,
                  text : str = "",
                  antialias : bool = True #启用字体平滑
                  ) -> Button:...
    
    @dispatch(Tuple[float, float],
              Tuple[float, float],
              Tuple[int, int, int],
              Tuple[int, int, int]
              )
    def construct(self,                                               # type: ignore
                  start_pos : Tuple[float, float],
                  size : Tuple[float, float],
                  button_color : Tuple[int, int, int] = (255, 255, 255),
                  border_color : Tuple[int, int, int] = (0, 0, 0)
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
        :param border_color: Button边框颜色
        :type border_color: Tuple[int, int, int]
        :return: Button对象
        :rtype: Button
        """
        button_rect = pygame.Rect(start_pos[0], start_pos[1], size[0], size[1])
        return Button(button_rect, button_color, border_color, None)
    
    @dispatch(Tuple[float, float],
              Tuple[float, float],
              Tuple[int, int, int],
              Tuple[int, int, int],
              Tuple[int, int, int],
              str|None,
              int,
              str,
              bool
              )
    def construct(self,                                               # type: ignore
                  start_pos : Tuple[float, float],
                  size : Tuple[float, float],
                  button_color : Tuple[int, int, int] = (255, 255, 255), 
                  border_color : Tuple[int, int, int] = (0, 0, 0),
                  text_color : Tuple[int, int, int] = (0, 0, 0),
                  text_font : str|None = None,
                  text_size : int = 18,
                  text : str = "",
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
        text_obj = pygame.font.Font(text_font, text_size)
        button_text = text_obj.render(text, antialias, text_color)
        return Button(button_rect, button_color, border_color, button_text)


def welcome_screen(surface: pygame.Surface):
    # 欢迎界面
    global RUNNING
    surface.fill((255, 255, 255))
    
    pass
    
    

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