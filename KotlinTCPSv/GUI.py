from queue import Queue
from enum import Enum

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QApplication, QLabel, QVBoxLayout, QTextEdit, QHBoxLayout
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
    my_q:Queue[str] = client.thr_safe_q()
    port = 8080

    total_nr_lines = 0
    current_debug_line = 0


    def __init__(self):
        super().__init__()
        self.my_executor = ThreadPoolExecutor(max_workers=1)
        self.my_executor_future = None

        self.my_main_widget = QWidget(self)
        self.setCentralWidget(self.my_main_widget)
        self.my_main_widget.setFixedSize(600,600)

        self.my_text_box = QTextEdit(self)
        self.my_text_box.setFixedSize(200,200)

        self.my_output_text_box = QTextEdit(self)
        self.my_output_text_box.setReadOnly(True)
        self.my_output_text_box.setFixedSize(200,70)

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
        self.my_exit_button.setText("EXIT")
        self.my_exit_button.setFixedSize(50,50)
        self.my_exit_button.clicked.connect(lambda: self.exit_button_event())


        self.my_buttons_h_box_layout = QHBoxLayout(self)
        self.my_buttons_h_box_layout.insertStretch(0)
        self.my_buttons_h_box_layout.insertWidget(1,self.my_run_button)
        self.my_buttons_h_box_layout.insertWidget(2,self.my_debug_button)
        self.my_buttons_h_box_layout.insertStretch(3)



        self.my_client_status_lbl = QLabel(self)
        self.my_client_status_lbl.setText("Client is not launched")


        self.my_timer = QTimer(self)
        self.my_timer.setInterval(100)
        self.my_timer.start()
        self.my_timer.timeout.connect(lambda: self.timer_check())

        self.my_v_box_layout = QVBoxLayout(self)
        self.my_main_widget.setLayout(self.my_v_box_layout)
        self.my_v_box_layout.insertStretch(0)
        self.my_v_box_layout.insertWidget(1,self.my_client_status_lbl,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertWidget(2,self.my_step_in_button,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertWidget(3,self.my_text_box,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertLayout(4,self.my_buttons_h_box_layout)
        self.my_v_box_layout.insertWidget(5,self.my_output_text_box,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertWidget(6,self.my_exit_button,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertStretch(7)




    def launch_client(self):
        self.my_executor_future = self.my_executor.submit(client.client_loop,self.my_q,self.port)
        self.my_client_status_lbl.setText("Client is launched")
        self.my_is_client_launched = True

    def send_txt(self):
        textbox_contents = self.my_text_box.toPlainText()
        with open("MyScript.kts","w") as f:
            f.write(textbox_contents)
        msg = m.MessageFrame(sender=m.CLIENT_NAME,purpose=m.PURPOSE_COMPILE,destination=m.SERVER_NAME,message="").get_string()
        self.my_q.put(msg,block=False)

    def run_button_event(self):
        global current_state
        if not self.my_is_client_launched:
            self.launch_client()
        self.send_txt()
        current_state = current_state = States.RUNNING

    def debug_button_event(self):
        global current_state
        if not self.my_is_client_launched:
            self.launch_client()
        self.send_txt()
        current_state = current_state = States.DEBUGGING

    def step_in_event(self):
        self.current_debug_line = self.current_debug_line+1 if self.current_debug_line<self.total_nr_lines else self.current_debug_line


    def exit_button_event(self):
        global current_state
        current_state = States.IDLE
        msg_str = m.MessageFrame(sender=m.CLIENT_NAME,purpose=m.PURPOSE_DISCONNECT,destination=m.CLIENT_NAME,message="").get_string()
        try:
            self.my_q.put(msg_str,block=False)
        except:
            pass



    def timer_check(self):
        global current_state
        if self.my_executor_future is None:
            self.my_is_client_launched = False
        else:
            if self.my_executor_future.done():
                self.my_is_client_launched = False
                if self.my_executor_future.done() is True:
                    self.my_client_status_lbl.setText("Client ended gracefully")
                else:
                    self.my_client_status_lbl.setText("Client ended with error")
            else:
                self.my_is_client_launched = True
                self.my_client_status_lbl.setText("Client is running..")

        self.my_step_in_button.setVisible(True if current_state==States.DEBUGGING else False)
        self.my_step_in_button.setDisabled(False if current_state==States.DEBUGGING else True)
        current_state = current_state if self.my_is_client_launched else States.IDLE
        self.my_debug_button.setDisabled(True if current_state==States.RUNNING else False)
        self.my_run_button.setDisabled(True if current_state==States.DEBUGGING else False)
        nr_lines = len(self.my_text_box.toPlainText().split('\n'))

        self.my_text_box.setReadOnly(True if current_state!=States.IDLE else False)
        self.total_nr_lines = 0 if current_state==States.IDLE else len(self.my_text_box.toPlainText().split("\n"))
        self.current_debug_line = 0 if current_state == States.IDLE else self.current_debug_line



if __name__ == "__main__":
    app = QApplication(client.sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec()
