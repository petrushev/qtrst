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
        pub = Publisher(None, None, None, settings=None,
                             source_class=StringInput,
                             destination_class=StringOutput)
        pub.set_components('standalone', 'restructuredtext', 'html')
        pub.process_programmatic_settings(None, None, None)
        pub.set_destination(None, None)

        self.pub = pub

    def translate(self, text):
        text_hash = md5(text.encode('utf-8')).digest()
        if text_hash in self._cache:
            return self._cache[text_hash]

        # apply transform
        self.pub.set_source(text, None)

        tmp_stderr = sys.stderr
        sys.stderr = StringIO()
        output = self.pub.publish(enable_exit_status=False)
        sys.stderr = tmp_stderr

        self._cache[text_hash] = output
        return output

    def close(self):
        self._cache.clear()
        self.pub.set_source(None, None)


class MainWindow(Ui_MainWindow, QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.setupUi(self, self)

        self.resultHtml = ''

        # monospace font
        font = QFont('')
        font.setStyleHint(QFont.TypeWriter)
        font.setKerning(True)

        self.inputBox.setFont(font)
        self.resultDock.setTitleBarWidget(QWidget())

        self.translator = Translator()

    @property
    def previewTypeSource(self):
        return not self.togglePreviewTypeButton.isChecked()

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

    def closeEvent(self, *args, **kwargs):
        result = QMainWindow.closeEvent(self, *args, **kwargs)

        self.translator.close()

        return result
