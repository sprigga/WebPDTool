from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
import sys
import ast

class OPjudge_confirm(QDialog):
    def __init__(self, ImagePath, content, parent=None):
        super(OPjudge_confirm, self).__init__(parent)

        self.setWindowTitle("OP judge")

        # Add Button
        QBtn = QPushButton("confirm", self)
        QBtn.setFixedSize(200, 80)
        QBtn.setFont(QFont("Arial", 15))
        QBtn.setStyleSheet("background-color: green; color: white;") 
        QBtn.clicked.connect(self.on_click)

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
        button_layout.addWidget(QBtn)
        button_layout.addStretch()

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def on_click(self):
        print('Yes')
        self.accept()
        
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
    dialog = OPjudge_confirm(ImagePath, content)
    dialog.exec_()
    sys.exit()