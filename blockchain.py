from enum import unique
from subprocess import call
import sys
import os
import json
from typing import Dict, Any, List, Union
import traceback
import re

from models import db

sys.path.append("/home/ubuntu/python-sdk")
sys.path.append("/home/ubuntu/evoting/avec")
from client.bcosclient import BcosClient
from client.bcoserror import BcosError, BcosException
from client.contractnote import ContractNote
from client.datatype_parser import DatatypeParser
from client.common.compiler import Compiler
from eth_utils import address, to_checksum_address
from client.signer_impl import Signer_ECDSA, Signer_Impl
from eth_account.account import Account
from client_config import client_config
from __init__ import app

contract_list = ["Auction"]

# 生成区块链账户 写入.keystore文件存储信息
def create_account(name, password=""):
    ac = Account.create(password)
    kf = Account.encrypt(ac.privateKey, password)
    keyfile = "{}/{}.keystore".format(client_config.account_keyfile_path, name)

    with open(keyfile, "w") as dump_f:
        json.dump(kf, dump_f)
        dump_f.close()

    return ac.address,signup_account(name, password)


# signer 用于判断发起交易方
def signup_account(username, password) -> Union[Signer_Impl, None]:
    try:
        signer = Signer_ECDSA.from_key_file(
            f"{client_config.account_keyfile_path}/{username}.keystore", password
        )
    except:
        return None
    return signer

def compile_and_abis(compile: bool = True):
    """
    Compiles all contracts and generates abi and bin files
    """
    global abis, dp
    for c in contract_list:
        if compile:
            Compiler.compile_file(f"contracts/{c}.sol", output_path="contracts")
        # data_parser = DatatypeParser()
        # data_parser.load_abi_file(f"contracts/{c}.abi")
        # abis[c] = data_parser.contract_abi
        # dp[c] = data_parser


# 部署合约返回合约地址
def deploy_contract(
    contract, compile: bool = False, signer: Signer_Impl = None, fn_args=None
):
    """
    Args:
        contract: the contract's name, e.g.: "EngineerList"
        compile (bool): compile or not
    Returns:
        the contract address
    """
    if compile and (
        os.path.isfile(client_config.solc_path)
        or os.path.isfile(client_config.solcjs_path)
    ):
        Compiler.compile_file(f"contracts/{contract}.sol", output_path="contracts")

    data_parser = DatatypeParser()
    data_parser.load_abi_file(f"contracts/{contract}.abi")

    client = BcosClient()
    try:
        with open(f"contracts/{contract}.bin", "r") as load_f:
            contract_bin = load_f.read()
            load_f.close()
        result = client.deploy(
            contract_bin,
            contract_abi=data_parser.contract_abi,
            fn_args=fn_args,
            from_account_signer=signer,
        )
        addr = result["contractAddress"]
    except BcosError as e:
        traceback.print_exc()
        return None
    except BcosException as e:
        traceback.print_exc()
        return None
    except Exception as e:
        traceback.print_exc()
        return None
    finally:
        client.finish()
    app.logger.info(f"deploy contract {contract} at {addr}")
    return addr


# 调用合约
def call_contract(
    contract_addr: str, #合约地址
    contract_name: str, #合约名字
    fn_name: str,       #函数名
    args: List = None,  #参数
    signer = None, 
):
    client = BcosClient()
    if signer is not None:
        client.default_from_account_signer = signer

    data_parser: DatatypeParser = DatatypeParser()
    data_parser.load_abi_file(f"contracts/{contract_name}.abi")
    contract_abi = data_parser.contract_abi

    ret = client.call(contract_addr, contract_abi, fn_name, args)
    app.logger.info(
        f"call contract {contract_name} at {contract_addr}. {fn_name} ({args}) -> {ret}"
    )
    client.finish()
    return ret

def send_transaction(
    contract_addr: str,
    contract_name: str,
    fn_name: str,
    args: List = None,
    signer: Signer_Impl = None,
    gasPrice=30000000,
):
    global abis, dp
    client = BcosClient()

    # contract_abi = abis[contract_name]
    data_parser: DatatypeParser = DatatypeParser()
    data_parser.load_abi_file(f"contracts/{contract_name}.abi")
    contract_abi = data_parser.contract_abi

    receipt = client.sendRawTransactionGetReceipt(
        to_address=contract_addr,
        contract_abi=contract_abi,
        fn_name=fn_name,
        args=args,
        from_account_signer=signer,
        gasPrice=gasPrice,
    )

    if receipt["status"] != "0x0":
        msg = receipt.get("statusMsg", "")
        app.logger.warn(
            f"call contract {contract_name} at {contract_addr}. {fn_name} ({args}) error:{msg}"
        )
        app.logger.warn(f"receipt: {receipt}")
        print(msg)
        raise Exception(f"contract error: {msg}")
    txhash = receipt["transactionHash"]
    txresponse = client.getTransactionByHash(txhash)
    try:
        inputresult = data_parser.parse_transaction_input(txresponse["input"])
        outputresult = data_parser.parse_receipt_output(
            inputresult["name"], receipt["output"]
        )
    except:
        outputresult = "0x0"
    client.finish()
    app.logger.info(
        f"call contract {contract_name} at {contract_addr}. {fn_name} ({args}) -> {outputresult}"
    )
    return outputresult


def init():
    app.logger.warn("clean databases")
    db.drop_all()
    db.create_all()
    app.logger.warn("compile all contracts")
    compile_and_abis(compile=True)
    # for contract_name in contract_list:
    #     addr =deploy_contract(contract_name)
    #     contract = Contract(name=contract_name,addr = addr)
    #     db.session.add(contract)
    #     db.session.commit()
    #     # create_account("test")
    '''
    management_addr = deploy_contract("Management")
    contract = Contract(name="Management", addr=management_addr)
    db.session.add(contract)
    db.session.commit()
    '''

if __name__ == "__main__":
    init()
    