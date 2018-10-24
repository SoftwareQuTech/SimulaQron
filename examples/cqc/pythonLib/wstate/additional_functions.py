from SimulaQron.general.hostConfig import *
from SimulaQron.cqc.backend.cqcHeader import *
from SimulaQron.cqc.pythonLib.cqc import *
from SimulaQron.cqc.pythonLib.protocols.wstate import *


def string_to_int(message):
    """
    Converts string message into integer.
    - **Arguments**
        :message: String message
    """
    ord_list = []
    for x in range(0, len(message)):
        ord_list.append(ord(message[x]))
    return ord_list


def int_to_string(message):
    """
    Converts integer message into string.
    - **Arguments**
        :message: integer message
    """
    char_list = ""
    for x in range(0, len(message)):
        char_list += chr(message[x])
    return char_list


def broadbastClassical(message, Owner):
    """
    Broadcasts the same classical message.
    - **Arguments**
        :message: Integer message
    """
    print("Broadcasting leader election result")
    for key in Owner._cqcNet.hostDict.keys():
        if key != Owner.name:
            Owner.sendClassical(key, message)
