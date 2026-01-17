#include<iostream>
#include<vector>
#include<string>
#include<map>
#include<algorithm>
#include<random>
#include<ctime>
#include<chrono>
#include<memory>
#include<functional>
#include<queue>
#include<sstream>
#include<atomic>
#define ASIO_STANDALONE
#include<asio.hpp>

using namespace std;
//=============================================================
#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <algorithm>
#include <random>
#include <ctime>
#include <chrono>
#include <memory>
#include <functional>
#include <queue>
#include <sstream>
#include <atomic>
#define ASIO_STANDALONE
#include <asio.hpp>
// -*- encoding : gtk -*-
using namespace std;
//=============================================================
//基础数据结构
//=============================================================
//牌类
class Card{
public:
    int suit; //花色   0:黑桃, 1:红心, 2:梅花, 3:方块
    int value; //点数
    int id;   //唯一标识
    int weight; //权重  用于比大小
    Card(int card_id=0):id(card_id){
        if(id<0||id>53){
            cout<<"错误！"<<endl;
            return;
        }
        if(id==52){
            //小王
            suit=0;//花色只有黑桃
            value=16;
            weight =16;
        }
        else if(id==53){
            //大王
            suit=0;
            value=17;
            weight =17;
        }
        else{
            //普通牌
            suit=id/13;
            value=3+(id%13);
            weight =value;
        }
    }
    string getName()const{
        //花色和名字
        map<int,string> suitNames={
            {0,"??"},{1,"??"},{2,"??"},{3,"?"}
        };
        // 点数名字
        map<int, string> valueNames = {
            {3, "3"}, {4, "4"}, {5, "5"}, {6, "6"},
            {7, "7"}, {8, "8"}, {9, "9"}, {10, "10"},
            {11, "J"}, {12, "Q"}, {13, "K"}, {14, "A"},
            {15, "2"}, {16, "小王"}, {17, "大王"}
        };
        if(value>=16){
            return valueNames.at(value);
        }
        //其他：点数+花色
        string suit_str=(suitNames.count(suit)?suitNames.at(suit):"?");
        string value_str=(valueNames.count(value)?valueNames.at(value):"?");
        return value_str + suit_str;
    }
    //打印牌型
    void print()const{
        cout<<getName();
    }
    //比较牌的大小
    bool operator<(const Card& other)const{
        return weight<other.weight;
    }
    //判断牌型是否相同
    bool operator==(const Card&other)const{
        return id==other.id;
    }

};

