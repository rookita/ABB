from re import A
from subprocess import call
from typing import Tuple
from blockchain import deploy_contract,signup_account,call_contract,send_transaction,create_account
from models import All_Auctions,Users,Relation,db
import hashlib,time,random
from __init__ import scheduler

contract_name = "Auction"

class Auction:
    def __init__(self,seller,auction_id,auction_addr,state,item):
        self.seller = seller
        self.aid = auction_id
        self.addr = auction_addr
        self.state = state
        self.item = item

    def set_winner_price(self,winner,price):
        self.winner = winner
        self.price = price
    
    def set_time(self,start_reveal_time,DDL):
        self.start_reveal_time = start_reveal_time
        self.DDL = DDL        

def Create_auction(username,item,start_reveal_time,DDL,signer): 
    auction_addr = deploy_contract("Auction",False,signer)   #"str"
    send_transaction(auction_addr,contract_name,"create_auction",[item,int(start_reveal_time),int(DDL)],signer)
    
    auction_id = int(open("current_auction_id","r").read().strip())
    auction_id += 1 
    open("current_auction_id","w").write(str(auction_id))
    
    #存入文件中
    auction = All_Auctions(
        seller=username,aid=auction_id,addr=auction_addr,state="commit",item=item,start_reveal_time=int(start_reveal_time),DDL=int(DDL))
    db.session.add(auction)
    db.session.commit()
    
    return auction_id,auction_addr

def End_auction(auction_addr,signer) :
    result = compute_winner(auction_addr,signer)
    winner = result[0][0][0].lower()    #地址
    winner = Users.query.filter_by(address=winner).first().username
    price = int(result[1])
    #在All_Auctions中修改状态
    tmp = All_Auctions.query.filter_by(addr = auction_addr).first()
    tmp.state = "end"
    tmp.winner = winner
    tmp.price = price
    db.session.commit()
    
    return result #(tuple)
    
def get_auction_addr(auction_id) -> str:
    return All_Auctions.query.filter(aid = auction_id).first().addr

def get_auction_info(auction_id):
    line = All_Auctions.query.filter_by(aid = auction_id).first()
    seller,auction_addr,state,item,start_reveal_time,DDL,winner,price = line.seller,line.addr,line.state,line.item,line.start_reveal_time,line.DDL,line.winner,line.price
    this_auction = Auction(seller,auction_id,auction_addr,state,item)
    this_auction.set_winner_price(winner,price)
    this_auction.set_time(time_decoder(start_reveal_time),time_decoder(DDL))
    return this_auction

def get_hash(str) -> str:
    #"123" -> a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3
    return hashlib.sha256(str.encode()).hexdigest() 

def commit(auction_addr,nonce,bid,signer):
    Hash = "0x" + hashlib.sha256(nonce.encode() + int(bid).to_bytes(32,'big')).hexdigest()
    send_transaction(auction_addr,contract_name,"commit",([[nonce,Hash]]),signer = signer)
    
def reveal(auction_addr,reveal_bid,signer):
    
    send_transaction(auction_addr,contract_name,"reveal",([[int(reveal_bid)]]),signer = signer)
    
def participate_auction(username,auction_addr,nonce,bid,signer):
    line = All_Auctions.query.filter_by(addr = auction_addr).first()
    aid,state,start_reveal_time,DDL = line.aid,line.state,line.start_reveal_time,line.DDL
    if state == "commit":
        commit(auction_addr,nonce,bid,signer)
        run_date = time_decoder(random.randint(start_reveal_time,DDL))
        scheduler.add_job(id=username+"reveal"+str(aid),trigger="date",func=reveal,run_date=run_date,args=(auction_addr,bid,signer))
    if state == "end":
        return -1
    
def compute_winner(auction_addr,signer):
    send_transaction(auction_addr,contract_name,"compute_winner",signer=signer)
    result = call_contract(auction_addr,contract_name,"queryResult",signer=signer)
    return result

def my_auctions(username):
    created_auctions = All_Auctions.query.filter_by(seller = username).all() #list
    win_auctions = All_Auctions.query.filter_by(winner = username).all()
    part_auctions = Relation.query.filter_by(username=username).all()
    Created_Auctions = []
    Win_Auctions = []
    Participate_Auctions = []
    
    for x in part_auctions:
        auction = All_Auctions.query.filter_by(addr=x.addr).first()
        auction_id,item,state,addr = auction.aid,auction.item,auction.state,auction.addr
        Participate_Auctions.append(Auction(username,auction_id,addr,state,item))
        
    for auction in created_auctions:
        auction_id,item,state,addr = auction.aid,auction.item,auction.state,auction.addr
        Created_Auctions.append(Auction(username,auction_id,addr,state,item))
    
    for auction in win_auctions:
        auction_id,item,state,addr = auction.aid,auction.item,auction.state,auction.addr
        Win_Auctions.append(Auction(username,auction_id,addr,state,item))
    return Created_Auctions,Win_Auctions,Participate_Auctions

def all_auctions():
    tmp = All_Auctions.query.all()
    Auctions = []
    for auction in tmp:
        Auctions.append(Auction(auction.seller,auction.aid,auction.addr,auction.state,auction.item))
    return Auctions

def update_state(auction_id,state):
    auction = All_Auctions.query.filter_by(aid=auction_id).first()
    auction.state = state
    db.session.commit()

# 获取现在时间的时间戳
def get_time_now():
    human_time = time_encoder(
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    )
    return human_time


# 解析str时间 生成时间戳
def time_encoder(_time):
    time_array = time.strptime(_time, "%Y-%m-%d %H:%M:%S")
    timestamp = int(time.mktime(time_array))
    return timestamp


# 转为str时间
def time_decoder(time_stamp):
    time_array = time.localtime(time_stamp)
    other_style_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
    return other_style_time

#将时间转换为秒 
def time2sec(time,uint):
    if uint == "sec":
        return int(time)
    if uint == "min":
        return int(time) * 60
    if uint == "hou":
        return int(time) * 3600
    if uint == "day":
        return int(time) * 3600 * 24