//SPDX-License-Identifier:GPL-3.0

pragma solidity ^0.8.0;

contract Auction{

    struct User{
        address addr;
    }

    struct Seller{
        User basic_info; 
        uint256 start_reveal_time;  //开始揭露密封价格时间
        uint256 DDL;
    }
    
    struct Bidder{
        User basic_info;
        Sealed_Bid sealed_bid;                    //竞标者提交的价格，用结构体方便扩展成密封投标
        True_Bid true_bid;
        bool reveal_error;                   //记录是否价格不一致
    }

    struct Sealed_Bid{
        string nonce;
        bytes32 Hash;
    }

    struct True_Bid {
        uint256 tbid;
    }
    
    Seller seller;
    Bidder[] bidders;   //storage
    Bidder winner;
    uint256 price; 
    string item; //商品    
    uint256 deposit = 10 ether; 
    mapping(address => bool) is_commited;   //防止重复报价
    mapping(address => uint256) BidderIndexByaddr;    //storage

    modifier beforeReveal(){    //commit
        require(
            getNow() < seller.start_reveal_time * 1000,
            "time error0"
        );
        _;
    }

    modifier afterCommit(){    //commit
        require(
            getNow() > seller.start_reveal_time * 1000,
            "time error0"
        );
        _;
    }

    modifier beforeDDL(){       //ddl
        require(
            getNow() <= seller.DDL * 1000,
            "time error2"
        );
        _;
    }

    modifier afterDDL(){       //ddl
        require(
            getNow() >= seller.DDL * 1000,
            "time error2"
        );
        _;
    }

    modifier check_deposit(uint256 _deposit){
        require(
            _deposit >= deposit,
            "Deposit is not enough!"
        );
        _;
    }
    
    modifier onlyOwner() {
        require(
            msg.sender == seller.basic_info.addr,
            "Not Owner!"
        );
        _;
    }

    constructor () {
        seller.basic_info.addr = msg.sender;
    }

    function create_auction(string memory _item,uint256 start_reveal_time,uint256 DDL) public onlyOwner {
        item = _item;
        seller.start_reveal_time = start_reveal_time;
        seller.DDL = DDL;
        //payable(address(this)).transfer(deposit);     //此处向合约转的以太币实际为msg.value
    }

    function commit(Sealed_Bid memory sealed_bid) public beforeReveal {    //参数为密封的价格
        require(
            (msg.sender != seller.basic_info.addr) && (is_commited[msg.sender] == false),   //时间要求
            "commit error!"
        );

        is_commited[msg.sender] = true;

        Bidder memory tmp;

        tmp.basic_info.addr = msg.sender;
        tmp.sealed_bid = sealed_bid;
        tmp.reveal_error = true;
        bidders.push(tmp);
        BidderIndexByaddr[msg.sender] = bidders.length - 1;
        //payable(address(this)).transfer(deposit);
    }

    function validate(Sealed_Bid memory sealed_bid , True_Bid memory true_bid) internal pure returns (bool){ //验证价格
        return (hash(sealed_bid.nonce,true_bid.tbid) == sealed_bid.Hash);        
    }

    function reveal(True_Bid memory true_bid) public beforeDDL afterCommit{
        require(
            (msg.sender != seller.basic_info.addr) && (is_commited[msg.sender] == true),
            "reveal error!"
        );
        Bidder storage this_bidder = bidders[BidderIndexByaddr[msg.sender]];
        if (validate(this_bidder.sealed_bid, true_bid)){
            this_bidder.reveal_error = false;     //揭露价格出错
        }

        this_bidder.true_bid = true_bid;         //无论是否揭露错误，都记录 
    }

    function compute_winner() public onlyOwner afterDDL{

        uint256 highest = 0;
        uint i = 0;
        price = 0;
        for(i = 0; (i < bidders.length) && (bidders[i].reveal_error != true) ; i++){
            uint256 tmp = bidders[i].true_bid.tbid;
            if (tmp > highest){
                price = highest;
                highest = tmp;
                winner = bidders[i];
            }
        }
    }

    /*
    function return_deposit() public {
        uint i = 0;
        for(i = 0;i < bidders.length;i++){
            payable(bidders[i].basic_info.addr).transfer(deposit);  //参与者押金
        }

        payable(seller.basic_info.addr).transfer(deposit);     //发起者押金
    }
    */

    function queryAllBidders() public view returns (Bidder[] memory){
        return bidders;
    }

    function queryBidderByaddr() public view returns (Bidder memory){
        return bidders[BidderIndexByaddr[msg.sender]];         
    }

    function querySeller() public view returns (Seller memory){
        return seller;
    }

    function queryItem() public view returns (string memory){
        return item;
    }

    function queryContractBalance() public view returns (uint256){
        return address(this).balance;
    }

    function queryBalanceOfContract() public view returns (uint256) {
        return (address(this).balance/1e18);
    }

    function queryResult() public view returns (Bidder memory, uint256){
        return (winner,price);
    }
    
    function intToBytes(uint256 x) internal pure  returns (bytes memory b) {
        b = new bytes(32);
        assembly { mstore(add(b, 32), x) }
    }

    function hash(string memory s,uint256 bid) public pure returns (bytes32){
        return sha256(bytes.concat(bytes(s),intToBytes(bid)));
    }
    
    function getNow() public view returns (uint256) {
        return block.timestamp;
    }

    /*
    receive() external payable check_deposit(msg.value){
        //emit Recieved_deposit(msg.sender,msg.value);
    }
    */
    
}