enum CardType{
    INVALID_TYPE,   // 无效牌型invalid
    SINGLE,         // 单张single
    PAIR,           // 对子pair
    TREE,           // 三张tree
    TREE_WITH_ONE,  // 三带一
    TREE_WITH_TWO,  // 三带二
    STRAIGHT,       // 顺子 (5张或以上连续单牌)
    BOMB,           // 炸弹 (四张相同)
    ROCKET,         // 王炸 (大王+小王)
     AIRPLANE,               // 飞机不带翅膀（至少2个连续三张）
    AIRPLANE_WITH_SINGLE,   // 飞机带单翅膀
    AIRPLANE_WITH_PAIR      // 飞机带对子翅膀
};
/* 
 * 1. 判断牌型是否合法
 * 2. 判断能否压过上家的牌
 * 3. 计算牌型分数
 * 4. 其他游戏规则
*/
class GameLogic{
    public:
    //检查牌型
    static CardType checkCardType(const vector<Card>& cards){
        if(cards.empty()) return INVALID_TYPE;
        int n = (int)cards.size();
        vector<Card> sorted = cards;
        sort(sorted.begin(), sorted.end());

        // 统计点数出现次数
        map<int,int> cnt;
        for(const auto &c: sorted) cnt[c.value]++;

        if(n == 1) return SINGLE;

        if(n == 2){
            // 王炸
            if((sorted[0].value == 16 && sorted[1].value == 17) ||
               (sorted[0].value == 17 && sorted[1].value == 16)) return ROCKET;
            if(sorted[0].value == sorted[1].value) return PAIR;
            return INVALID_TYPE;
        }

        if(n == 3){
            if(cnt.size() == 1) return TREE;
            return INVALID_TYPE;
        }

        if(n == 4){
            // 炸弹：四张相同
            for(auto &p: cnt) if(p.second == 4) return BOMB;
            // 三带一
            for(auto &p: cnt) if(p.second == 3) return TREE_WITH_ONE;
            return INVALID_TYPE;
        }

        if(n == 5){
            // 三带二
            bool has3 = false, has2 = false;
            for(auto &p: cnt){
                if(p.second == 3) has3 = true;
                if(p.second == 2) has2 = true;
            }
            if(has3 && has2) return TREE_WITH_TWO;

            // 顺子（5张连续，不包含2或王）
            if(cnt.size() == 5){
                if(sorted.back().value >= 15) return INVALID_TYPE; // 不能包含2或王
                bool ok = true;
                for(int i=1;i<n;i++){
                    if(sorted[i].value != sorted[i-1].value + 1) { ok = false; break; }
                }
                if(ok) return STRAIGHT;
            }
            return INVALID_TYPE;
        }

        // n >= 6：目前只支持顺子（至少5张连续单牌）
        if(n >= 5){
            if(cnt.size() == n){
                if(sorted.back().value >= 15) return INVALID_TYPE;
                for(int i=1;i<n;i++){
                    if(sorted[i].value != sorted[i-1].value + 1) return INVALID_TYPE;
                }
                return STRAIGHT;
            }
            if(n==6&&sorted[0].value==sorted[1].value&&sorted[2].value==sorted[3].value&&sorted[4].value==sorted[6].value){
                return AIRPLANE;
            }
            if((n==7&&sorted[0].value==sorted[1].value&&sorted[2].value==sorted[3].value&&sorted[4].value==sorted[5].value)||(
                sorted[1].value==sorted[2].value&&sorted[3].value==sorted[4].value&&sorted[5].value==sorted[6].value
            )){
                return AIRPLANE_WITH_SINGLE;
            }
             if(n==8&&sorted[0].value==sorted[1].value&&sorted[2].value==sorted[3].value&&sorted[4].value==sorted[5].value&&sorted[6].value==sorted[7].value){
                return AIRPLANE_WITH_SINGLE;
            }
            return INVALID_TYPE;
        }

        return INVALID_TYPE;
    }
    //转化成字符串
     static string getTypeName(CardType type) {
        map<CardType, string> typeNames = {
            {INVALID_TYPE, "无效牌型"},
            {SINGLE, "单张"},
            {PAIR, "对子"},
            {TREE, "三张"},
            {TREE_WITH_ONE, "三带一"},
            {TREE_WITH_TWO, "三带二"},
            {STRAIGHT, "顺子"},
            {BOMB, "炸弹"},
            {ROCKET, "王炸"},
            {AIRPLANE,"飞机"},
            {AIRPLANE_WITH_SINGLE,"飞机带单"},
             {AIRPLANE_WITH_PAIR,"飞机带双"},
        };
        return (typeNames.count(type)?typeNames.at(type):"未知牌型");
     }

/*
*检查能否出牌
*检查上家出的牌
*检查能否出牌
*/

static bool canPlayCards(const vector<Card>&lastCards,
                        const vector<Card>&currentCards){
    //检查当前牌是否合法
    CardType currentType=checkCardType(currentCards);
    if(currentType==INVALID_TYPE){
        return false;
    }
    if(lastCards.empty()){
        return true;//第一次出能出任何合法的牌
    }
    //检查上家牌牌型
    CardType lastType=checkCardType(lastCards);
    if(lastType==INVALID_TYPE){
        return false;
    }
    if(currentType==ROCKET){
        return true;

    }
    if(currentType==BOMB){
       if(lastType!=BOMB&&lastType!=ROCKET){
        return true;
       } 
    }
    //相同牌型
    if(currentType==lastType){
        if (currentType == STRAIGHT && 
            currentCards.size() != lastCards.size()) {
             return false;
        }
        //比较主牌
        int currentMain=getMainValue(currentCards,currentType);
        int lastMain=getMainValue(lastCards,lastType);
        return (currentMain>lastMain)?true:false;

    }
    return false;

}
//取主值
static int getMainValue(const vector<Card>& cards, CardType type){   
    if(cards.empty())return 0;
    vector<Card> sorted = cards;
    sort(sorted.begin(), sorted.end());
    switch(type){
    case SINGLE:
    case PAIR:
    case TREE:
    case BOMB:
        return sorted.back().weight;
    case TREE_WITH_ONE:
    case TREE_WITH_TWO:{
        map<int,int>mp;
        for(const auto &it:sorted){
            mp[it.value]++;
        }
        for(const auto &it:mp){
            if(it.second==3) return it.first;
        }
        return 0;
    }
    case STRAIGHT:
        return sorted.back().weight;
    case ROCKET:
        return 100;
    case AIRPLANE:
        return sorted[5].weight;
    case AIRPLANE_WITH_SINGLE:
        if(sorted[0].value==sorted[1].value)return sorted.back().weight;
    case AIRPLANE_WITH_PAIR:
        return sorted.back().weight;
    default:
        return 0;
    
    }
}

static void printCards(const vector<Card>& cards, const string& title = "") {
    if(!title.empty()){
        cout << title << ": ";
    }
    
    for(size_t i=0; i<cards.size(); i++){
        cards[i].print();
        if(i<cards.size()-1){
            cout << " ";
        }
    }
    
    if(!cards.empty()){
        CardType type = checkCardType(cards);
        cout << " 【" << getTypeName(type) << "】";
    }
    cout << endl;
}
static void sortCards(vector<Card>&cards){
    sort(cards.begin(),cards.end());
}

};
//====================================================================
//第三部分：游戏工具
//====================================================================
/*
发牌
*/  
class GameUtils{
    public:
    static vector<int>createDeck(){
        vector<int>deck;
        for(int i=0;i<54;i++){
            deck.push_back(i);
        }
        return deck;
    }
    //洗牌
    static void shuffledeck(vector<int>&deck){
        static std::mt19937 rng((unsigned)std::chrono::system_clock::now().time_since_epoch().count());
        std::shuffle(deck.begin(), deck.end(), rng);
    }
    static vector<vector<Card>>dealCards(){
        vector<int>deck=createDeck();
        shuffledeck(deck);
        vector<vector<Card>>result(4);//三个玩家和一个底牌
        //三个玩家
        for(int i=0;i<51;i++){
            int p=i%3;
            result[p].push_back(Card(deck[i]));
        }
        //底牌
        for(int i=51;i<54;i++){
            result[3].push_back(Card(deck[i]));
        }
        //帮玩家排序
        for(int i=0;i<4;i++){
            GameLogic::sortCards(result[i]);
        }
        return result;
    }
};     
//============================================================
//服务器实现
//============================================================
class ClientSession:public enable_shared_from_this<ClientSession>{
public:
    ClientSession(asio::ip::tcp::socket socket)
         :socket_(move(socket)),sessionId_(-1),playerId_(-1){

    }
    void start(){
        sessionId_=++sessionCounter;
        cout<<"[服务器] 新客户端连接，会话ID:"<<sessionId_<<endl;
        string welcomeMsg="欢迎连接到斗地主服务器！\n";
        welcomeMsg+="你的会话ID: " + to_string(sessionId_) + "\n";
        sendMsg(welcomeMsg);
        readMessage();
    }
    void sendMsg(const string &message){
        auto self=shared_from_this();
       asio::async_write(socket_,
            asio::buffer(message),
            [this, self](asio::error_code ec, size_t /*length*/) {
                if(ec) {
                    cout << "[会话 " << sessionId_ << "] 发送失败: " << ec.message() << endl;
                    close();
                }
            });
    }
    int getSessionId() const { return sessionId_; }
    int getPlayerId() const { return playerId_; }
    void setPlayerId(int id) { playerId_ = id; }
    void close() {
        if(socket_.is_open()) {
            cout << "[会话 " << sessionId_ << "] 关闭连接" << endl;
            socket_.close();
        }
    }
private:
    void readMessage() {
        auto self = shared_from_this();
        
        asio::async_read_until(socket_, buffer_, '\n',
            [this, self](asio::error_code ec, size_t length) {
                if(!ec) {
                    istream is(&buffer_);
                    string message;
                    getline(is, message);
                    
                    cout << "[会话 " << sessionId_ << "] 收到: " << message << endl;
                    handleMessage(message);
                    readMessage();
                } else {
                    if(ec != asio::error::eof) {
                        cout << "[会话 " << sessionId_ << "] 读取错误: " << ec.message() << endl;
                    }
                    close();
                }
            });
    }
    
