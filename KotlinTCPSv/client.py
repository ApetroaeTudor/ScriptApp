import queue
import socket
import sys
import threading
import traceback
from queue import Queue as thr_safe_q, Queue


import messages as m

import json
import select
import time

from messages import JSON_ERROR, JSON_TYPE, JSON_MESSAGE, JSON_RESULT, JSON_CONSOLE, separator, SERVER_ERROR


def client_loop(q:thr_safe_q[str],receiver_q:thr_safe_q[str],port)->bool:
    global max_msg_len
    try:
        cl_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    except:
        return False
    try:
        cl_socket.connect(('127.0.0.1',port))
    except:
        return False

    receiver_thr = threading.Thread(target=receiver_task,args=(cl_socket,receiver_q))
    receiver_thr.start()

    while True:
        try:
            msg_from_gui = q.get(block=True)
            msg_data:m.MessageFrame = m.MessageFrame()
            msg_data.unpack_string(msg_from_gui)
            if msg_data.destination == m.CLIENT_NAME and msg_data.purpose == m.PURPOSE_DISCONNECT:
                cl_socket.close()
                receiver_thr.join()
                return True
            if msg_data.destination == m.SERVER_NAME:
                try:
                    msg_from_gui = msg_from_gui.replace("\n","@@@")
                    cl_socket.sendall((msg_from_gui+"\n").encode("utf-8"))
                except (ConnectionRefusedError, socket.timeout):
                    receiver_thr.join()
                    return False
        except Queue.queue.Empty:
            pass
        except Exception as e:
            print(f"ERROR processing message from GUI queue: {e}")


        time.sleep(0.05)



def receiver_task(cl_socket, comm_q:thr_safe_q[str]):
    while(True):
        ready_to_read,_,_ = select.select([cl_socket],[],[],0.05)

        if ready_to_read:
            try:
                msg_raw = cl_socket.recv(m.MAX_MSG_LEN)
                msg = msg_raw.decode("utf-8")
                msg_json = json.loads(msg)

                if msg_raw == b'':
                    error_msg = SERVER_ERROR
                else:
                    error_msg = str(msg_json.get(JSON_ERROR))

                type_msg = str(msg_json.get(JSON_TYPE))
                message_msg = str(msg_json.get(JSON_MESSAGE))
                result_msg = str(msg_json.get(JSON_RESULT))
                console_msg = str(msg_json.get(JSON_CONSOLE))

                comm_q.put(item = error_msg + separator + type_msg + separator + message_msg + separator + result_msg + separator + console_msg + separator,block=True)
            except queue.Empty:
                pass
            except:
                break


