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
from CardsIdentifier import *
from socket import IPPROTO_TCP, TCP_NODELAY, SOL_SOCKET, SO_KEEPALIVE
from UIComponent import *
from Logger import logger
from typing import Tuple, Callable, Optional
import os, sys, pygame, asyncio
# -*- encoding: utf-8 -*-

# TODO: interface with server
# TODO: design the game_surface

ID = 0
IDENTITY = 0
CARD_QUEUE : List[Optional[Tuple[int, int]]] = []
LORD_QUEUE : List[Optional[Tuple[int, int]]] = []

# 运行路径初始化
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(application_path)

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

'''
def game_screen(surface: pygame.Surface, sk_main: "SocketMain") -> None:
    """
    游戏界面（使用增强版CardImageObject）

    :param surface: pygame主窗口
    :type surface: pygame.Surface
    """
    global UI_MAIN, RUNNING, CARD_QUEUE

    logger("Rendering game_screen.", t="TRACE", thread="game_screen/self._surfunc")

    # 加载游戏背景
    game_bg = pygame.image.load("src\\bg\\game_bg.jpg")
    surface.blit(game_bg, (0, 0))

    # 等待接收卡牌队列
    if not CARD_QUEUE:
        # 显示等待信息
        waiting_text = LABELFACTORY.construct(
            Text("等待发牌...", "src\\fonts\\MicrosoftYaHei.ttf", 36),
            (500, 300),
            (280, 50),
            bg_apparent=True
        )
        waiting_text.run(surface)
        return

    logger(f"收到卡牌队列: {CARD_QUEUE}", t="INFO", thread="game_screen")

    # 创建卡牌对象
    card_objects = []
    image_factory = CardImageObjectFactory()

    def card_clicked_job(card_obj: InteractorArea) -> None:
        """
        卡牌点击事件处理函数
        """
        if isinstance(card_obj, CardImageObject):
            # 交替移动卡牌
            card_obj.move_alternating(50)
            logger(f"卡牌 {card_obj.id} 被点击", t="TRACE", thread="game_screen")

            # 可以在这里添加游戏逻辑，比如选择要出的牌

    # 创建并显示卡牌
    for i, card_type in enumerate(CARD_QUEUE):
        # 计算卡牌位置（在屏幕底部水平排列）
        pos_x = 200 + i * 100  # 起始位置200，每个卡牌间隔100像素
        pos_y = 500  # 屏幕底部

        card_obj = image_factory.construct(card_type, Coord(pos_x, pos_y))
        if card_obj:
            card_obj.bind(card_clicked_job)
            card_obj.run(surface)
            card_objects.append(card_obj)

    # 显示玩家信息
    player_info = LABELFACTORY.construct(
        Text(f"玩家 {ID} 的手牌", "src\\fonts\\MicrosoftYaHei.ttf", 24),
        (50, 450),
        (200, 40),
        bg_apparent=True
    )
    player_info.run(surface)

    # 显示操作提示
    hint_text = LABELFACTORY.construct(
        Text("点击卡牌可选择/取消选择，选中的卡牌会向上移动", "src\\fonts\\MicrosoftYaHei.ttf", 18),
        (300, 650),
        (680, 30),
        bg_apparent=True
    )
    hint_text.run(surface)
'''

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
                        logger("Client quit.", t = "TRACE", thread = "UI_MAIN")
                        RUNNING = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            logger("Client quit.", t = "TRACE", thread = "UI_MAIN")
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
            logger(f"Exception occurred: {e}", t = "ERROR", thread = "UI_MAIN")
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
        self._running = True
        self._reader : Optional[asyncio.StreamReader] = None
        self._writer : Optional[asyncio.StreamWriter] = None
        self._connected : bool = False

    @property
    def isalive(self) -> bool:
        return self._running

    async def _connect(self, timeout: float = 5.0) -> bool:
        """
        异步连接
        """
        logger("Start connect tasks.", thread="lambda/self._connect")

        try:
            logger("Connecting...", thread="lambda/self._connect")
            self._read, self._writer = await asyncio.wait_for(
                asyncio.open_connection(
                    host = self._addr[0],
                    port = self._addr[1]
                    ),
                timeout = timeout
            )

            peername = self._writer.get_extra_info('peername')
            if peername:
                logger(f'Connection ready, server at {peername}', thread = 'lambda/self._connect')

            sock = self._writer.get_extra_info('socket')
            if sock:
                sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1) # 禁用Nagle
                sock.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1) # 启用保活

            return True

        except (ConnectionError, OSError, asyncio.TimeoutError) as e:
            logger(f"Connection failed: {e}", thread="lambda/self._connect")
            if self._writer:
                try:
                    self._writer.close()
                    await self._writer.wait_closed()
                except :
                    pass
                finally:
                    self._writer = None
                    self._reader = None
            return False

        except Exception as e:
            logger(f"Unexpected error during connection: {e}",
                   t="ERROR",
                   thread="lambda/self._connect")

            if self._writer:
                try:
                    self._writer.close()
                except:
                    pass
                self._writer = None
                self._reader = None
            return False

    async def _send(self) -> None:
        """
        发送协程

        """
        logger("Send tasks loops.", thread = "send_task/self._send")

        while self._running:
            try:
                msg = await self._sendmsg.get()
                logger(f"Message '{msg}' ready to be sent.", t = "TRACE", thread = "send_task/self._send")

                if self._writer and not self._writer.is_closing():
                    self._writer.write(msg.encode('utf-8'))
                    await self._writer.drain()
                    logger(f"Message {msg} has been sent.", t = "TRACE", thread = "send_task/self._send")
                else:
                    logger(f'Writer failed, plz check the status of self._writer.', t = "WARN", thread = "send_task/self._send")

                self._sendmsg.task_done()

            except (ConnectionError, OSError, BrokenPipeError) as e:
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
        logger("Listen task loops", thread = "listen_task/self._listen")

        while self._running:
            try:
                data = b''
                if self._reader:
                    data = await self._reader.readuntil(b'\n')

                msg = data.decode("utf-8").strip()

                if msg == "":
                    await asyncio.sleep(0.1)
                    continue
                logger(f'msg : "{msg}" received', t = "TRACE", thread = "listen_task/self._listen")

                await self._listenmsg.put(msg)

            except (asyncio.IncompleteReadError, ConnectionError, OSError) as e:
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
        await self._sendmsg.put(str(self.id) + " " + msg + '\n')

    async def alive(self):
        """
        管理listen_thread和send_thread生命周期的函数
        交由lifemanager_thread管理

        """
        global RUNNING
        logger("life manager task starts.", thread = "life_task/self.alive")
        while self._running:
            await asyncio.sleep(0.1)

            if not RUNNING:
                logger("Stop RUNNING!", t = "TRACE", thread = "life_task/self.alive")
                self._running = False
                break

    async def _run(self) -> None:
        """
        客户端游戏逻辑的socket线程 待完善

        """
        global CARD_QUEUE, LORD_QUEUE, IDENTITY, ID
        logger("Game task starts.", thread = "game_task/self._run")

        connect_status = await self.recv() # <- server.server._handle_client
        if connect_status == "":
            logger("Connection timeout.", t = "WARN", thread = "game_task/self._run")
            return
        if connect_status == "f":
            logger("Connection already full.", t = "WARN", thread = "game_task/self._run")
            return
        ID = int(connect_status)
        self.id = connect_status
        logger(f"Connected successfully, id is {id}.", thread = "game_task/self._run")

        ifbegin = await self.recv() # <- server.server._game_run

        if ifbegin:
            if ifbegin != "b":return

        logger("Game started.", t = "TRACE", thread = "game_task/self._run")
        UI_MAIN.switch_surfunc(game_screen)

        LORD_QUEUE = eval(await self.recv()) # <- server.server._client_run(1)
        IDENTITY = eval(await self.recv()) # <- serevr.Server._client_run
        CARD_QUEUE = eval(await self.recv()) # <- server.server._client_run(2)


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
            life_task = asyncio.create_task(self.alive())

            logger("All socket tasks started.", thread = "SOCKET_MAIN")
            await asyncio.gather(send_task, listen_task, life_task, game_task)

        except asyncio.CancelledError as e:
            logger(str(e), t = "ERROR", thread = "SOCKET_MAIN")

            self._running = False
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
            self._running = False
            logger(str(e), t = "ERROR", thread = "SOCKET_MAIN")

        finally:
            if self._writer and not self._writer.is_closing():
                try:
                    self._writer.close()
                except:
                    pass

            self.close()
            logger("Socket close, SOCKET_MAIN finished!", thread = "SOCKET_MAIN")

    def close(self) -> None:
        """
        关闭连接

        """
        global RUNNING
        RUNNING = False


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