    void handleMessage(const string& message) {
        // 处理游戏命令
        string response = processGameCommand(message);
        sendMsg(response);
    }
    
    string processGameCommand(const string& command) {
        // 简单的命令解析
        if(command == "HELLO") {
            return "欢迎！请创建房间或加入房间\n";
        }
        else if(command.rfind("PLAY ",0) == 0) {
            // 模拟出牌命令: PLAY 1 5 9
            vector<Card> cards;
            string cardStr = command.substr(5);
            istringstream iss(cardStr);
            int cardId;
            while(iss >> cardId) {
                cards.push_back(Card(cardId));
            }
            
            CardType type = GameLogic::checkCardType(cards);
            return string("出牌: ") + GameLogic::getTypeName(type) + "\n";
        }
        else if(command == "DEAL") {
            auto dealtCards = GameUtils::dealCards();
            string response = "发牌完成:\n";
            for(int i=0; i<3; i++) {
                response += "玩家" + to_string(i+1) + ": ";
                for(const auto& card : dealtCards[i]) {
                    response += card.getName() + " ";
                }
                response += "\n";
            }
            return response;
        }
        
        return string("未知命令: ") + command + "\n";
    }
    
private:
    asio::ip::tcp::socket socket_;
    asio::streambuf buffer_;
    int sessionId_;
    int playerId_;
    static atomic<int> sessionCounter;
};

