import struct
from typing import Any, Dict, List, Optional, Union
from ff_api.config.fields import PROTO_FIELD_MAP
from ff_api.api.errors import FFError, ErrorCode

# Protobuf Wire Types
WIRE_VARINT = 0
WIRE_64BIT = 1
WIRE_LENGTH_DELIMITED = 2
WIRE_32BIT = 5

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
        def encode_field(tag: int, wire_type: int, value: Union[str, int, bytes]) -> bytes:
            header = self.encode_varint((tag << 3) | wire_type)
            if wire_type == WIRE_LENGTH_DELIMITED:
                if isinstance(value, str):
                    encoded_val = value.encode('utf-8')
                else:
                    encoded_val = value
                return header + self.encode_varint(len(encoded_val)) + encoded_val
            elif wire_type == WIRE_VARINT:
                return header + self.encode_varint(value)
            return b""

        from ff_api.config.settings import settings

        res = b""
        res += encode_field(1, WIRE_LENGTH_DELIMITED, uid)
        res += encode_field(2, WIRE_LENGTH_DELIMITED, region)
        res += encode_field(3, WIRE_LENGTH_DELIMITED, settings.OB_VERSION)
        return res

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

                    # Check if this field name should be treated as a nested message
                    target_map_key = nested_mapping.get(field_name)
                    if target_map_key and target_map_key in PROTO_FIELD_MAP:
                        result[field_name] = self.decode_response(val, target_map_key)
                    else:
                        try:
                            result[field_name] = val.decode('utf-8')
                        except UnicodeDecodeError:
                            result[field_name] = val
                elif wire_type == WIRE_64BIT:
                    val = struct.unpack("<Q", data[pos:pos+8])[0]
                    result[field_name] = val
                    pos += 8
                elif wire_type == WIRE_32BIT:
                    val = struct.unpack("<I", data[pos:pos+4])[0]
                    result[field_name] = val
                    pos += 4
                else:
                    raise FFError(ErrorCode.DECODE_ERROR, f"Unknown wire type {wire_type}")
        except Exception as e:
            if isinstance(e, FFError):
                raise e
            raise FFError(ErrorCode.DECODE_ERROR, f"Protobuf decode failed: {str(e)}")

        return result

proto_handler = ProtobufHandler()
