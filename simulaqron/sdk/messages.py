import abc
import enum
import ctypes

from netqasm.encoding import Address, Register, INTEGER, OptionalInt
from netqasm.messages import Message, MESSAGE_TYPE, MESSAGE_TYPE_BYTES

MESSAGE_ID = ctypes.c_uint32


# TODO move to netqasm
class MessageHeader(ctypes.Structure):
    _fields_ = [
        ('id', MESSAGE_ID),
        ('length', ctypes.c_uint32),
    ]

    @classmethod
    def len(cls):
        return len(bytes(cls()))

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id}, length={self.length})"


class ReturnMessage(Message):
    pass


class ReturnMessageType(enum.Enum):
    DONE = 0x00
    ERR = 0x01
    RET_ARR = 0x02
    RET_REG = 0x03


class MsgDoneMessage(ReturnMessage):
    _fields_ = [
        ('msg_id', MESSAGE_ID),
    ]

    TYPE = ReturnMessageType.DONE

    def __init__(self, msg_id=0):
        super().__init__(self.TYPE.value)
        self.msg_id = msg_id


class ErrorCode(enum.Enum):
    GENERAL = 0x00
    NO_QUBIT = 0x01
    UNSUPP = 0x02


class ErrorMessage(ReturnMessage):
    _fields_ = [
        ('err_code', ctypes.c_uint8),
    ]

    TYPE = ReturnMessageType.ERR

    def __init__(self, err_code):
        super().__init__(self.TYPE.value)
        self.err_code = err_code.value


class ReturnArrayMessageHeader(ctypes.Structure):
    _pack = 1
    _fields_ = [
        ('address', Address),
        ('length', INTEGER),
    ]

    @classmethod
    def len(cls):
        return len(bytes(cls()))


class ReturnArrayMessage:

    TYPE = ReturnMessageType.RET_ARR

    def __init__(self, address, values):
        """NOTE this message does not subclass from `ReturnMessage` since
        the values is of variable length.
        Still this class defines the methods `__bytes__` and `deserialize_from`
        so that it can be packed and unpacked.
        
        The packed form of the message is:

        .. code-block:: text

            | ADDRESS | LENGTH | VALUES ... |

        """
        self.type = self.TYPE.value
        self.address = address
        self.values = values

    def __bytes__(self):
        array_type = OptionalInt * len(self.values)
        payload = array_type(*(OptionalInt(v) for v in self.values))
        hdr = ReturnArrayMessageHeader(
            address=Address(self.address),
            length=len(self.values),
        )
        return bytes(MESSAGE_TYPE(self.type)) + bytes(hdr) + bytes(payload)

    def __str__(self):
        return f"{self.__class__.__name__}(address={self.address}, values={self.values})"

    def __len__(self):
        return len(bytes(self))

    @classmethod
    def deserialize_from(cls, raw: bytes):
        raw = raw[MESSAGE_TYPE_BYTES:]
        hdr = ReturnArrayMessageHeader.from_buffer_copy(raw)
        array_type = OptionalInt * hdr.length
        raw = raw[ReturnArrayMessageHeader.len():]
        values = list(v.value for v in array_type.from_buffer_copy(raw))
        return cls(address=hdr.address.address, values=values)


class ReturnRegMessage(ReturnMessage):
    _fields_ = [
        ('register', Register),
        ('value', INTEGER),
    ]

    TYPE = ReturnMessageType.RET_REG

    def __init__(self, register, value):
        super().__init__(self.TYPE.value)
        self.register = register
        self.value = value


RETURN_MESSAGE_CLASSES = {
    ReturnMessageType.DONE: MsgDoneMessage,
    ReturnMessageType.ERR: ErrorMessage,
    ReturnMessageType.RET_REG: ReturnRegMessage,
    ReturnMessageType.RET_ARR: ReturnArrayMessage,
}


def deserialize(raw: bytes) -> Message:
    message_type = ReturnMessageType(MESSAGE_TYPE.from_buffer_copy(raw[:MESSAGE_TYPE_BYTES]).value)
    message_class = RETURN_MESSAGE_CLASSES[message_type]
    return message_class.deserialize_from(raw)
