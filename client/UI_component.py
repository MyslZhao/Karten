"""
使用pygameUI做的为游戏专门设计的UI组件及组件工厂，包括：
+ UI组件相关参数的描述类
+ UI组件及控件
+ UI组件及控件的单例工厂
"""
# pylint: disable=W0221
# pylint: disable=R0903
# 抑制警告：
# + W0221:覆写方法与原方法参数数量不统一/出现不必要的可变参数。
# + R0903:类的公共方法太少(小于2)。
from dataclasses import dataclass
from abc import ABCMeta, abstractmethod
from typing import Any, Tuple, Optional, Callable
import os
from pygame import (
    error, image, transform,
    Surface, Rect,
    SRCALPHA, draw, font,
    event, MOUSEBUTTONDOWN
    )

# -*- encoding: utf-8 -*-

# NOTE: 在下一次可能的更新前，该文件应消极改写。

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
    _frame : Rect

    @abstractmethod
    def _display(self, surface : Surface) -> None:...

    def draw(self, surface : Surface) -> None:
        """
        在surface上启用显示组件

        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        self._display(surface)

class Board(DisplayArea):
    """
    自定义Board类
    """
    def __init__(self,
                 rect : Rect,
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

    def _display(self, surface: Surface) -> None:
        """
        从属于self.run，用来显示背景板组件

        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        temp_surf = Surface((self._frame.width, self._frame.height), SRCALPHA)
        r, g, b = self.color
        temp_surf.fill((r, g, b, self.apparency))
        surface.blit(temp_surf, self._frame.topleft)
        if self.border_width != 0:
            draw.rect(surface, self.border_color, self._frame, self.border_width)

class Label(DisplayArea):
    """
    自定义组件Label类
    """
    def __init__(self,
                 text : Surface,
                 text_area : Rect,
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
        self._content : Surface = text
        self._frame = text_area
        self.bg_apparent = bg_apparent
        self.bg_color = bg_color
        self.border_width = border.width
        self.border_color = tuple(border.color)

    def _display(self, surface: Surface) -> None:
        """
        从属于self.run，用来显示文本组件

        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        if not self.bg_apparent:
            draw.rect(surface, self.bg_color, self._frame)
        if self.border_width != 0:
            draw.rect(surface, self.border_color, self._frame, self.border_width)
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
        board_rect = Rect(start_pos.x, start_pos.y, size.length, size.width)
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
        text_rect = Rect(start_pos[0], start_pos[1], size[0], size[1])
        text_obj = font.Font(text.font, text.size)
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

    @abstractmethod
    def _display(self, surface : Surface) -> None:...

    @abstractmethod
    def handle_events(self, e : event.Event) -> bool:...

    def draw(self, surface : Surface) -> None:
        self._display(surface)

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
                 button_rect : Rect,
                 button_color : Tuple[int, int, int],
                 border : Border,
                 text : Surface|None
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

    def handle_events(self, e: event.Event) -> bool:
        """
        从属于_handle，用于自定义对单一特定交互事件的处理

        :param event: 本次处理的事件
        :type event: pygame.event
        """
        if e.type == MOUSEBUTTONDOWN:
            if self._frame.collidepoint(e.pos):
                if self._func:
                    self._func(self)
                return True
        return False

    def _display(self, surface : Surface) -> None:
        """
        从属于self.run，用来显示按钮

        :param surface: pygame主窗口
        :type surface: pygame.Surface
        """
        draw.rect(surface, self.color, self._frame)
        if self.border_width != 0:
            draw.rect(surface, self.border_color, self._frame, self.border_width)
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
                 img: Surface,
                 card_id: Tuple[int, int],
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
        self._content = img
        self._frame = img.get_rect()
        self._func = None
        self._pos = pos
        self._frame.left = int(pos.x)
        self._frame.top = int(pos.y)
        self._id = card_id
        self._choosen: bool = False
        self._move_up_next: bool = True  # 交替移动方向

    def handle_events(self, e: event.Event) -> bool:
        """
        处理交互事件

        :param event: 本次处理的事件
        :type event: pygame.event
        """
        if e.type == MOUSEBUTTONDOWN:
            if self._frame.collidepoint(e.pos) and self._func:
                self._func(self)
                self._choosen = not self._choosen
                return True
        return False

    def _display(self, surface: Surface) -> None:
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

    def movetowards(self, direc: str, dis: float) -> None:
        """
        向指定方向移动

        :param direc: 方向('u'为向上, 'd'为向下, 'l'为向左, 'r'为向右)
        :type direc: str
        :param dis: 移动距离
        :type dis: float
        """
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

    def move_alternating(self, dis: float) -> None:
        """
        交替移动：第一次向上，第二次向下，以此类推

        :param dis: 移动距离
        :type dis: float
        """
        if self._move_up_next:
            self.movetowards('u', dis)
        else:
            self.movetowards('d', dis)

        # 切换下一次的方向
        self._move_up_next = not self._move_up_next

    @property
    def ischoosen(self) -> bool:
        """
        是否处于选择状态

        :return: 是否处于选择状态
        :rtype: bool
        """
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
        button_rect = Rect(start_pos[0], start_pos[1], size[0], size[1])
        if text is None:
            return Button(button_rect, button_color, border, None)
        text_obj = font.Font(text.font, text.size)
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
        match type[0]:
            case 0:
                src = "heart_"
            case 1:
                src = "spade_"
            case 2:
                src = "club_"
            case 3:
                src = "diamond_"
            case 4:
                src = "joker_"
            case _:
                return None

        image_path = os.path.join("src", "cards", f"{src}{((type[1]) % 13 + 1) % 13 + 1}.png")

        try:
            i = image.load(image_path)
            # 缩放图像到合适大小
            i = transform.scale(i, (80, 120))
            return CardImageObject(i, type, start_pos)
        except error:
            # 创建替代图像（红色背景白色边框）
            img = Surface((80, 120))
            img.fill((255, 0, 0))
            draw.rect(img, (255, 255, 255), (5, 5, 70, 110), 2)
            return CardImageObject(img, type, start_pos)

BUTTONFACTORY = ButtonFactory()
LABELFACTORY = LabelFactory()
BOARDFACTORY = BoardFactory()
CardImageObjectFACTORY = CardImageObjectFactory()