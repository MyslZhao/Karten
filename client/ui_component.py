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
from typing import Any, Tuple, Optional, Callable, cast
import os
from enum import Enum
from copy import deepcopy
from pygame import (
    error, image, transform,
    Surface, Rect,
    SRCALPHA, draw, font,
    event, MOUSEBUTTONDOWN
    )
from path_utils import resource_path
# -*- encoding: utf-8 -*-

# NOTE: 在下一次可能的更新前，该文件应消极改写。
# NOTE: 后续组件考虑加入更高级的内容

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

class RectPtn(Enum):
    """
    CIO中碰撞矩形覆盖方式
    """
    FULL = 0
    DISPLAYED = 1
    HIDDEN = 2

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

    @property
    def content(self) -> Any:
        return self._content

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

class CardImage(DisplayArea):
    """牌图片类(简单版本)
    """
    def __init__(self,
                 img : Surface,
                 coord : Tuple[int, int]
                 ):
        self._content = img
        self._coord = coord

    def _display(self, surface: Surface) -> None:
        surface.blit(self._content, self._coord)

# TODO: 待审核代码块 start
class InputBox(DisplayArea):
    """
    文本输入框组件
    """
    def __init__(self,
                 rect: Rect,
                 text_info: Text,
                 bg_color: Color,
                 border: Border,
                 active_border_color: Optional[Color] = None,
                 cursor_color: Color = Color(0, 0, 0),
                 max_length: int = 20,
                 password_char: Optional[str] = None):
        """
        :param rect: 组件位置和大小
        :param text_info: 文本信息（内容、字体、大小、颜色）
        :param bg_color: 背景颜色
        :param border: 边框数据
        :param active_border_color: 激活时的边框颜色（默认与普通边框相同）
        :param cursor_color: 光标颜色
        :param max_length: 最大输入长度
        :param password_char: 密码模式替换字符（如 '*'），None 表示正常显示
        """
        self._frame = rect
        self._content = text_info.text  # 初始文本
        self.text_color = tuple(text_info.color)
        self.bg_color = tuple(bg_color)
        self.border = border
        self.border_color = tuple(border.color)
        self.active_border_color = tuple(active_border_color) if active_border_color else self.border_color
        self.cursor_color = tuple(cursor_color)
        self.max_length = max_length
        self.password_char = password_char

        # 创建字体对象
        if text_info.font is None:
            self.font = font.Font(None, text_info.size)
        else:
            self.font = font.Font(text_info.font, text_info.size)

        # 交互状态
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_interval = 500  # 500ms 闪烁一次

    def _display(self, surface: Surface) -> None:
        """绘制输入框"""
        # 绘制背景
        temp_surf = Surface((self._frame.width, self._frame.height))
        temp_surf.fill(self.bg_color)
        surface.blit(temp_surf, self._frame.topleft)

        # 绘制边框（激活时可能变色）
        if self.border.width > 0:
            border_color = self.active_border_color if self.active else self.border_color
            draw.rect(surface, border_color, self._frame, self.border.width)

        # 准备显示的文本（密码模式处理）
        display_text = self._content
        if self.password_char and self._content:
            display_text = self.password_char * len(self._content)

        # 渲染文本
        text_surface = self.font.render(display_text, True, self.text_color)
        # 垂直居中，左侧留5像素边距
        text_x = self._frame.x + 5
        text_y = self._frame.y + (self._frame.height - text_surface.get_height()) // 2
        # 如果文本宽度超过输入框，考虑截断（简单处理：仅显示末尾部分）
        if text_surface.get_width() > self._frame.width - 10:
            # 裁剪文本，保留末尾能显示的部分
            while text_surface.get_width() > self._frame.width - 10 and display_text:
                display_text = display_text[1:]
                text_surface = self.font.render(display_text, True, self.text_color)
        surface.blit(text_surface, (text_x, text_y))

        # 绘制光标（激活且可见时）
        if self.active and self.cursor_visible:
            cursor_x = text_x + text_surface.get_width() + 2
            cursor_y = self._frame.y + 5
            cursor_height = self.font.get_height()
            draw.line(surface, self.cursor_color,
                      (cursor_x, cursor_y),
                      (cursor_x, cursor_y + cursor_height), 2)

    def handle_event(self, event) -> None:
        """处理输入事件（由主循环调用）"""
        if event.type == MOUSEBUTTONDOWN:
            # 鼠标点击切换激活状态
            if self._frame.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            # 重置光标可见性
            self.cursor_visible = True
            self.cursor_timer = pygame.time.get_ticks()

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                # 回车：可触发外部回调，这里只是示例
                print(f"Input submitted: {self._content}")
                # 可以在这里调用一个外部函数（通过回调）
            elif event.key == pygame.K_BACKSPACE:
                # 退格删除最后一个字符
                self._content = self._content[:-1]
            else:
                # 普通字符输入
                if event.unicode and event.unicode.isprintable():
                    if len(self._content) < self.max_length:
                        self._content += event.unicode

    def update(self) -> None:
        """更新光标闪烁状态（由主循环定期调用）"""
        now = pygame.time.get_ticks()
        if now - self.cursor_timer > self.cursor_interval:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = now

    @property
    def text(self) -> str:
        return self._content

    @text.setter
    def text(self, value: str) -> None:
        self._content = value[:self.max_length]
