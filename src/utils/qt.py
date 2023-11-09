from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont, QPainter, QPen
import pyautogui as pg
import sys


class LineWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(LineWidget, self).__init__(*args, **kwargs)
        self.x, self.y = 0, 0

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.red, 2)
        painter.setPen(pen)
        painter.drawLine(self.x, 0, self.x, self.height())
        painter.drawLine(0, self.y, self.width(), self.y)


class ConfigUI:
    def __init__(self, first_text: str, click_callback) -> None:
        self.app = QApplication(sys.argv)
        self.setup_line_widget()
        self.setup_label(first_text)
        pg.mouseListener(on_click=click_callback)
        self.app.processEvents()

    def setup_line_widget(self):
        line_widget = LineWidget()
        line_widget.setWindowFlags(
            Qt.SplashScreen | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        )
        line_widget.setAttribute(Qt.WA_TranslucentBackground)
        line_widget.show()
        screen = self.app.primaryScreen()
        size = screen.size()
        line_widget.resize(size.width(), size.height())
        line_widget.move(0, 0)
        line_widget.setAttribute(Qt.WA_TranslucentBackground)
        line_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.line = line_widget

    def setup_label(self, text: str):
        label = QLabel(text)
        label.setWindowFlags(
            Qt.Widget | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        )
        label.setAttribute(Qt.WA_TranslucentBackground)
        label.setAttribute(Qt.WA_TransparentForMouseEvents)
        current_font = label.font()
        current_font.setPointSize(current_font.pointSize() * 2)
        label.setFont(current_font)
        palette = QPalette()
        palette.setColor(QPalette.WindowText, QColor(Qt.white))
        label.setPalette(palette)
        label.show()
        self.label = label

    def update_text(self, text):
        self.label.setText(text)
        self.label.repaint()

    def close(self):
        self.label.close()
        self.line.close()
        self.app.quit()

    def loop(self):
        x, y = pg.position()
        self.line.x, self.line.y = x, y
        self.line.repaint()
        label_width = self.label.fontMetrics().boundingRect(self.label.text()).width()
        self.label.move(x - label_width // 2, y - 30)


def on_click(x, y, button, pressed):
    if button == pg.LEFT:
        if pressed:
            positions.append((x, y))
