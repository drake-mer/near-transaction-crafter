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


def test_simple_craft(client, signer):
    response = client.post(
        "/craft",
        json={
            "sender": "davidkremer.testnet",
            "action": {
                "receiver": "maximilien.testnet",
                "amount": f"{10**20}",
            },
        },
    )
    assert response.status_code == 200
    raw_tx = response.json()
    assert isinstance(raw_tx, str)


def test_offline_signature(client, signer):
    response = client.post(
        "/craft",
        json={
            "sender": "davidkremer.testnet",
            "action": {
                "receiver": "maximilien.testnet",
                "amount": f"{10**20}",
            },
        },
    )
    raw_tx = response.json()
    signature = signer.sign(hashlib.sha256(bytes.fromhex(raw_tx)).digest()).hex()
    # encoded_signature = Signature()
    # encoded_signature.keyType = 0
    # encoded_signature.data = signature
    # raw_signature = BinarySerializer(tx_schema).serialize(encoded_signature).hex()
    response = client.post("/broadcast", json={"raw": raw_tx, "signature": signature})
    assert response.status_code == 200


def test_simple_sign_and_broadcast(client, signer):
    broadcast = client.post(
        "/sign",
        json={
            "sender": "davidkremer.testnet",
            "action": {
                "receiver": "maximilien.testnet",
                "amount": f"{10**20}",
            },
        },
    )
    assert broadcast.status_code == 200
