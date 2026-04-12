import pytest
from ff_api.core.crypto import crypto
from ff_api.core.proto import proto_handler
from ff_api.core.decoder import decoder
from ff_api.api.schemas import PlayerData

def test_aes_round_trip(mock_settings):
    original = b"hello world 123"
    encrypted = crypto.encrypt(original)
    decrypted = crypto.decrypt(encrypted)
    assert decrypted == original

def test_proto_encode_request(mock_settings):
    encoded = proto_handler.encode_request("12345", "IND")
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

def test_rank_translation():
    from ff_api.config.ranks import RANK_MAP
    assert RANK_MAP[114] == "Platinum IV"
    assert RANK_MAP[119] == "Heroic"

def test_nested_proto_decode(mock_settings):
    # Test Strategy B recursion
    # We'll manually construct a small nested protobuf binary
    # Account info (tag 1) -> uid (tag 1), nickname (tag 2)

    def encode_varint(v):
        res = bytearray()
        while v >= 0x80:
            res.append((v & 0x7F) | 0x80)
            v >>= 7
        res.append(v & 0x7F)
        return bytes(res)

    def encode_ld(tag, data):
        header = encode_varint((tag << 3) | 2)
        return header + encode_varint(len(data)) + data

    inner = encode_ld(1, b"4899748638") + encode_ld(2, "Ƭɴɪᴛᴀᴄʜɪ".encode('utf-8'))
    outer = encode_ld(1, inner)

    decoded = proto_handler.decode_response(outer)
    assert "account_info" in decoded
    assert decoded["account_info"]["uid"] == "4899748638"
    assert decoded["account_info"]["nickname"] == "Ƭɴɪᴛᴀᴄʜɪ"

def test_missing_optional_fields(mock_player_data):
    data = PlayerData.model_validate(mock_player_data)
    assert data.account.nickname == "Ƭɴɪᴛᴀᴄʜɪ"
    assert data.pet is None
    assert data.social.guild is None