atomic<int> ClientSession::sessionCounter{0};

class DouDiZhuServer{
   private:
    asio::io_context& io_context_;
    asio::ip::tcp::acceptor acceptor_;
    vector<shared_ptr<ClientSession>> sessions_;
    bool isRunning_;
    private:
    void startAccept() {
        acceptor_.async_accept(
            [this](asio::error_code ec, asio::ip::tcp::socket socket) {
                if(!ec) {
                    auto session = make_shared<ClientSession>(move(socket));
                    sessions_.push_back(session);
                    session->start();
                } else {
                    cout << "[服务器] 接受连接错误: " << ec.message() << endl;
                }
                
                if(isRunning_) {
                    startAccept();
                }
            });
    }
    public: DouDiZhuServer(asio::io_context& io_context, short port)
                :io_context_(io_context),
                acceptor_(io_context, asio::ip::tcp::endpoint(asio::ip::tcp::v4(), port)),
          isRunning_(false) {
        cout << "[服务器] 创建服务器，端口: " << port << endl;
    }
    void start() {
        if(isRunning_) {
            cout << "[服务器] 服务器已经在运行" << endl;
            return;
        }
        
        isRunning_ = true;
        startAccept();
        cout << "[服务器] 服务器启动成功，等待客户端连接..." << endl;
    }
    
    void stop() {
        if(!isRunning_) return;
        
        isRunning_ = false;
        acceptor_.close();
        
        for(auto& session : sessions_) {
            session->close();
        }
        sessions_.clear();
        
        cout << "[服务器] 服务器已停止" << endl;
    }
    
    string getStatus() const {
        stringstream ss;
        ss << "服务器状态:\n";
        ss << "- 运行状态: " << (isRunning_ ? "运行中" : "已停止") << "\n";
        ss << "- 当前连接数: " << sessions_.size() << "\n";
        try{
            ss << "- 监听端口: " << acceptor_.local_endpoint().port() << "\n";
        }catch(...){
        }
        return ss.str();
    }
    
    bool isRunning() const { return isRunning_; }
    
};
class ServerManager {
public:
    ServerManager() : server_(nullptr), serverThread_(nullptr) {
        cout << "[服务器管理器] 初始化" << endl;
    }
    
    ~ServerManager() {
        stopServer();
    }
    
    void startServer(short port = 8080) {
        if(server_ && server_->isRunning()) {
            cout << "[服务器管理器] 服务器已经在运行" << endl;
            return;
        }
        
        try {
            io_context_ = make_unique<asio::io_context>();
            server_ = make_unique<DouDiZhuServer>(*io_context_, port);
            
            serverThread_ = make_unique<thread>([this]() {
                cout << "[服务器线程] 启动" << endl;
                server_->start();
                io_context_->run();
                cout << "[服务器线程] 结束" << endl;
            });
            
            cout << "[服务器管理器] 服务器启动命令已发送" << endl;
            
        } catch(const exception& e) {
            cerr << "[服务器管理器] 启动失败: " << e.what() << endl;
        }
    }
    
