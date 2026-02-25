"""
客户端程序，包含了：
+ 各个界面的pygame func
+ UI/Sock双线程
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
from typing import Tuple, Callable, Optional, List, cast
from socket import IPPROTO_TCP, TCP_NODELAY, SOL_SOCKET, SO_KEEPALIVE
import os
import sys
import asyncio
import json
from enum import Enum
import pygame
from cards_transfer import CardsTransfer
from cards_identifier import Identifier, Pattern, Cards
from cards_judger import Judger
from ui_component import (
    Coord, Size, Color, Text, Border, RectPtn,
    InteractorArea, Button, CardImageObject,
    BUTTONFACTORY, LABELFACTORY, BOARDFACTORY, CIOFACTORY,
    CIFACTORY
)
from logger import Logger # DEBUG
from path_utils import resource_path
# -*- encoding: utf-8 -*-
# pylint: disable=C2401

class Idtt(Enum):
    """身份信息映射

    """
    农民 = 0
    地主 = 1

ID = 0 # 玩家id号
RELATIVE_ID = [0, 0, 0] # 相对位置 -> id
IDENLIST = [0, -1, -1, -1] # id -> identity
IDENTITY = 0 # 身份, 1为地主, 0为农民
TURN : int = 1 # 标明哪个玩家的回合
ISEND = 0

RECV_QUEUE : List[Optional[List[int]]] = [] # 接收牌列(初始化使用)
LORD_QUEUE : List[Optional[List[int]]] = [] # 地主牌型

# 发送牌型(牌数 + 牌型)
CARD_SEND : Tuple[int, Cards] = (-1, Cards(Pattern.NONE, None))
SRC_LIST : List[Tuple[int, int]] = [(-1, -1)]
# 得到的广播牌型(id + 牌型)
CARD_RECV : Tuple[int, Cards] = (-1, Cards(Pattern.NONE, None))
# 储存所有玩家的牌数供显示, id -> cn
CARDS_NUMS : List[int] = [0, 17, 17, 17]
# 显示区域
DISPLAY_CARDS : List[Optional[Tuple[int, int]]] = []

async def check_send_ready(
    ) -> Tuple[int, Cards]:
    """检查是否准备发送

    :return: 要发送的牌型信息
    :rtype: Tuple[int, Cards]
    """
    global CARD_SEND
    while True:
        if CARD_SEND[0] != -1:
            cp = CARD_SEND
            CARD_SEND = (-1, Cards(Pattern.NONE, None))
            return cp
        await asyncio.sleep(0.1)

def card_clicked_job(cio: InteractorArea) -> None:
    """
    图片点击触发事件

    :param cio: 事件绑定的cio对象
    :type cio: InteractorArea
    """
    if isinstance(cio, CardImageObject):
        cio.move_alternating(30)
        CARD_STK.switch_clicked(cio.card_id)

class Cardstack:
    """
    手牌堆管理类(Tuple[int, int])
    """
    _movequant : int = 30
    _hand_cards : List[Optional[Tuple[int, int]]] = [] #手牌id序列
    _render_cards : List[Optional[CardImageObject]] = [] #手牌渲染类序列
    _clicked_cards : List[Optional[Tuple[int, int]]] = [] #选中牌id序列
    _rdcenter_coord : Tuple = (0, 0)

    def bind(self, ui_main : "UIMain") -> None:
        """绑定ui管理类

        :param ui_main: 绑定的ui类
        :type ui_main: UIMain
        """
        self._ui_main = ui_main

    def set_center(self, coord : Coord) -> None:
        """设置渲染中心

        :param coord: 中轴线上顶点坐标
        :type coord: Coord
        """
        self._rdcenter_coord = (coord.x, coord.y)

    def add_cards(self, cards : Tuple[int, int] | List[Tuple[int, int]]) -> None:
        """添加牌

        :param cards: 要添加的牌
        :type cards: Tuple[int, int] | List[Tuple[int, int]]
        """
        _cache = cards[0]
        if isinstance(_cache, int):
            _card : Tuple[int, int] = cast(Tuple[int, int], cards)
            self._hand_cards.append(_card)
            if self._hand_cards:
                self._hand_cards.sort(key = lambda x : x[1] if x else 0)

        if isinstance(_cache, tuple):
            _cards : List[Tuple[int, int]] = cast(List[Tuple[int, int]], cards)
            self._hand_cards.extend(_cards)
            if self._hand_cards:
                self._hand_cards.sort(key = lambda x : x[1] if x else 0)

        self.update_render() # 更新ui

    def clear_cards(self) -> None:
        """清空牌
        """
        self._hand_cards.clear()

        self.update_render()

    @property
    def cards_num(self) -> int:
        """手牌数

        :return: 手牌数
        :rtype: int
        """
        return len(self._hand_cards)

    def update_render(self) -> None:
        """更新注册
        """
        self._ui_main.clear_cards()
        centred = self.cards_num >> 1
        for cdi, cdv in enumerate(self._hand_cards):
            if cdv:
                cd = cast(Tuple[int, int], cdv)
                _cd = CIOFACTORY.construct(
                    cd,
                    Coord(
                        self._rdcenter_coord[0] - (centred - cdi) * 20,
                        self._rdcenter_coord[1]
                    ))

                if _cd:
                    if cdi != self.cards_num - 1:
                        _cd.reshape_frame(RectPtn.DISPLAYED, 20)
                    _cd.bind(card_clicked_job)
                    self._ui_main.add_interactors(_cd)
                    self._render_cards.append(_cd)

    @property
    def clicked_card(self) -> List[Optional[Tuple[int, int]]]:
        """选中的牌

        :return: 选中的牌
        :rtype: List[Optional[Tuple[int, int]]]
        """
        return self._clicked_cards

    def switch_clicked(self, card : Tuple[int, int]) -> None:
        """改变选中状态

        :param card: 被点选的卡牌
        :type card: Tuple[int, int]
        """
        if card in self._clicked_cards:
            self._clicked_cards.remove(card)
        else:
            self._clicked_cards.append(card)

    def recover_clicked(self) -> None:
        """恢复相关移动状态
        """
        for i in self._render_cards:
            if i and i.ischoosen:
                i.move_alternating(30)

        self._clicked_cards.clear()

    def remove_clicked(self) -> None:
        """移除选中
        """
        for i in self._clicked_cards:
            if i:
                self._hand_cards.remove(i)

        if self._hand_cards:
            self._hand_cards.sort(key = lambda x : x[1] if x else 0)

        self._clicked_cards.clear()
        self.update_render()

CARD_STK = Cardstack()

# UI界面设计
def welcome_screen(surface: pygame.Surface, ui_main : "UIMain", sk_main : "SocketMain") -> None:
    """
    欢迎界面

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    :param ui_main: UI绘制类
    :type ui_main: UIMain
    :param sk_main: 异步通信类
    :type sk_main: SocketMain
    """
    def start_buttons_job(_button : InteractorArea):
        """
        start_button绑定的方法
        """
        asyncio.create_task(sk_main.send(str(sk_main.id) + "1")) # -> server.server._client_run
        ui_main.switch_surfunc(waiting_screen)

    if ui_main.interactors_emp:# 交互组件事件注册
        # 主Frame按钮注册
        start_button = BUTTONFACTORY.construct(Coord(520, 360),
                                            (240, 60),
                                            Text("开始",
                                                    resource_path("src\\fonts\\MicrosoftYaHei.ttf"),
                                                    18
                                                    ),
                                            border = Border(Color(0, 0, 0), 1)
                                            )
        start_button.bind(start_buttons_job)
        ui_main.add_interactors(start_button)

    # 窗口背景载入
    welcome_bg = pygame.image.load(resource_path("src\\bg\\welcome_bg.jpg"))
    surface.blit(welcome_bg, (0, 0))
    # 主Frame背景载入
    BOARDFACTORY.construct(
        Coord(360, 150),
        Size(560, 420),
        Color(255, 255, 255),
        apparency = 240,
        border = Border(
            Color(0, 0, 0),
            width = 0
            )
        ).draw(surface)

    # 主Frame标题载入
    LABELFACTORY.construct(
        Text(
            "斗地主",
            resource_path("src\\fonts\\No.400-ShangShouZhaoPaiTi-2.ttf"),
            70
            ),
        Coord(400, 200),
        (480, 120),
        bg_apparent = True
        ).draw(surface)

def waiting_screen(surface : pygame.Surface, _ui_main : "UIMain", _sk_main: "SocketMain") -> None:
    """
    等待连接界面

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    :param ui_main: UI绘制类
    :type ui_main: UIMain
    :param _sk_main: 异步通信类
    :type _sk_main: SocketMain
    """
    # 窗口背景载入
    waiting_bg = pygame.image.load(resource_path("src\\bg\\welcome_bg.jpg"))
    surface.blit(waiting_bg, (0, 0))

    # 主Frame背景载入
    BOARDFACTORY.construct(
        Coord(360, 150),
        Size(560, 420),
        Color(255, 255, 255),
        apparency = 240,
        border = Border(
            Color(0,0,0),
            width = 0
            )
        ).draw(surface)

    # 主Farme说明文本载入
    LABELFACTORY.construct(
        Text(
            "等待其他玩家...",
            resource_path("src\\fonts\\MicrosoftYaHei.ttf"),
            70
            ),
        Coord(400, 200),
        (480, 120),
        bg_apparent = True,
        border = Border(Color(255, 255, 255), 1)
        ).draw(surface)

def game_screen(surface: pygame.Surface, ui_main : "UIMain", _sk_main : "SocketMain") -> None:
    """
    游戏界面

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    :param ui_main: UI绘制类
    :type ui_main: UIMain
    :param _sk_main: 异步通信类
    :type _sk_main: SocketMain
    """
    game_bg = pygame.image.load(resource_path("src\\bg\\game_bg.png"))
    surface.blit(game_bg, (0, 0))

    CARD_STK.set_center(Coord(400, 550))
    if RECV_QUEUE:
        for i in RECV_QUEUE:
            _cst = cast(Tuple[int, int], i) # HACK: u know it xp.
            CARD_STK.add_cards(_cst)

        RECV_QUEUE.clear()

    def submit_button_job(bt : InteractorArea) -> None:
        if isinstance(bt, Button):
            global CARD_SEND, SRC_LIST
            if ISEND:
                CARD_STK.recover_clicked()
                return

            if CARD_RECV[0] == -1:
                clicked_queue = CARD_STK.clicked_card
                if clicked_queue:
                    cld_queue = cast(List[List[int]], clicked_queue)
                    cd = Identifier.identify(cld_queue)
                    if cd.pattern == Pattern.NONE:
                        CARD_STK.recover_clicked()
                    else:
                        CARD_SEND = (len(cld_queue), cd)
                        SRC_LIST = cast(List[Tuple[int, int]], [tuple(i) for i in cld_queue])
                        CARD_STK.remove_clicked()
                return

            if CARD_RECV[0] != ID:
                return

            clicked_queue = CARD_STK.clicked_card
            if clicked_queue:
                cld_queue = cast(List[List[int]], clicked_queue)
                cd = Identifier.identify(cld_queue)
                if cd.pattern == Pattern.NONE:
                    CARD_STK.recover_clicked()

                else:
                    res = Judger.compare(CARD_RECV[1], cd)
                    if res == 2:
                        SRC_LIST = cast(List[Tuple[int, int]], [tuple(i) for i in cld_queue])
                        CARD_SEND = (len(cld_queue), cd)
                        CARD_STK.remove_clicked()
                    else:
                        CARD_STK.recover_clicked()

    def pass_button_job(bt : InteractorArea) -> None:
        if isinstance(bt, Button):
            if ISEND:
                CARD_STK.recover_clicked()
            global CARD_SEND
            CARD_STK.recover_clicked()
            CARD_SEND = (0, Cards(Pattern.NONE, None))

    # 出牌按钮
    submit_button = BUTTONFACTORY.construct(
            Coord(500, 480),
            (100, 50),
            Text(
                "出",
                font = resource_path("src\\fonts\\button.ttf"),
                size = 17
            ),
            button_color = Color(201, 175, 47)
        )
    submit_button.bind(submit_button_job)
    ui_main.add_interactors(submit_button)

    # 过~ 按钮
    pass_button = BUTTONFACTORY.construct(
            Coord(250, 480),
            (100, 50),
            Text(
                "过",
                font = resource_path("src\\fonts\\button.ttf"),
                size = 17
            ),
            button_color = Color(164, 164, 164)
        )
    pass_button.bind(pass_button_job)
    ui_main.add_interactors(pass_button)

    prir = ID - 1 if ID - 1 else 3
    nxt = (ID % 3) + 1
    if -1 not in IDENLIST:
        LABELFACTORY.construct(
            Text(
                f"{'>' if TURN == prir else ''}上家({Idtt(IDENLIST[prir]).name}): {CARDS_NUMS[prir]}张牌",
                resource_path("src\\fonts\\MicrosoftYaHei.ttf"),
                size = 20
                ),
            Coord(1050, 20),
            size = (180, 30),
            bg_apparent = False,
            bg_color = (190, 45, 37),
            border = Border(
                Color(0, 0, 0),
                width = 1
                )
            ).draw(surface) # 上家牌数

        LABELFACTORY.construct(
            Text(
                f"{'>' if TURN == ID else ''}本家({Idtt(IDENLIST[ID]).name}): {CARDS_NUMS[ID]}张牌",
                resource_path("src\\fonts\\MicrosoftYaHei.ttf"),
                size = 20
                ),
            Coord(1050, 60),
            size = (180, 30),
            bg_apparent = False,
            bg_color = (190, 185, 37),
            border = Border(
                Color(0, 0, 0),
                width = 1
                )
            ).draw(surface) # 本家牌数

        LABELFACTORY.construct(
            Text(
                f"{'>' if TURN == nxt else ''}下家({Idtt(IDENLIST[nxt]).name}): {CARDS_NUMS[nxt]}张牌",
                resource_path("src\\fonts\\MicrosoftYaHei.ttf"),
                size = 20
                ),
            Coord(1050, 100),
            size = (180, 30),
            bg_apparent = False,
            bg_color = (117, 190, 37),
            border = Border(
                Color(0, 0, 0),
                width = 1
                )
            ).draw(surface) # 下家牌数

    # 绘制地主牌展示
    if LORD_QUEUE:
        lord_cache = cast(List[List[int]], LORD_QUEUE)
        for i, v in enumerate(lord_cache):
            ion = CIFACTORY.construct(
                (v[0], v[1]),
                Coord(330 + i * 70, 50)
            )
            if ion:
                ion.draw(surface)

    # 绘制所出牌
    if DISPLAY_CARDS:
        display_cards = cast(List[Tuple[int, int]], DISPLAY_CARDS)
        centred_x = 410
        centred_num = len(display_cards) >> 1
        for i, v in enumerate(display_cards):
            ion = CIFACTORY.construct(
                (v[0], v[1]),
                Coord(centred_x - (centred_num - i) * 30, 360)
            )
            if ion:
                ion.draw(surface)

    # 胜利信息显示
    if ISEND:
        LABELFACTORY.construct(
            Text(
                f"{Idtt(IDENLIST[ISEND]).name}阵营胜利",
                resource_path("src\\fonts\\No.400-ShangShouZhaoPaiTi-2.ttf"),
                40),
            Coord(1050, 330),
            (150, 30),
            bg_apparent = True
        ).draw(surface)

        LABELFACTORY.construct(
            Text(
                "20秒后关闭界面",
                resource_path("src\\fonts\\MicrosoftYaHei.ttf"),
                12,
                color = Color(162, 162, 162)
                ),
            Coord(1060, 370),
            (120, 10),
            bg_apparent = True
        ).draw(surface)

# 客户端主程序
TESTADDR = ("127.0.0.1", 8888)
ADDR = (input("输入服务器ip(忘记设计ip输入组件了xp):"), 8888)

class UIMain():
    """
    ui主程序，主管ui绘制
    """
    _screen : pygame.Surface
    _buttons : List[Optional[Button]] = []
    _cios : List[Optional[CardImageObject]] = []

    def __init__(self,
                 start_surfunc : Callable[[pygame.Surface, "UIMain", "SocketMain"], None],
                 socket_main : "SocketMain"
                 ):
        """
        用一个界面方法初始化一个UIMain对象

        :param start_surfunc: 初始界面((pygame.Surface) -> None)
        :type start_surfunc: Callable[[pygame.Surface], None]
        """
        self._socket_main : Optional[SocketMain] = socket_main
        self._surfunc : Callable[[pygame.Surface, UIMain, SocketMain], None] = start_surfunc

    @property
    def interactors_emp(self) -> bool:
        """
        返回注册的交互事件是否为空

        :return: 注册的交互事件是否为空
        :rtype: bool
        """
        return len(self._buttons) + len(self._cios) == 0

    def clear_buttons(self):
        """清除注册的按钮事件
        """
        self._buttons.clear()

    def clear_cards(self):
        """清除注册的cio事件
        """
        self._cios.clear()

    def add_interactors(self, interactor : InteractorArea) -> None:
        """
        注册新的交互事件

        :param interactor: 交互事件所属的交互组件
        :type interactor: InteractorArea
        """
        if isinstance(interactor, Button):
            self._buttons.append(interactor)
        if isinstance(interactor, CardImageObject):
            self._cios.append(interactor)

    def clear_interactors(self) -> None:
        """
        清除不再需要的交互事件

        """
        self.clear_buttons()
        self.clear_cards()

    def switch_surfunc(self,
                       new_surfunc : Callable[
                           [pygame.Surface, "UIMain", "SocketMain"],
                           None
                           ]
                       ) -> None:
        """
        切换界面方法

        :param new_surfunc: 新的界面((pygame.Surface) -> None)
        :type new_surfunc: Callable[[pygame.Surface], None]
        """
        self.clear_interactors()
        self._surfunc : Callable[[pygame.Surface, UIMain, SocketMain], None] = new_surfunc

    async def _run(self) -> None:
        """
        UIMain主要运行逻辑

        """
        pygame.font.init()
        pygame.init()
        self._screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("斗地主")
        try:
            while True:
                events = pygame.event.get()
                for e in events:
                    if e.type == pygame.QUIT:
                        return
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            return

                    for itactor in self._buttons:
                        if itactor and itactor.handle_events(e):
                            break

                    for itactor in self._cios:
                        if itactor and itactor.handle_events(e):
                            break

                self._screen.fill((255, 255, 255))
                if self._surfunc and self._socket_main:
                    self._surfunc(self._screen, self, self._socket_main)

                for itactor in self._buttons:
                    if itactor:
                        itactor.draw(self._screen)

                for itactor in self._cios:
                    if itactor:
                        itactor.draw(self._screen)

                pygame.display.flip()

                await asyncio.sleep(1/60)

        except KeyboardInterrupt as e:
            Logger.write(f"{e}", t = "ERROR", thread = "UI_MAIN")
        finally:
            # 确保资源被正确释放
            pygame.quit()

    async def start(self) -> None:
        """
        转入self._run运行

        """
        Logger.write("UI starts", t = "INFO", thread = "UI_MAIN")
        await self._run()

class SocketMain():
    """
    线程socket_thread负责的socket主程序，负责与server交换数据
    """
    id = "0"
    _ui_main : Optional[UIMain]

    def __init__(self, addr : Tuple[str, int]):
        self._addr = addr
        self._listenmsg = asyncio.Queue()
        self._sendmsg = asyncio.Queue()
        self._reader : Optional[asyncio.StreamReader] = None
        self._writer : Optional[asyncio.StreamWriter] = None
        self._connected : bool = False

    def set_ui(self, ui_main : UIMain) -> None:
        """
        延迟引用ui_main

        :param ui_main: 渲染类对象
        :type ui_main: UIMain
        """
        self._ui_main = ui_main

    async def _connect(self, timeout: float = 5.0) -> bool:
        """
        异步连接

        :param timeout: 超时时限
        :type timeout: float
        :return: 连接状态
        :rtype: bool
        """
        Logger.write("Start connect tasks.", thread="lambda/self._connect")

        try:
            Logger.write("Connecting...", thread="lambda/self._connect")
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(
                    host = self._addr[0],
                    port = self._addr[1]
                    ),
                timeout = timeout
            )

            peername = self._writer.get_extra_info('peername')
            if peername:
                Logger.write(f'Connection ready, server at {peername}',
                             thread = 'lambda/self._connect')

            sock = self._writer.get_extra_info('socket')
            if sock:
                sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1) # 禁用Nagle
                sock.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1) # 启用保活

            return True

        except (ConnectionError, OSError, asyncio.TimeoutError) as e:
            Logger.write(f"Connection failed: {e}, plz check your addr.", thread="lambda/self._connect")
            if self._writer:
                try:
                    self._writer.close()
                    await self._writer.wait_closed()
                except Exception:
                    pass
                finally:
                    self._writer = None
                    self._reader = None
            return False

        except Exception as e:
            Logger.write(f"Unexpected error during connection: {e}",
                   t="ERROR",
                   thread="lambda/self._connect")

            if self._writer:
                try:
                    self._writer.close()
                except Exception:
                    pass
                self._writer = None
                self._reader = None
            return False

    async def _send(self) -> None:
        """
        发送协程

        """
        Logger.write("Send tasks loops.", thread = "send_task/self._send")

        while True:
            try:
                msg = await self._sendmsg.get()
                Logger.write(f"Message '{msg}' ready to be sent.",
                             t = "TRACE",
                             thread = "send_task/self._send")

                if self._writer and not self._writer.is_closing():
                    self._writer.write(msg.encode('utf-8'))
                    await self._writer.drain()
                    Logger.write(f"Message {msg} has been sent.",
                                 t = "TRACE",
                                 thread = "send_task/self._send")
                else:
                    Logger.write('Writer failed, plz check the status of self._writer.',
                                 t = "WARN",
                                 thread = "send_task/self._send")

                self._sendmsg.task_done()

            except (ConnectionError, OSError, BrokenPipeError) as e:
                Logger.write(str(e), t = "ERROR", thread = "send_task/self._send")
                raise
            except asyncio.CancelledError as e:
                Logger.write(f"Tasks cancelled : {e}", t = "WARN", thread = "send_task/self._send")
                raise
            except Exception as e:
                if ISEND:
                    Logger.write(f"{e}, but game was over.", thread = "send_task/self._send")
                else:
                    Logger.write(f"{e}, but the game is still going!", t = "ERROR", thread = "send_task/self._send")

    async def _listen(self) -> None:
        """
        监听协程

        """
        Logger.write("Listen task loops", thread = "listen_task/self._listen")

        while True:
            try:
                data = b''
                if self._reader:
                    data = await self._reader.readuntil(b'\n')

                msg = data.decode("utf-8").strip()

                if msg == "":
                    await asyncio.sleep(0.1)
                    continue
                Logger.write(f'msg : "{msg}" received',
                             t = "TRACE",
                             thread = "listen_task/self._listen")

                await self._listenmsg.put(msg)

            except (asyncio.IncompleteReadError, ConnectionError, OSError) as e:
                Logger.write(f"{e}, connect status is {self._connected}", t = "ERROR", thread = "listen_task/self._listen")
                raise
            except asyncio.CancelledError as e:
                Logger.write(f"Tasks cancelled : {e}", t = "WARN", thread = "send_task/self._send")
                raise

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
        await self._sendmsg.put(msg + '\n')

    async def _run(self) -> None:
        """
        客户端游戏逻辑的socket逻辑 待完善

        """
        global RECV_QUEUE, LORD_QUEUE, IDENTITY, ISEND
        global ID, TURN, CARD_RECV, DISPLAY_CARDS
        Logger.write("Game task starts.", thread = "game_task/self._run")

        connect_status = await self.recv() # <- server.server._handle_client
        if connect_status == "":
            Logger.write("Connection timeout.", t = "WARN", thread = "game_task/self._run")
            return
        if connect_status == "f":
            Logger.write("Connection already full.", t = "WARN", thread = "game_task/self._run")
            return

        ID = int(connect_status)
        RELATIVE_ID[0] = ID
        RELATIVE_ID[-1] = 3 if ID - 1 == 0 else ID - 1
        RELATIVE_ID[1] = (ID % 3) + 1
        self.id = connect_status
        Logger.write(f"Connected successfully, id is {self.id}.", thread = "game_task/self._run")

        ifbegin = await self.recv(t = 180) # <- server.server._game_run

        if ifbegin:
            if ifbegin != "b":
                Logger.write("Waiting timeout, exit automatically.", thread = "game_task/self._run")
                return

        Logger.write("Game started.", t = "TRACE", thread = "game_task/self._run")
        if self._ui_main:
            self._ui_main.switch_surfunc(game_screen)

        LORD_QUEUE = json.loads(await self.recv()) # <- server.server._game_run List[int]

        idlist = list(await self.recv()) # <- serevr.Server._client_run "xxx"
        for i in range(3):
            IDENLIST[i + 1] = int(idlist[i])
        IDENTITY = IDENLIST[ID]
        CARDS_NUMS[IDENLIST.index(1)] += 3
        TURN = IDENLIST.index(1)

        RECV_QUEUE = json.loads(await self.recv()) # <- server.server._client_run

        Logger.write("Round loops.", thread = "game_task/self._run")
        recv_msg = ""
        while True:
            if ID == TURN:
                # 出牌回合
                res = await check_send_ready()
                if res[0] == 0:
                    Logger.write(f"passcode trigger, CARD_SEND = {res}", t = "DEBUG", thread = "game_task/self._run")
                    await self.send(
                        CardsTransfer.passcode(recv_msg)
                    )
                else:
                    await self.send(
                        CardsTransfer.covercode(
                            ID,
                            res[0],
                            res[1],
                            SRC_LIST
                            )
                        )

            else:
                # 非出牌回合
                pass

            while True:
                recv_msg = await self.recv()
                if recv_msg == "":
                    continue
                break

            cache = CardsTransfer.parsetotuple(recv_msg)
            CARDS_NUMS[cache[1] - 1 if cache[1] - 1 else 3] -= cache[2]

            if cache[0] == cache[1] and ID == cache[1]:
                CARD_RECV = (-1, Cards(Pattern.NONE, None))
            else:
                CARD_RECV = (cache[1], cache[3])
            DISPLAY_CARDS.clear()
            DISPLAY_CARDS = cast(List[Optional[Tuple[int, int]]], cache[4])
            if 0 in CARDS_NUMS[1:]:
                ISEND = CARDS_NUMS[1:].index(0) + 1
                break

            TURN = cache[1]
            await asyncio.sleep(0.05)

    async def start(self) -> None:
        """
        socket总逻辑管理

        """
        send_task = listen_task = game_task = None
        try:
            Logger.write("Socket starts", thread = "SOCKET_MAIN")

            result = await self._connect()
            if not result:
                raise TimeoutError("Connection timeout.")
            self._connected = True
            Logger.write("Connection established.", thread = "SOCKET_MAIN")

            send_task = asyncio.create_task(self._send())
            listen_task = asyncio.create_task(self._listen())
            game_task = asyncio.create_task(self._run())

            Logger.write("All socket tasks started.", thread = "SOCKET_MAIN")
            done, pending = await asyncio.wait([send_task, listen_task, game_task],
                                         return_when = asyncio.FIRST_COMPLETED)

            if game_task in done:
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions = True)
            else:
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions = True)
                for task in done:
                    if task.exception():
                        cache_exce = cast(BaseException, task.exception())
                        raise cache_exce

        except asyncio.CancelledError as e:
            Logger.write(str(e), t = "ERROR", thread = "SOCKET_MAIN")
            raise

        except TimeoutError as e:
            Logger.write(str(e), t = "ERROR", thread = "SOCKET_MAIN")
            raise

        except Exception as e:
            Logger.write(str(e), t = "ERROR", thread = "SOCKET_MAIN")
            raise

        finally:
            if self._writer and not self._writer.is_closing():
                try:
                    self._writer.close()
                    await self._writer.wait_closed()
                except Exception:
                    pass
            self._connected = False

            Logger.write("Socket close, SOCKET_MAIN finished!", thread = "SOCKET_MAIN")
            if ISEND:
                await asyncio.sleep(20) # 20秒后关闭

async def main():
    """
    主函数
    """
    socket_main = SocketMain(ADDR)
    ui_main = UIMain(welcome_screen, socket_main)
    CARD_STK.bind(ui_main)
    socket_main.set_ui(ui_main)
    ui_task = asyncio.create_task(ui_main.start(), name = "UI")
    socket_task = asyncio.create_task(socket_main.start(), name = "Socket")

    done, pending = await asyncio.wait(
        [ui_task, socket_task],
        return_when = asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    for task in done:
        try:
            task.result()
        except Exception as e:
            Logger.write(f"Task {task.get_name} failed: {e}", t = "ERROR", thread = "Moudel/main")


# 运行路径初始化
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(application_path)

asyncio.run(main())

Logger.write("")
