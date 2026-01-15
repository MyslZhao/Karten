#include<iostream>
#include<asio.hpp>
#include<vector>
#include<string>
#include<map>
#include<algorithm>
#include<random>
#include<ctime>
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
        map<int,string>suitNames={
            {0,"♠️"},{1,"♥️"},{2,"♣️"},{3,"♦"}
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
        string  value_str=(valueNames.count(value)?valueNames.at(value):"?");
        return value_str+suit_str;
    }
    //打印牌型
    void print()const{
        cout<<getName();
    }
    //比较牌的大小
    bool  operator<(const Card& other)const{
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
    static CardType checkCardType(const vector<Card>&cards){
        if(cards.empty())return INVALID_TYPE;
        int size=cards.size();
        
        if(size==2){
            //检查王炸
            if((cards[0]==16&&cards[1]==17)||(cards[0]==17&&cards[1]==16)){
                return ROCKET;
            }
            //对子
            if(cards[0]==cards[1])return PAIR;
        }
        
        if(size==4){
            //炸弹
            int y=1;
            for(int i=1;i<3;i++){
                    if(cards[i].value!=cards[i-1].value){
                        y=0;
                        break;
                    }
            }
            if(y==1)return BOMB;
            //三带一
            vector<Card>sorted=cards;
            sort(sorted.begin(),sorted.end());
            if ((sorted[0].value == sorted[1].value && 
                 sorted[1].value == sorted[2].value) ||  // 前三张相同
                (sorted[1].value == sorted[2].value && 
                 sorted[2].value == sorted[3].value)) {  // 后三张相同
                return TREE_WITH_ONE;
            }
        

        }
        if(size==3&&cards[0].value == cards[1].value && 
            cards[1].value == cards[2].value){
                return TREE;
            }
        if(size==1){
            return SINGLE;
        }
        if(size==5){
            //三带二
            vector<Card>sorted=cards;
            sort(sorted.begin(),sorted.end());
            //AAABB  BBAAA
            if((sorted[0].value==sorted[1].value&&sorted[0].value==sorted[2].value&&sorted[3].value==sorted[4].value&&sorted[0].value!=sorted[4].value)||(sorted[0].value==sorted[1].value&&sorted[3].value==sorted[2].value&&sorted[2].value==sorted[4].value&&sorted[0].value!=sorted[4].value)){
                return TREE_WITH_TWO;
            }
            bool isStraight=true;
            for(int i=1;i<4;i++){
                if(sorted[i].value!=sorted[i-1].value+1){
                    isStraight=false;
                    break;
                }
                if(sorted[i].value>=15){
                    isStraight=false;
                    break;
                }
            }
            if(isStraight){
                return STRAIGHT;
            }
        }
        return INVALID_TYPE;
        
    }
};

int main(){
    return 0;
}