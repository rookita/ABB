from __init__ import app,scheduler
from client_config import client_config
from blockchain import call_contract, create_account, signup_account, send_transaction
from flask import redirect, request, render_template, session, flash, url_for
from models import All_Auctions,Users,Relation,db
import json,time

from auction_utils import (
    Auction,
    Create_auction,
    all_auctions,
    compute_winner,
    get_auction_info,
    get_hash,
    participate_auction,
    End_auction,
    my_auctions,
    time2sec,
    time_decoder,
    update_state
)

'''
定时触发函数,改变数据库中auction state

'''

reveal_time = 1 * 60 # 30分钟

def check_signup(username):
    return Users.query.filter_by(username = username).first() == None 

@app.route("/user/signup",methods = ['GET','POST'])
def signup():
    if request.method == 'GET':
        return render_template("signup.html",title="signup")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hash_password = get_hash(password)
        if not check_signup(username):
            #print("username already exists!")
            error =  "username already exists!"
            return error
        addr,_ = create_account(username,password) 
        user = Users(username=username,password=hash_password,address=addr)
        db.session.add(user)
        db.session.commit()
        return "success"

def is_password_right(username,password): #检查是否注册，密码是否正确
    try:
        hash_password = Users.query.filter_by(username = username).first().password
    except:
        hash_password = ""
    return get_hash(password) == hash_password

def valid_login():
    """检查登录是否合法，包括是否登录，密码是否正确
    """
    username = session.get('username',None)
    password = session.get('password',None)
    if username and password:
        return username,password
    else:
        return None
        
@app.route("/user/login",methods = ['GET','POST'])
def login():
    if request.method != 'POST':
        return render_template("login.html",title = "Login")
    username = request.form['username'] 
    password = request.form['password']
    if is_password_right(username,password):
        session['username'] = username
        session['password'] = password
        return "Login Success"   #login success
    return "Login Failed"       #ajax

@app.route("/user/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/user/info")
def user_info():
    try:
        username,_ = valid_login()
    except:
        return render_template("login.html",title="Login")
    address = Users.query.filter_by(username = username).first().address
    Created_Auctions,Win_Auctions,Participate_Auctions = my_auctions(username)
    return render_template("userinfo.html",
                           username = username,address = address,Created_Auctions=Created_Auctions,Win_Auctions=Win_Auctions,Participate_Auctions=Participate_Auctions)

@app.route("/auction/create",methods = ['GET','POST'])
def create_auction():
    """创建拍卖
    Returns:
        _type_: _description_
    """
    try:
        username,password = valid_login()
    except:
        return redirect(url_for("login"))
    #hash_password = get_hash(password)
    if request.method == 'GET':
        return render_template("create_auction.html")
    if request.method == 'POST':
        item = request.form['item']
        commit_time = request.form['commit_time']
        uint = request.form['uint']
        commit_sec = time2sec(commit_time,uint)
        
        start_reveal_time = int(time.time() + commit_sec)
        DDL = int(start_reveal_time + reveal_time)
        
        signer = signup_account(username,password)
        auction_id,auction_addr = Create_auction(username,item,start_reveal_time,DDL,signer)
        
        scheduler.add_job(id="update_state" + str(auction_id), trigger="date", run_date=time_decoder(start_reveal_time), func=update_state, args=(auction_id,"reveal"))
        scheduler.add_job(id="computer_winner" + str(auction_id), trigger="date", run_date=time_decoder(DDL), func=End_auction, args=(auction_addr,signer))
        
        this_auction = Auction(username,auction_id,auction_addr,"commit",item)
        this_auction.set_time(time_decoder(start_reveal_time),time_decoder(DDL))
        return render_template("auction_detail.html",Auction=this_auction)

@app.route("/Auctions/<int:aid>",methods=['GET'])
def auction_info(aid):
    """返回某个拍卖的详细信息

    Args:
        aid (int): 拍卖号

    Returns:
        _type_: _description_
    """
    try:
        username,_ = valid_login()
    except:
        return redirect(url_for("login"))
    this_auction = get_auction_info(aid)
    
    if username != this_auction.seller:
        is_commited = not Relation.query.filter_by(username=username,addr=this_auction.addr).first() == None
        return render_template("auction_detail.html",Auction = this_auction,buyer = True,is_commited=is_commited)    
    else:
        return render_template("auction_detail.html",Auction = this_auction,seller = True)    

@app.route("/auction/view")
def view_auctions():
    """返回所有拍卖

    Returns:
        _type_: _description_
    """
    try:
        username,_ = valid_login()
    except:
        return redirect(url_for("login"))
    Auctions = all_auctions()
    return render_template("Auctions.html",Auctions = Auctions)

@app.route("/auction/participate",methods=['POST'])
def participate():
    """参与拍卖

    Returns:
        _type_: _description_
    """
    try:
        username,_ = valid_login()
    except:
        return redirect(url_for("login"))
    
    bid = request.form.get('bid',0)
    auction_addr = request.form['addr']
    nonce = request.form['nonce']
    password = request.form['password']    
    
    if password == session.get('password',None):
        signer = signup_account(username,password)  
        res = participate_auction(username,auction_addr,nonce,bid,signer)
        if res == -1:   #state = end
            return "auction end"
        else:
            relation = Relation(username=username,addr=auction_addr,bid=int(bid))
            db.session.add(relation)
            db.session.commit()
            return "success"
    else:
        return "password wrong"

if __name__ == "__main__":
    pass
        