import socket
import sys
import threading
from queue import Queue as thr_safe_q

import json
import select
import time

from thonny.plugins.microbit.api_stubs.time import sleep

# type: status, error, finished
# message
# line


max_msg_len = int(256)


def client_loop(q:thr_safe_q[str],port)->bool:
    global max_msg_len
    try:
        cl_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    except:
        return False
    try:
        cl_socket.connect(('127.0.0.1',port))
    except:
        return False

    while True:

        ready_to_read,_,_ = select.select([cl_socket],[],[],0.05)
        if ready_to_read:
            try:
                msg = cl_socket.recv(max_msg_len)
                print(msg.decode("utf-8"))
            except BlockingIOError:
                continue

            # msg_json = json.loads(msg)
            #
            # msg_type = msg_json.get("type")
            # msg_content = msg_json.get("message")
            # msg_line = msg_json.get("line")
            #
            # if msg == b'':
            #     q.put("Server closed")
            #     cl_socket.close()
            #     return True
            # elif msg_type == "status":
            #     q.put("LINE: {0} - [{1}]:{2}".format(msg_line,msg_type,msg_content))
            # elif msg_type == "error" or msg_type == "finished":
            #     q.put("LINE: {0} - [{1}]:{2}".format(msg_line,msg_type,msg_content))
            #     cl_socket.close()
            #     return True
            # else:
            #     q.put("ERROR: Invalid message received!")
            #     cl_socket.close()
            #     return True

            thr_safe_q.put("SERVER`"+msg.decode("utf-8"))

        try:

            msg_from_gui = q.get(block=False)
            msg_from_gui_tokens = msg_from_gui.strip().split("`")
            print(msg_from_gui_tokens)
            if msg_from_gui_tokens[0]!="CLIENT":
                q.put(msg_from_gui)
            else:
                if msg_from_gui_tokens[1] == "CLOSE":
                    cl_socket.close()
                    return True
                elif msg_from_gui_tokens[1] == "SENDING":
                    try:
                        cl_socket.send((msg_from_gui_tokens[2] + "\n").encode("utf-8"))
                    except BrokenPipeError:
                        print("Connection closed by peer")
                    except ConnectionResetError:
                        print("Connection reset by peer")
                    except BlockingIOError:
                        print("Send would block (non-blocking socket)")
                    except OSError as e:
                        print("Other socket error:", e)


        except:
            pass

        time.sleep(0.05)




