from subprocess import call
from blockchain import deploy_contract,signup_account,call_contract,send_transaction,create_account,init
from auction_utils import (
    commit,
    get_hash,
    reveal
)
import time

#signer_A发起拍卖，B，C，D参与
def Test(item = "item for test"):
    signer_A = signup_account("A","123456")
    signer_B = signup_account("B","123456")
    signer_C = signup_account("C","123456")
    signer_D = signup_account("D","123456")
    
    auction_name = "Auction"
    nonce = "nonce"
    #创建拍卖nce
    auction_addr = deploy_contract(auction_name,True,signer_A)
    #auction_addr = "0x0a3545be185451b1b49a9bb537963eba0822589a"
    print("auction address:",auction_addr)
    
    send_transaction(auction_addr,auction_name,"create_auction",[item,int(time.time())+60,int(time.time())+60+60],signer_A)
    
    commit(auction_addr,nonce,100,signer_B)
    commit(auction_addr,nonce,200,signer_C)
    commit(auction_addr,nonce,300,signer_D)
    
    time.sleep(60)
    
    reveal(auction_addr,100,signer_B)
    reveal(auction_addr,200,signer_C)
    reveal(auction_addr,300,signer_D)
    """
    #commit
    send_transaction(auction_addr,auction_name,"commit",[[200]],signer_B)
    send_transaction(auction_addr,auction_name,"commit",[[300]],signer_C)
    send_transaction(auction_addr,auction_name,"commit",[[400]],signer_D)
    
    #reveal
    send_transaction(auction_addr,auction_name,"reveal",[[200]],signer_B)
    send_transaction(auction_addr,auction_name,"reveal",[[300]],signer_C)
    send_transaction(auction_addr,auction_name,"reveal",[[600]],signer_D)
    """
    
    #查看所有参与者
    Bidders = call_contract(auction_addr,auction_name,"queryAllBidders",signer = signer_A)
    print(Bidders)
    
    #计算赢家
    send_transaction(auction_addr,auction_name,"compute_winner",signer = signer_A)
    winner,price = call_contract(auction_addr,auction_name,"queryResult",signer = signer_A)
    print(winner,price)
    
if __name__ == "__main__":
    Test()