    void stopServer() {
        if(server_) {
            server_->stop();
        }
        
        if(io_context_) {
            io_context_->stop();
        }
        
        if(serverThread_ && serverThread_->joinable()) {
            serverThread_->join();
            serverThread_.reset();
        }
        
        server_.reset();
        io_context_.reset();
        
        cout << "[服务器管理器] 服务器已停止" << endl;
    }
    
    string getStatus() const {
        if(!server_) {
            return "服务器未启动";
        }
        return server_->getStatus();
    }
    
    bool isRunning() const {
        return server_ && server_->isRunning();
    }
    
private:
    unique_ptr<asio::io_context> io_context_;
    unique_ptr<DouDiZhuServer> server_;
    unique_ptr<thread> serverThread_;
};

// ====================================================
// 第四部分：主函数
// ====================================================

ServerManager serverManager;
void showWelcome() {
    cout << "=========================================" << endl;
    cout << "      斗地主游戏逻辑与服务器系统        " << endl;
    cout << "=========================================" << endl;
    cout << endl;
    cout << "系统包含：" << endl;
    cout << "1. 游戏逻辑模块 - 处理出牌规则、牌型判断" << endl;
    cout << "2. 网络服务器模块 - 基于Asio的TCP服务器" << endl;
    cout << endl;
    cout << "编译命令：g++ -std=c++11 -pthread main.cpp -o doudizhu" << endl;
    cout << "=========================================" << endl;
}

void showMenu() {
    cout << "\n============ 斗地主系统主菜单 ============" << endl;
    cout << "1. 启动游戏服务器（端口8888）" << endl;
    cout << "2. 启动游戏服务器（自定义端口）" << endl;
    cout << "3. 停止游戏服务器" << endl;
    cout << "4. 查看服务器状态" << endl;
    cout << "5. 测试游戏逻辑" << endl;
    cout << "0. 退出程序" << endl;
    cout << "=========================================" << endl;
    cout << "请输入选项 (0-5): ";
}

void testGameLogic() {
    cout << "\n=== 游戏逻辑测试 ===" << endl;
    
    // 测试一些牌型
    vector<Card> single = {Card(0)};
    vector<Card> pair = {Card(0), Card(13)};
    vector<Card> bomb = {Card(0), Card(13), Card(26), Card(39)};
    
    cout << "测试牌型识别:" << endl;
    GameLogic::printCards(single, "单张");
    GameLogic::printCards(pair, "对子");
    GameLogic::printCards(bomb, "炸弹");
    
    // 测试发牌
    cout << "\n测试发牌功能:" << endl;
    auto cards = GameUtils::dealCards();
    for(int i=0; i<3; i++) {
        cout << "玩家" << (i+1) << " (" << cards[i].size() << "张): ";
        for(const auto& card : cards[i]) {
            card.print();
            cout << " ";
        }
        cout << endl;
    }
    
    cout << "\n游戏逻辑测试完成！" << endl;
}

//回huan地址127.0.0.1  8080  utf8编码
int main(){
    showWelcome();
    
    bool running = true;
    while(running) {
        showMenu();//看菜单
        
        int choice;
        cin >> choice;
        
        switch(choice) {
            case 0://停止游戏
                if(serverManager.isRunning()) {
                    cout << "正在停止服务器..." << endl;
                    serverManager.stopServer();
                }
                cout << "\n感谢使用，再见！" << endl;
                running = false;
                break;
                
            case 1:
                serverManager.startServer(8080);
                break;
                
            case 2: {
                short port;
                cout << "请输入端口号 (1024-65535): ";
                cin >> port;
                if(port >= 1024 && port <= 65535) {
                    serverManager.startServer(port);
                } else {
                    cout << "端口号无效！" << endl;
                }
                break;
            }
                
            case 3:
                serverManager.stopServer();
                break;
                
            case 4:
                cout << serverManager.getStatus() << endl;
                break;
                
            case 5:
                testGameLogic();
                break;
                
            default:
                cout << "无效选项，请重新输入！" << endl;
        }
        
        if(choice != 0) {
            cout << "\n按回车键继续...";
            cin.ignore();
            cin.get();
        }
    }
    
    return 0;
}