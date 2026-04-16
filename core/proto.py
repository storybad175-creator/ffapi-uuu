import struct
from typing import Any, Dict, List, Optional, Union
from config.fields import PROTO_FIELD_MAP
from api.errors import FFError, ErrorCode

# Protobuf Wire Types
WIRE_VARINT = 0
WIRE_LENGTH_DELIMITED = 2

class ProtobufHandler:
    @staticmethod
    def encode_varint(value: int) -> bytes:
        out = bytearray()
        while value >= 0x80:
            out.append((value & 0x7F) | 0x80)
            value >>= 7
        out.append(value & 0x7F)
        return bytes(out)

    @staticmethod
    def decode_varint(data: bytes, pos: int) -> (int, int):
        result = 0
        shift = 0
        while True:
            b = data[pos]
            result |= (b & 0x7F) << shift
            pos += 1
            if not (b & 0x80):
                return result, pos
            shift += 7

    def encode_request(self, uid: str, region: str) -> bytes:
        """Standard OB52 request structure: {1: uid_str, 2: region_str}"""
        def f(tag, wire, val):
            header = self.encode_varint((tag << 3) | wire)
            if isinstance(val, str): val = val.encode()
            return header + self.encode_varint(len(val)) + val

        # OB52 direct strategy: UID then Region
        return f(1, 2, uid) + f(2, 2, region)

    def decode_response(self, data: bytes, map_key: str = "response") -> Dict[str, Any]:
        result = {}
        pos = 0
        field_map = PROTO_FIELD_MAP.get(map_key, {})
        nested_mapping = PROTO_FIELD_MAP.get("nested_mapping", {})

        try:
            while pos < len(data):
                tag_wire, pos = self.decode_varint(data, pos)
                tag = tag_wire >> 3
                wire_type = tag_wire & 0x07
                field_name = field_map.get(tag, f"field_{tag}")

                if wire_type == WIRE_VARINT:
                    val, pos = self.decode_varint(data, pos)
                    result[field_name] = val
                elif wire_type == WIRE_LENGTH_DELIMITED:
                    length, pos = self.decode_varint(data, pos)
                    val = data[pos:pos+length]
                    pos += length

                    target_map_key = nested_mapping.get(field_name)
                    if target_map_key and target_map_key in PROTO_FIELD_MAP:
                        result[field_name] = self.decode_response(val, target_map_key)
                    else:
                        try:
                            result[field_name] = val.decode('utf-8')
                        except UnicodeDecodeError:
                            result[field_name] = val
                else:
                    # Skip unknown wires
                    pass
        except Exception as e:
            if isinstance(e, FFError):
                raise e
            raise FFError(ErrorCode.DECODE_ERROR, f"Protobuf decode failed: {str(e)}")

        return result

proto_handler = ProtobufHandler()