# NOTE: 待审核代码块 end

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
                 start_pos : Coord,
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
        :type start_pos: Coord
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
        text_rect = Rect(start_pos.x, start_pos.y, size[0], size[1])
        text_obj = font.Font(text.font, text.size)
        text_surface = text_obj.render(text.text, antialias, tuple(text.color))
        return Label(text_surface, text_rect, bg_apparent, bg_color, border)

class CardImageFactory(DisplayAreaFactory):
    """牌图片类工厂
    """
    def construct(self,
                  card_id : Tuple[int, int],
                  start_pos : Coord
                  ) -> Optional[CardImage]:
        """构造牌显示对象

        :param card_id: 牌id
        :type card_id: Tuple[int, int]
        :param start_pos: 绘制起始点(左上角坐标)
        :type start_pos: Coord
        :return: 牌显示对象或None
        :rtype: Optional[CardImage]
        """
        match card_id[0]:
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

        image_path = os.path.join("src", "cards", f"{src}{((card_id[1]) % 13 + 1) % 13 + 1}.png")
        cache = (int(start_pos.x), int(start_pos.y))

        i = image.load(image_path)
        # 缩放图像到合适大小
        i = transform.scale(i, (80, 120))
        return CardImage(i, cache)

# NOTE: 待审核代码块 start
class InputBoxFactory(DisplayAreaFactory):
    """
    输入框组件工厂（单例）
    """
    def construct(self,
                  start_pos: Coord,
                  size: Size,
                  text: Text,
                  bg_color: Color,
                  border: Border = Border(Color(0,0,0), 1),
                  active_border_color: Optional[Color] = None,
                  cursor_color: Color = Color(0,0,0),
                  max_length: int = 20,
                  password_char: Optional[str] = None) -> InputBox:
        """
        构建 InputBox 实例
        :param start_pos: 左上角坐标
        :param size: 宽度和高度
        :param text: 文本信息（初始内容、字体、大小、颜色）
        :param bg_color: 背景颜色
        :param border: 边框数据
        :param active_border_color: 激活时的边框颜色（默认与普通边框相同）
        :param cursor_color: 光标颜色
        :param max_length: 最大输入长度
        :param password_char: 密码字符
        :return: InputBox 对象
        """
        rect = Rect(start_pos.x, start_pos.y, size.length, size.width)
        return InputBox(rect, text, bg_color, border,
                        active_border_color, cursor_color,
                        max_length, password_char)
