
CLIENT_NAME = str("CLIENT")
SERVER_NAME = str("SERVER")

PURPOSE_EXECUTE = str("EXECUTE")
PURPOSE_DISCONNECT = str("DISCONNECT")
PURPOSE_COMPILE = str("COMPILE")
PURPOSE_SEND = str("SEND")
PURPOSE_UPDATE_CONSOLE_OK = str("UPDATE_CONSOLE_OK")
PURPOSE_UPDATE_CONSOLE_ERR = str("UPDATE_CONSOLE_ERR")


separator = str('`')
MAX_MSG_LEN = int(256)

class MessageFrame:
    def __init__(self,sender:str="",purpose:str="",destination:str="",message:str=""):
        self.sender = sender
        self.purpose = purpose
        self.destination = destination
        self.message = message

    def get_string(self):
        global separator
        return self.sender+separator+self.purpose+separator+self.destination+separator+self.message

    def unpack_string(self,msg_str:str):
        global separator
        str_tokens = msg_str.split(separator)
        self.sender = str_tokens[0]
        self.purpose = str_tokens[1]
        self.destination = str_tokens[2]
        self.message = str_tokens[3]




