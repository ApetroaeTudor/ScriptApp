from queue import Queue
from enum import Enum
import html
import threading

import traceback

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextCursor, QTextFormat, QTextCharFormat, QColor, QFont
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QApplication, QLabel, QVBoxLayout, QTextEdit, \
    QHBoxLayout, QTextBrowser

import client
import messages as m
from concurrent.futures import ThreadPoolExecutor


class States(Enum):
    IDLE = 1
    RUNNING = 2
    DEBUGGING = 3

current_state = States.IDLE

class MainWindow(QMainWindow):
    my_is_client_launched = False
    my_q:client.thr_safe_q[str] = client.thr_safe_q()
    server_q:client.thr_safe_q[str] = client.thr_safe_q()
    port = 8080

    stop_event = threading.Event()



    total_nr_lines = 0
    current_debug_line = 0
    lines_marked = False


    current_script = ""
    current_script_lines = []
    accumulated_script = ""

    def __init__(self):
        super().__init__()
        self.my_executor = ThreadPoolExecutor(max_workers=1)
        self.my_executor_future = None

        self.my_main_widget = QWidget(self)
        self.setCentralWidget(self.my_main_widget)
        self.my_main_widget.setFixedSize(600,600)

        self.my_text_box = QTextEdit(self)
        self.my_text_box.setFixedSize(200,200)

        self.my_output_text_box = QTextBrowser(self)
        self.my_output_text_box.setReadOnly(True)
        self.my_output_text_box.setFixedSize(500,90)
        self.my_output_text_box.setAlignment(Qt.AlignCenter)
        self.my_error_line_idx = 0
        self.my_output_text_box.anchorClicked.connect(lambda: self.move_cursor_to_line(self.my_error_line_idx))
        self.my_output_text_box.setOpenExternalLinks(False)


        self.my_run_button = QPushButton(self)
        self.my_run_button.setText("Run")
        self.my_run_button.setFixedSize(90,50)
        self.my_run_button.clicked.connect(lambda: self.run_button_event())

        self.my_debug_button = QPushButton(self)
        self.my_debug_button.setText("Debug")
        self.my_debug_button.setFixedSize(90,50)
        self.my_debug_button.clicked.connect(lambda: self.debug_button_event())

        self.my_step_in_button = QPushButton(self)
        self.my_step_in_button.setDisabled(True)
        self.my_step_in_button.setText("Step In")
        self.my_step_in_button.setFixedSize(50,50)
        self.my_step_in_button.clicked.connect(lambda: self.step_in_event())

        self.my_exit_button = QPushButton(self)
        self.my_exit_button.setText("EXIT CL")
        self.my_exit_button.setFixedSize(50,50)
        self.my_exit_button.clicked.connect(lambda: self.exit_button_event())

        self.my_clear_button = QPushButton(self)
        self.my_clear_button.setText("CLEAR")
        self.my_clear_button.setFixedSize(50,50)
        self.my_clear_button.clicked.connect(lambda: self.clear_button_event() )


        self.my_buttons_h_box_layout = QHBoxLayout(self)
        self.my_buttons_h_box_layout.insertStretch(0)
        self.my_buttons_h_box_layout.insertWidget(1,self.my_run_button)
        self.my_buttons_h_box_layout.insertWidget(2,self.my_debug_button)
        self.my_buttons_h_box_layout.insertWidget(3,self.my_clear_button)
        self.my_buttons_h_box_layout.insertStretch(4)

        self.my_client_status_lbl = QLabel(self)
        self.my_client_status_lbl.setText("Client is not launched")

        self.my_current_status_lbl = QLabel(self)
        self.my_current_status_lbl.setText("CURRENT STATUS: IDLE")
        self.my_current_status_lbl.setStyleSheet("color:Green")
        self.my_current_status_lbl.setAlignment(Qt.AlignCenter)
        self.my_current_status_lbl.setFont(QFont("Arial",15,QFont.Bold))
        self.my_current_status_lbl.setFixedSize(600,50)


        self.my_timer = QTimer(self)
        self.my_timer.setInterval(100)
        self.my_timer.start()
        self.my_timer.timeout.connect(lambda: self.timer_check())

        self.my_v_box_layout = QVBoxLayout(self)
        self.my_main_widget.setLayout(self.my_v_box_layout)
        self.my_v_box_layout.insertStretch(0)
        self.my_v_box_layout.insertWidget(1,self.my_current_status_lbl,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertWidget(2,self.my_client_status_lbl,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertWidget(3,self.my_step_in_button,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertWidget(4,self.my_text_box,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertLayout(5,self.my_buttons_h_box_layout)
        self.my_v_box_layout.insertWidget(6,self.my_output_text_box,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertWidget(7,self.my_exit_button,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertStretch(8)




    def trim_lines(self):
        txt_lines = self.my_text_box.toPlainText().split("\n")
        txt_lines_filtered = list(filter(lambda s: s.strip(),txt_lines))
        new_txt = "\n".join(txt_lines_filtered)
        self.my_text_box.setText(new_txt)


    def mark_lines(self):
        if self.lines_marked:
            return
        txt_lines = self.my_text_box.toPlainText().split("\n")
        txt_lines_appended = list(map(lambda idx_elem: "L{0}: {1}".format(idx_elem[0]+1,idx_elem[1]), enumerate(txt_lines)))
        new_txt = "\n".join(txt_lines_appended)
        self.my_text_box.setText(new_txt)
        self.lines_marked = True

    def launch_client(self):
        self.my_executor_future = self.my_executor.submit(client.client_loop,self.my_q,self.server_q,self.port,self.stop_event)
        self.my_client_status_lbl.setText("Client is launched")
        self.my_is_client_launched = True

    def send_txt(self):
        textbox_contents = self.my_text_box.toPlainText()
        self.current_script = textbox_contents
        self.current_script_lines = self.current_script.split("\n")
        with open("MyScript.kts","w") as f:
            f.write(textbox_contents)


    def run_button_event(self):
        global current_state
        if not self.my_text_box.toPlainText().strip():
            return

        self.trim_lines()
        self.send_txt()
        msg = m.MessageFrame(sender=m.CLIENT_NAME,purpose=m.PURPOSE_COMPILE,destination=m.SERVER_NAME,message=self.current_script).get_string()
        self.my_q.put(msg,block=False)
        self.my_output_text_box.clear()

        if not self.my_is_client_launched:
            self.launch_client()
        current_state = current_state = States.RUNNING

    def debug_button_event(self):
        global current_state
        if not self.my_text_box.toPlainText().strip():
            return

        self.trim_lines()
        self.send_txt()

        # self.mark_lines()
        self.my_output_text_box.clear()

        if not self.my_is_client_launched:
            self.launch_client()
        current_state = current_state = States.DEBUGGING
        self.my_current_status_lbl.setText("CURRENT STATUS: Debugging, LINE: {0}".format(self.current_debug_line))

    def step_in_event(self):
        global current_state
        self.accumulated_script = self.accumulated_script + self.current_script_lines[self.current_debug_line] + "\n"
        self.current_debug_line = self.current_debug_line+1 if self.current_debug_line<self.total_nr_lines else self.current_debug_line

        msg_to_sv = m.MessageFrame(sender=m.CLIENT_NAME,purpose=m.PURPOSE_EXECUTE,destination=m.SERVER_NAME,message=self.accumulated_script).get_string()
        self.my_q.put(msg_to_sv,block=False)
        self.my_current_status_lbl.setText("CURRENT STATUS: Debugging, LINE: {0}".format(self.current_debug_line))



        if self.current_debug_line == self.total_nr_lines:
            self.total_nr_lines = 0
            self.current_debug_line = 0
            current_state = States.IDLE



    def exit_button_event(self):
            global current_state
            current_state = States.IDLE
            msg_str = m.MessageFrame(sender=m.CLIENT_NAME,purpose=m.PURPOSE_DISCONNECT,destination=m.CLIENT_NAME,message="").get_string()
            try:
                self.my_q.put(msg_str,block=False)
            except:
                pass

    def clear_button_event(self):
        self.my_text_box.clear()
        self.my_output_text_box.clear()
        self.lines_marked = False


    def move_cursor_to_line(self, line: int):
        document = self.my_text_box.document()
        print(line)

        target_block = document.findBlockByNumber(line - 1)

        if target_block.isValid():
            cursor = self.my_text_box.textCursor()
            cursor.setPosition(target_block.position())

            self.my_text_box.setTextCursor(cursor)
            self.my_text_box.ensureCursorVisible()
            self.my_text_box.setFocus()


    def closeEvent(self, event):
        self.stop_event.set()
        self.server_q.put("",block=True)
        self.my_q.put("",block=True)
        if self.stop_event.is_set():
            event.accept()
        else:
            event.ignore()


    def timer_check(self):
        global current_state

        try:
            msg = self.server_q.get(block=False)
            tokenized_msg = msg.split(m.separator)
            error_msg = tokenized_msg[0]
            type_msg = tokenized_msg[1]
            compilation_msg = tokenized_msg[2]
            return_msg = tokenized_msg[3]
            console_msg = tokenized_msg[4]


            if error_msg == 'True':
                line_idx_start_pos = compilation_msg.find(" - AT [LINE: ")+len(" - AT [LINE: ")
                line_idx_start_pos = line_idx_start_pos if line_idx_start_pos>=0 else 0
                line_idx_end_pos = compilation_msg.find(", COLUMN:")
                line_idx_end_pos = line_idx_end_pos if line_idx_end_pos>=0 else 0

                self.my_error_line_idx = int(compilation_msg[line_idx_start_pos:line_idx_end_pos].strip())

                text_html = f'<a href="{self.my_error_line_idx}">AN ERROR OCCURED: {error_msg} - {type_msg} - {compilation_msg}</a>'
                self.my_output_text_box.setAcceptRichText(True)
                self.my_output_text_box.append(text_html)
                current_state = States.IDLE

            elif error_msg == m.SERVER_ERROR:
                self.my_output_text_box.clear()
                self.my_output_text_box.setAcceptRichText(False)
                txt = html.escape("SERVER CLOSED. Closing socket..").replace("\n", "<br>")
                self.my_output_text_box.setText(txt)
                current_state = States.IDLE
                self.exit_button_event()
            elif error_msg == 'False' and type_msg == 'REAL_TIME':
                print(console_msg)
                self.my_output_text_box.setAcceptRichText(False)
                self.my_output_text_box.append(console_msg)
            else:
                self.my_output_text_box.setAcceptRichText(False)
                txt = "LINE: {0}\nError Status: {1}\n[{2}] - {3}\nReturn code: {4}\n{5}".format("general compilation" if self.current_debug_line == 0 else self.current_script_lines[self.current_debug_line-1],error_msg,type_msg,compilation_msg,return_msg,console_msg)
                txt = html.escape(txt).replace("\n","<br>")
                self.my_output_text_box.append(txt)

        except client.queue.Empty:
            pass
        except Exception as e:
            print(e)
            traceback.print_exc()

        if self.my_executor_future is None:
            self.my_is_client_launched = False
        else:
            if self.my_executor_future.done():
                self.my_is_client_launched = False
                if self.my_executor_future.result():
                    self.my_client_status_lbl.setText("Client ended gracefully")
                else:
                    self.my_client_status_lbl.setText("Client ended with error. Server is unreachable..")
            else:
                self.my_is_client_launched = True
                self.my_client_status_lbl.setText("Client is running..")

        self.my_current_status_lbl.setText("Current Status: RUNNING" if current_state == States.RUNNING else self.my_current_status_lbl.text())
        self.my_step_in_button.setVisible(True if current_state==States.DEBUGGING else False)
        self.my_step_in_button.setDisabled(False if current_state==States.DEBUGGING else True)
        current_state = current_state if self.my_is_client_launched else States.IDLE
        self.my_debug_button.setDisabled(True if current_state==States.RUNNING else False)
        self.my_run_button.setDisabled(True if current_state==States.DEBUGGING else False)

        # self.my_text_box.setReadOnly(True if current_state!=States.IDLE else False)
        self.total_nr_lines = 0 if current_state==States.IDLE else len(self.my_text_box.toPlainText().split("\n"))
        self.current_debug_line = 0 if current_state == States.IDLE else self.current_debug_line
        self.my_current_status_lbl.setText("CURRENT STATUS: IDLE" if current_state == States.IDLE else self.my_current_status_lbl.text())

        self.current_script = self.current_script if current_state != States.IDLE else ""
        self.accumulated_script = self.accumulated_script if current_state != States.IDLE else ""
        self.current_script_lines = self.current_script_lines if current_state !=States.IDLE else []



if __name__ == "__main__":
    app = QApplication(client.sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec()
# val x = 5
# val y = 6
# print(x+y)
# print(x-y)
# print("hi")