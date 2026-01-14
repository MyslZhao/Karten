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
    int a;
};


int main(){
    return 0;
}