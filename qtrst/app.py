from hashlib import md5
import sys
from cStringIO import StringIO
from os.path import basename

from docutils.core import Publisher
from docutils.io import StringInput, StringOutput
from docutils.utils import SystemMessage

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal

from qtrst.ui.main import Ui_MainWindow

BASE_TITLE = 'reStructuredText editor'


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

        try:
            output = self.pub.publish(enable_exit_status=False)
        except SystemMessage, err:
            output = unicode(err.message)

        sys.stderr = tmp_stderr

        self._cache[text_hash] = output
        return output

    def close(self):
        self._cache.clear()
        self.pub.set_source(None, None)


class File(QObject):

    updated = pyqtSignal()

    def __init__(self, parent, filename=None):
        QObject.__init__(self, parent)
        self._filename = filename
        self._isChanged = False

    @property
    def isChanged(self):
        return self._isChanged

    @isChanged.setter
    def isChanged(self, val):
        self._isChanged = val
        self.updated.emit()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename):
        self._filename = filename
        self.updated.emit()


class MainWindow(Ui_MainWindow, QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.setupUi(self, self)

        self.editFile = File(self, None)
        self.editFile.updated.connect(self.editFileUpdated)

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
        self.refreshPreview()
        self.editFile.isChanged = True

    @property
    def resultHtml(self):
        text = self.inputBox.document().toPlainText()
        return self.translator.translate(text)

    def refreshPreview(self):
        doc = self.previewBox.document()

        if self.previewTypeSource:
            doc.setPlainText(self.resultHtml)
        else:
            doc.setHtml(self.resultHtml)

    def editFileUpdated(self):

        if self.editFile.filename is None:
            self.setWindowTitle('Untitled' + ' - ' + BASE_TITLE)
            self.revertAction.setEnabled(False)

        else:
            if self.editFile.isChanged:
                title = '*'
                self.revertAction.setEnabled(True)
            else:
                title = ''
                self.revertAction.setEnabled(False)

            title = title + basename(self.editFile.filename) + ' - ' + BASE_TITLE
            self.setWindowTitle(title)

    @pyqtSlot()
    def newDoc(self):
        # TODO: prompt to save changed document

        self.inputBox.setPlainText('')

        self.editFile.filename = None
        self.editFile.isChanged = False

    @pyqtSlot()
    def openDoc(self):
        # TODO: prompt to save changed document

        filename, _ = QFileDialog.getOpenFileName(self, caption='Open text/rst file')

        if filename == '':
            return

        self._openDoc(filename)

    def _openDoc(self, filename):
        with open(filename, 'r') as f:
            content = f.read()

        self.editFile.filename = filename
        self.editFile.isChanged = False

        self.inputBox.blockSignals(True)
        self.inputBox.setPlainText(content)
        self.inputBox.blockSignals(False)

        self.refreshPreview()

    @pyqtSlot()
    def saveChangesRst(self):
        pass

    @pyqtSlot()
    def revert(self):
        if self.editFile.filename is None:
            return
        if not self.editFile.isChanged:
            return

        self._openDoc(self.editFile.filename)

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

        self.editFile.filename = filename
        self.editFile.isChanged = False

    def closeEvent(self, *args, **kwargs):
        result = QMainWindow.closeEvent(self, *args, **kwargs)

        self.translator.close()

        return result
