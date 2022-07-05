import hashlib

import pytest
from fastapi.testclient import TestClient
from near_api.signer import KeyPair, Signer

from near.app import app


@pytest.fixture
def signer():
    return Signer(
        "davidkremer.testnet",
        KeyPair(
            "ed25519:6U5SHsVto7agV5kx4nmfAQfH8ThoBXTnSrNXKT"
            "e1dp7RAiGvafimFn553aeSKiKKnT4iMA39iJWxzhPk6fQsKdB"
        ),
    )


@pytest.fixture(scope="session")
def client():
    yield TestClient(app)


payload_list = [
    {
        "sender": "davidkremer.testnet",
        "action": {"receiver": "maximilien.testnet", "amount": "100000000000000000000"},
    },
    {
        "sender": "davidkremer.testnet",
        "action": {
            "receiver": "maximilien.testnet",
            "amount": "10000000000000",
            "function": "get_all_shop_pos",
            "arguments": [],
        },
    },
]


@pytest.mark.parametrize("crafting_payload", payload_list)
def test_simple_craft(client, signer, crafting_payload):
    response = client.post(
        "/craft",
        json=crafting_payload,
    )
    assert response.status_code == 200
    raw_tx = response.json()
    assert isinstance(raw_tx, str)


@pytest.mark.parametrize("crafting_payload", payload_list)
def test_offline_signature(client, signer, crafting_payload):
    response = client.post(
        "/craft",
        json=crafting_payload,
    )
    raw_tx = response.json()
    signature = signer.sign(hashlib.sha256(bytes.fromhex(raw_tx)).digest()).hex()
    response = client.post("/broadcast", json={"raw": raw_tx, "signature": signature})
    assert response.status_code == 200


@pytest.mark.parametrize("crafting_payload", payload_list)
def test_simple_sign_and_broadcast(client, signer, crafting_payload):
    broadcast = client.post(
        "/sign",
        json=crafting_payload,
    )
    assert broadcast.status_code == 200
