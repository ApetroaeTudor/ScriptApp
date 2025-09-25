from queue import Queue

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QApplication, QLabel, QVBoxLayout, QTextEdit
import client
from concurrent.futures import ThreadPoolExecutor


class MainWindow(QMainWindow):
    myIsClientLaunched = False
    comm_q:Queue[str] = client.thr_safe_q()
    port = 8080

    def __init__(self):
        super().__init__()
        self.myExecutor = ThreadPoolExecutor(max_workers=1)
        self.myExecutorFuture = None

        self.myMainWidget = QWidget(self)
        self.setCentralWidget(self.myMainWidget)
        self.myMainWidget.setFixedSize(600,600)

        self.myLaunchClientButton = QPushButton(self)
        self.myLaunchClientButton.setFixedSize(200,50)
        self.myLaunchClientButton.setText("Launch Client")
        self.myLaunchClientButton.clicked.connect(lambda:self.launch_server())


        self.myTextBox = QTextEdit(self)
        self.myTextBox.setFixedSize(200,200)

        self.mySubmitButton = QPushButton(self)
        self.mySubmitButton.setDisabled(True)
        self.mySubmitButton.setText("Submit to SV")
        self.mySubmitButton.setFixedSize(200,50)
        self.mySubmitButton.clicked.connect(lambda: self.send_txt())

        self.myClientStatusLbl = QLabel(self)
        self.myClientStatusLbl.setText("Client is not launched")

        self.myTimer = QTimer(self)
        self.myTimer.setInterval(200)
        self.myTimer.start()
        self.myTimer.timeout.connect(lambda: self.timer_check())

        self.myVBoxLayout = QVBoxLayout(self)
        self.myMainWidget.setLayout(self.myVBoxLayout)
        self.myVBoxLayout.insertStretch(0)
        self.myVBoxLayout.insertWidget(1,self.myLaunchClientButton,alignment=Qt.AlignCenter)
        self.myVBoxLayout.insertWidget(2,self.myClientStatusLbl,alignment=Qt.AlignCenter)
        self.myVBoxLayout.insertStretch(3)
        self.myVBoxLayout.insertWidget(4,self.myTextBox,alignment=Qt.AlignCenter)
        self.myVBoxLayout.insertWidget(5,self.mySubmitButton,alignment=Qt.AlignCenter)
        self.myVBoxLayout.insertStretch(6)




    def launch_server(self):
        self.myExecutorFuture = self.myExecutor.submit(client.client_loop,self.comm_q,self.port)
        self.myClientStatusLbl.setText("Client is launched")
        self.myIsClientLaunched = True

    def send_txt(self):
        msg = "CLIENT`"+"SENDING`"+self.myTextBox.toPlainText()
        self.comm_q.put(msg)
        self.myTextBox.clear()

    def timer_check(self):
        if self.myExecutorFuture is None:
            self.myIsClientLaunched = False
            self.myLaunchClientButton.setDisabled(False)
        else:
            if self.myExecutorFuture.done():
                self.myIsClientLaunched = False
                self.myLaunchClientButton.setDisabled(False)
                if self.myExecutorFuture.done() is True:
                    self.myClientStatusLbl.setText("Client ended gracefully")
                else:
                    self.myClientStatusLbl.setText("Client ended with error")
            else:
                self.myIsClientLaunched = True
                self.myLaunchClientButton.setDisabled(True)
                self.myClientStatusLbl.setText("Client is running..")
        if self.myIsClientLaunched:
            self.mySubmitButton.setDisabled(False)
        else:
            self.mySubmitButton.setDisabled(True)

        try:
            msg = self.comm_q.get(block=False)
            msg_tokens = msg.strip().split("`")
            if msg_tokens[0] and msg_tokens[0]!= "SERVER":
                self.comm_q.put(msg)
            else:
                self.myServerResponse.setText("Server response: {}".format(msg_tokens[1]))
        except:
            pass


if __name__ == "__main__":
    app = QApplication(client.sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec()
