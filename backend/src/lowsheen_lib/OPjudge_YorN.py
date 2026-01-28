from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
import sys
import ast

class OPjudge_YorN(QDialog):
    def __init__(self, ImagePath, content, parent=None):
        super(OPjudge_YorN, self).__init__(parent)

        self.setWindowTitle("OP judge")

        # Add Button
        yesBtn = QPushButton("Yes", self)
        yesBtn.setFixedSize(200, 80)
        yesBtn.setFont(QFont("Arial", 15))
        yesBtn.setStyleSheet("background-color: green; color: white;") 
        yesBtn.clicked.connect(self.on_yes_click)

        noBtn = QPushButton("No", self)
        noBtn.setFixedSize(200, 80)
        noBtn.setFont(QFont("Arial", 15))
        noBtn.setStyleSheet("background-color: red; color: white;") 
        noBtn.clicked.connect(self.on_no_click)

        self.layout = QVBoxLayout()

        # Add Image
        if ImagePath:
            pixmap = QPixmap(ImagePath)
            pixmap = pixmap.scaled(800, 500, Qt.KeepAspectRatio)
            label = QLabel(self)
            label.setPixmap(pixmap)
            self.layout.addWidget(label)

        # Add content
        if content:
            message = QLabel(content)
            font = QFont("Arial", 20)
            message.setFont(font)
            self.layout.addWidget(message)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(yesBtn)
        button_layout.addWidget(noBtn)
        button_layout.addStretch()

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def on_yes_click(self):
        print('Yes')
        self.accept()

    def on_no_click(self):
        print('No')
        self.reject()
        
    def closeEvent(self, event):
        print('No')
        self.reject()

if __name__ == "__main__":
    
    # ImagePath, content = r'C:\Users\linhs\workflow\0607_Python_UI\BUP\star.png', "Please confirm "

    # args = dict(arg.split('=') for arg in sys.argv[2:])
    # ImagePath = args.get('ImagePath', '')
    # content = args.get('content', '')

    args = sys.argv[2]
    args = ast.literal_eval(args) # list轉字典

    ImagePath = args['ImagePath'] if 'ImagePath' in args else ''
    content = args['content'] if 'content' in args else ''
    
    app = QApplication(sys.argv)
    dialog = OPjudge_YorN(ImagePath, content)
    dialog.exec_()
    sys.exit()