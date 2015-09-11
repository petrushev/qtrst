from hashlib import md5
import sys
from cStringIO import StringIO

from docutils.core import Publisher
from docutils.io import StringInput, StringOutput

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSlot

from qtrst.ui.main import Ui_MainWindow


class Translator(object):

    _cache = {}

    def __init__(self):
        # publisher is used for html generation
        self.pub = Publisher(None, None, None, settings=None,
                             source_class=StringInput,
                             destination_class=StringOutput)
        self.pub.set_components('standalone', 'restructuredtext', 'html')
        self.pub.process_programmatic_settings(None, None, None)
        self.pub.set_destination(None, None)

    def translate(self, text):
        text_hash = md5(text.encode('utf-8')).digest()
        if text_hash in self._cache:
            return self._cache[text_hash]

        # apply transform
        tmp_stderr = sys.stderr
        sys.stderr = StringIO()
        self.pub.set_source(unicode(text), None)
        output = self.pub.publish(enable_exit_status=False)
        sys.stderr = tmp_stderr

        self._cache[text_hash] = output
        return output


class MainWindow(Ui_MainWindow, QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.setupUi(self, self)

        self.previewTypeSource = False
        self.resultHtml = ''

        # monospace font
        font = QFont('')
        font.setStyleHint(QFont.TypeWriter)
        font.setKerning(True)

        self.inputBox.setFont(font)
        self.resultDock.setTitleBarWidget(QWidget())

        self.inputBox.textChanged.connect(self.textChanged)
        self.saveHtmlAction.triggered.connect(self.saveHtmlAs)
        self.saveHtmlButton.clicked.connect(self.saveHtmlAs)
        self.saveRstAction.triggered.connect(self.saveRstAs)
        self.saveRstButton.clicked.connect(self.saveRstAs)
        self.togglePreviewTypeButton.clicked.connect(self.togglePreviewType)

        self.translator = Translator()

    @pyqtSlot(bool)
    def togglePreviewType(self, checked):
        self.previewTypeSource = checked

        self.refreshPreview()

    @pyqtSlot()
    def textChanged(self):
        text = self.inputBox.document().toPlainText()
        self.resultHtml = self.translator.translate(text)

        self.refreshPreview()

    def refreshPreview(self):
        doc = self.previewBox.document()
        if self.previewTypeSource:
            doc.setPlainText(self.resultHtml)
        else:
            doc.setHtml(self.resultHtml)

    @pyqtSlot()
    def saveHtmlAs(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export html")

        if filename == '':
            return

        with open(filename, 'w') as f:
            f.write(self.resultHtml)

    @pyqtSlot()
    def saveRstAs(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save reStructuredText")

        if filename == '':
            return

        with open(filename, 'w') as f:
            rst = self.inputBox.document().toPlainText()
            f.write(rst)
