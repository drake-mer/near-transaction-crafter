import dataclasses
from decimal import Decimal
from typing import Any, Tuple, Union

import base58
import pydantic
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from near_api.providers import JsonProvider
from near_api.serializer import BinarySerializer
from near_api.transactions import (
    Action,
    PublicKey,
    Transaction,
    Transfer,
    create_function_call_action,
    create_transfer_action,
    sign_and_serialize_transaction,
    tx_schema,
)
from pydantic import BaseModel
from structlog import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="", tags=["transactions"])

MAINNET_PROVIDER = "https://rpc.mainnet.near.org"
TESTNET_PROVIDER = "https://rpc.testnet.near.org"

PROVIDER = TESTNET_PROVIDER
provider = JsonProvider(PROVIDER)


class TransferIntent(BaseModel):
    receiver: str
    amount: int


class ContractCallIntent(BaseModel):
    receiver: str
    function: str
    arguments: list
    amount: int


class NearTransaction(BaseModel):
    sender: str
    action: Union[TransferIntent, ContractCallIntent]


class SignedTransaction(BaseModel):
    raw: str
    signature: str


def create_action(tx: NearTransaction):
    if isinstance(tx.action, TransferIntent):
        to_do = create_transfer_action(tx.action.amount)
    elif isinstance(tx.action, ContractCallIntent):
        to_do = create_function_call_action(
            tx.action.function,
            tx.action.arguments,
            100000000000000000,
            tx.action.amount,
        )
    else:
        raise NotImplementedError()
    return to_do


class TxDynamicParameters(BaseModel):
    account: Any
    pub_key: str
    block_hash: str
    nonce: int
    gas_price: int


def get_tx_info(sender) -> TxDynamicParameters:
    account = provider.get_account(sender, finality="final")
    block = provider.json_rpc("block", {"finality": "final"})["header"]
    access_key = provider.get_access_key_list(sender, finality="final")
    logger.info("access key", access_keys=access_key)
    key_list = access_key["keys"]
    first_key, *args = key_list
    block_hash = access_key["block_hash"]
    gas_price = block["gas_price"]
    return TxDynamicParameters(
        account=account,
        pub_key=first_key["public_key"],
        block_hash=block_hash,
        nonce=first_key["access_key"]["nonce"],
        gas_price=int(gas_price),
    )


tx_dynamic = get_tx_info("davidkremer.testnet")
logger.info("sender infos", **tx_dynamic.dict())


def serialize_tx(tx: NearTransaction) -> bytes:
    tx_infos: TxDynamicParameters = get_tx_info(tx.sender)
    new_tx = Transaction()
    new_tx.signerId = tx.sender
    new_tx.publicKey = PublicKey()
    new_tx.publicKey.keyType = 0
    new_tx.publicKey.data = base58.b58decode(tx_infos.pub_key.removeprefix("ed25519:"))
    new_tx.nonce = tx_infos.nonce
    new_tx.receiverId = tx.action.receiver
    new_tx.actions = [create_action(tx)]
    new_tx.blockHash = base58.b58decode(tx_infos.block_hash)
    msg = BinarySerializer(tx_schema).serialize(new_tx)
    return msg


craft_raw_send_tx = pydantic.parse_obj_as(
    NearTransaction,
    {
        "sender": "davidkremer.testnet",
        "action": {
            "receiver": "maximilien.testnet",
            "amount": "1000000",
        },
    },
)


craft_get_all_shop_pos = pydantic.parse_obj_as(
    NearTransaction,
    {
        "sender": "davidkremer.testnet",
        "action": {
            "receiver": "maximilien.testnet",
            "amount": "100000000000000000000000",
            "function": "get_all_shop_pos",
            "arguments": [],
        },
    },
)


logger.info("raw send", raw=serialize_tx(craft_raw_send_tx).hex())
logger.info("raw contract interaction", raw=serialize_tx(craft_get_all_shop_pos).hex())


@router.post("/craft", response_model=str, summary="Craft raw transaction")
def craft_raw_transaction(tx: NearTransaction) -> str:
    logger.info("tx", **tx.dict())
    return serialize_tx(tx).hex()


@router.post("/broadcast", response_model=str, summary="Broadcast a signed tx")
def broadcast_signed_transaction(tx: SignedTransaction):
    raise NotImplementedError()
