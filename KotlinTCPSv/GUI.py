from queue import Queue

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QApplication, QLabel, QVBoxLayout, QTextEdit
import client
from concurrent.futures import ThreadPoolExecutor

current_line = int(0)

class MainWindow(QMainWindow):
    my_is_client_launched = False
    my_q:Queue[str] = client.thr_safe_q()
    port = 8080

    def __init__(self):
        super().__init__()
        self.my_executor = ThreadPoolExecutor(max_workers=1)
        self.my_executor_future = None

        self.my_main_widget = QWidget(self)
        self.setCentralWidget(self.my_main_widget)
        self.my_main_widget.setFixedSize(600,600)

        self.my_launch_client_button = QPushButton(self)
        self.my_launch_client_button.setFixedSize(200,50)
        self.my_launch_client_button.setText("Launch Client")
        self.my_launch_client_button.clicked.connect(lambda:self.launch_server())


        self.my_text_box = QTextEdit(self)
        self.my_text_box.setFixedSize(200,200)

        self.my_submit_button = QPushButton(self)
        self.my_submit_button.setDisabled(True)
        self.my_submit_button.setText("Run")
        self.my_submit_button.setFixedSize(200,50)
        self.my_submit_button.clicked.connect(lambda: self.send_txt())

        self.my_client_status_lbl = QLabel(self)
        self.my_client_status_lbl.setText("Client is not launched")

        self.my_timer = QTimer(self)
        self.my_timer.setInterval(100)
        self.my_timer.start()
        self.my_timer.timeout.connect(lambda: self.timer_check())

        self.my_v_box_layout = QVBoxLayout(self)
        self.my_main_widget.setLayout(self.my_v_box_layout)
        self.my_v_box_layout.insertStretch(0)
        self.my_v_box_layout.insertWidget(1,self.my_launch_client_button,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertWidget(2,self.my_client_status_lbl,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertStretch(3)
        self.my_v_box_layout.insertWidget(4,self.my_text_box,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertWidget(5,self.my_submit_button,alignment=Qt.AlignCenter)
        self.my_v_box_layout.insertStretch(6)




    def launch_server(self):
        self.my_executor_future = self.my_executor.submit(client.client_loop,self.my_q,self.port)
        self.my_client_status_lbl.setText("Client is launched")
        self.my_is_client_launched = True

    def send_txt(self):
        msg = "CLIENT`"+"SENDING`"+self.my_text_box.toPlainText()
        self.my_q.put(msg)
        with open("MyScript.kts","w") as f:
            f.write(self.my_text_box.toPlainText())

    def timer_check(self):
        if self.my_executor_future is None:
            self.my_is_client_launched = False
            self.my_launch_client_button.setDisabled(False)
        else:
            if self.my_executor_future.done():
                self.my_is_client_launched = False
                self.my_launch_client_button.setDisabled(False)
                if self.my_executor_future.done() is True:
                    self.my_client_status_lbl.setText("Client ended gracefully")
                else:
                    self.my_client_status_lbl.setText("Client ended with error")
            else:
                self.my_is_client_launched = True
                self.my_launch_client_button.setDisabled(True)
                self.my_client_status_lbl.setText("Client is running..")
        if self.my_is_client_launched:
            self.my_submit_button.setDisabled(False)
        else:
            self.my_submit_button.setDisabled(True)

        try:
            msg = self.my_q.get(block=False)
            msg_tokens = msg.strip().split("`")
            if msg_tokens[0] and msg_tokens[0]!= "SERVER":
                self.my_q.put(msg)
            else:
                self.myServerResponse.setText("Server response: {}".format(msg_tokens[1]))
        except:
            pass

        nr_lines = len(self.my_text_box.toPlainText().split('\n'))
        print(nr_lines)



if __name__ == "__main__":
    app = QApplication(client.sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec()
