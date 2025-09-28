import socket
import sys
import threading
from queue import Queue as thr_safe_q, Queue

import messages as m

import json
import select
import time

from thonny.plugins.microbit.api_stubs.time import sleep

# type: status, error, finished
# message
# line



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
        try:
            msg_from_gui = q.get(block=True)
            msg_data:m.MessageFrame = m.MessageFrame()
            msg_data.unpack_string(msg_from_gui)
            if msg_data.destination == m.CLIENT_NAME and msg_data.purpose == m.PURPOSE_DISCONNECT:
                cl_socket.close()
                return True
            if msg_data.destination == m.SERVER_NAME:
                try:
                    msg_from_gui = msg_from_gui[:-2]
                    msg_from_gui = msg_from_gui + "`"
                    msg_from_gui = msg_from_gui.replace("\n","@@@")
                    cl_socket.sendall((msg_from_gui+"\n").encode("utf-8"))
                except:
                    print("?????")
        except Queue.queue.Empty:
            pass
        except Exception as e:
            print(f"ERROR processing message from GUI queue: {e}")

        ready_to_read,_,_ = select.select([cl_socket],[],[],0.05)

        if ready_to_read:
            try:
                msg = cl_socket.recv(m.MAX_MSG_LEN)
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

            # thr_safe_q.put("SERVER`"+msg.decode("utf-8"))

        time.sleep(0.05)