# NOTE: 待审核代码块 end

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
        self._src_frame = img.get_rect() # 储存原本的图形frame
        self._frame = img.get_rect() # 储存交互应用的图形frame
        self._func = None
        self._pos = pos
        # 抵消素材白边
        self._frame.left = int(pos.x) + 10
        self._frame.top = int(pos.y) + 10
        self._frame.width -= 20
        self._frame.height -= 20

        # 初始化上升碰撞矩形
        self._lift_frame : Rect = deepcopy(self._frame)
        self._lift_frame.top -= 30
        self._lift_frame.height = 30

        self._src_frame.left = int(pos.x)
        self._src_frame.top = int(pos.y)
        self._id = card_id
        self._choosen: bool = False

    def reshape_frame(self, ptn : RectPtn, displd_width : int) -> None:
        """
        更改碰撞矩形的覆盖方式:
        + 全图形覆盖
        + 显示覆盖
        + 隐藏

        默认为全图形覆盖

        :param ptn: 采用的碰撞策略
        :type ptn: RectPtn
        :param displd: (启用DISPLAYED时)图形显示的宽度
        """
        # HACK: 扑克牌左右叠放，只有宽度变化
        # HACK: 在可能的更新中，会严格化DISPLAYED的范围
        match ptn:
            case RectPtn.FULL:
                self._frame = self._src_frame
            case RectPtn.DISPLAYED:
                self._frame.width = displd_width
            case RectPtn.HIDDEN:
                self._frame.width = 0
                self._frame.height = 0

    def handle_events(self, e: event.Event) -> bool:
        """
        处理交互事件

        :param event: 本次处理的事件
        :type event: pygame.event
        """
        if e.type == MOUSEBUTTONDOWN:
            if self._frame.collidepoint(e.pos) and self._func:
                self._func(self)
                return True
            elif (not self._choosen
                ) and (self._lift_frame.collidepoint(e.pos)
                       ) and self._func:
                self._func(self)
                return True
        return False

    def _display(self, surface: Surface) -> None:
        # 绘制图像
        surface.blit(self._content, (self._src_frame.x, self._src_frame.y))

    @property
    def card_id(self) -> Tuple[int, int]:
        """
        牌型id
        """
        return self._id

    def movetocoord(self, coord: Coord) -> None:
        """
        移动到指定坐标
        """
        self._src_frame.x = int(coord.x)
        self._src_frame.y = int(coord.y)
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
                self._src_frame.move_ip(0, -dis)
            case 'd':
                self._frame.move_ip(0, dis)
                self._src_frame.move_ip(0, dis)
            case 'l':
                self._frame.move_ip(-dis, 0)
                self._src_frame.move_ip(-dis, 0)
            case 'r':
                self._frame.move_ip(dis, 0)
                self._src_frame.move_ip(dis, 0)
            case _:
                return

        self._pos = Coord(self._src_frame.x, self._src_frame.y)

    def move_alternating(self, dis: float) -> None:
        """
        交替移动：第一次向上，第二次向下，以此类推

        :param dis: 移动距离
        :type dis: float
        """
        if not self._choosen:
            self.movetowards('u', dis)
        else:
            self.movetowards('d', dis)

        # 切换下一次的方向
        self._choosen = not self._choosen

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
        return Coord(self._src_frame.x, self._src_frame.y)

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
                  start_pos : Coord,
                  size : Tuple[float, float],
                  text : Text = Text("", None, 18),
                  button_color : Color = Color(255, 255, 255),
                  border : Border = Border(Color(0, 0, 0), 0),
                  antialias : bool = True #启用字体平滑
                  ) -> Button:
        """
        构建一个Button对象
        预处理相关零散数据，包装为Button初始化所需的参数

        :param start_pos: Button左上角像素坐标
        :type start_pos: Coord
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
        button_rect = Rect(start_pos.x, start_pos.y, size[0], size[1])
        bt_color = (0, 0, 0)
        if len(tuple(button_color)) == 3:
            bt_color = cast(Tuple[int, int, int], tuple(button_color))
        else:
            text_obj = font.Font(resource_path("src\\fonts\\MicrosoftYaHei.ttf"), text.size)
            bt_text = text_obj.render("颜色错误", antialias, tuple(text.color))
            return Button(button_rect,
                          (0, 0, 0),
                          border,
                          bt_text
                          )
        if text is None:
            return Button(button_rect, bt_color, border, None)
        text_obj = font.Font(text.font, text.size)
        button_text = text_obj.render(text.text, antialias, tuple(text.color))
        return Button(button_rect,
                      bt_color,
                      border,
                      button_text
                      )

class CardImageObjectFactory(InteractorAreaFactory):
    """
    增强版CardImageObject的工厂类
    """
    def construct(self,
                  t: Tuple[int, int],
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
        match t[0]:
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

        image_path = os.path.join("src", "cards", f"{src}{((t[1]) % 13 + 1) % 13 + 1}.png")

        try:
            i = image.load(image_path)
            # 缩放图像到合适大小
            # NOTE: 鉴于没找到合适的小丑牌图片,小丑牌与其他牌大小不一
            i = transform.scale(i, (100, 150))
            return CardImageObject(i, t, start_pos)
        except error:
            # 创建替代图像（红色背景白色边框）
            img = Surface((80, 120))
            img.fill((255, 0, 0))
            draw.rect(img, (255, 255, 255), (5, 5, 70, 110), 2)
            return CardImageObject(img, t, start_pos)

BUTTONFACTORY = ButtonFactory()
LABELFACTORY = LabelFactory()
BOARDFACTORY = BoardFactory()
CIOFACTORY = CardImageObjectFactory()
CIFACTORY = CardImageFactory()
