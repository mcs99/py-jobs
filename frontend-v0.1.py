import random
import sys
import threading
import time

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, pyqtBoundSignal, QTimer, pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFormLayout, QLabel, QLineEdit, \
    QHBoxLayout, QRadioButton, QDialog, QGroupBox, QDialogButtonBox, QSpinBox, QProgressBar
from backend01 import JobSearch


class Thread(QThread):
    newText = pyqtBoundSignal(str)

    def __init__(self):
        super(Thread, self).__init__()

    def __del__(self):
        self.wait()

    def write(self, text):
        self.newText.emit(str(text))

class SecondWindow(QDialog):

    def __init__(self, parent=None):
        super(SecondWindow, self).__init__(parent)

        self.setWindowTitle('Py-Jobs')  # Set window title
        self.formGroupBox = QGroupBox("py-jobs")  # Create form box for inputs

        self.create_form()

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)

        self.setLayout(mainLayout)

    def create_form(self):
        layout = QFormLayout()

        layout.addRow(QLabel("Search may last several hours and requires internet connection. Please do not close "
                             "py-jobs."))

        self.formGroupBox.setLayout(layout)

class Window(QDialog):

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.setWindowTitle('Py-Jobs')  # Set window title
        self.formGroupBox = QGroupBox("py-jobs")  # Create form box for inputs

        self.titleLineEdit = QLineEdit()  # Create input edit line for job title
        self.locationLineEdit = QLineEdit()  # Create input edit line for job title
        self.experienceSpinBar = QSpinBox()  # Create spin box for minimum years of exp.

        self.fulltimeRadioButton = QRadioButton("Full-Time")  # Create full-time radio button
        self.parttimeRadioButton = QRadioButton("Part-Time")  # Create part-time radio button
        self.temporaryRadioButton = QRadioButton("Temporary")  # Create temporary radio button

        self.jobtypeLabel = QLabel()
        self.fulltimeRadioButton.toggled.connect(self.update_jobtype)  # Update jobtypeLabel input to "fulltime"
        self.parttimeRadioButton.toggled.connect(self.update_jobtype)  # Update jobtypeLabel input to "parttime"
        self.temporaryRadioButton.toggled.connect(self.update_jobtype)  # Update jobtypeLabel input to "temporary"

        self.jobtypeHBox = QHBoxLayout()  # Create horizontal box layout for job type radio buttons
        self.jobtypeHBox.addWidget(self.fulltimeRadioButton)  # Add job type radio buttons
        self.jobtypeHBox.addWidget(self.parttimeRadioButton)
        self.jobtypeHBox.addWidget(self.temporaryRadioButton)

        self.searchPushButton = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)  # Create push button
        self.searchPushButton.accepted.connect(self.on_clicked)  # If 'OK' perform on clicked
        self.searchPushButton.rejected.connect(self.reject)  # If 'Cancel' reject and close window
        self.searchPushButton.accepted.connect(self.disable_button)

        self.resultsSpinBar = QSpinBox()
        self.resultsSpinBar.setMaximum(99999999)

        self.dialog = SecondWindow()
        # self.textEdit = QtWidgets.QTextEdit(self)

        self.create_form()

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)

        self.setLayout(mainLayout)

    def disable_button(self):
        self.searchPushButton.setEnabled(False)

    def update_jobtype(self):
        rbtn = self.sender()

        if rbtn.isChecked():
            jobtype = rbtn.text()

            if jobtype == 'Full-Time':
                self.jobtypeLabel.setText('fulltime')
            elif jobtype == 'Part-Time':
                self.jobtypeLabel.setText('parttime')
            elif jobtype == 'Temporary':
                self.jobtypeLabel.setText('temporary')

    def create_form(self):
        layout = QFormLayout()

        layout.addRow(QLabel("Title"), self.titleLineEdit)
        layout.addRow(QLabel("Location"), self.locationLineEdit)
        layout.addRow(QLabel('Min Yrs Experience'), self.experienceSpinBar)
        layout.addRow(QLabel("Job Type"), self.jobtypeHBox)
        layout.addRow(QLabel('Max Results'), self.resultsSpinBar)
        # layout.addRow(QLabel('Results'), self.textEdit)

        # layout.addWidget(ProgressBar(self, minimum=0, maximum=100, objectName="RedProgressBar"))

        layout.addRow(self.searchPushButton)

        self.formGroupBox.setLayout(layout)

    @pyqtSlot()
    def on_clicked(self):
        self.dialog.show()
        threading.Thread(target=self.getInfo, daemon=True).start()

    # @pyqtSlot()
    # def on_value_changed(self, value):
    #     self.textEdit.append("Value: {}".format(value))

    def getInfo(self):

        input_title = "{0}".format(self.titleLineEdit.text())
        input_location = "{0}".format(self.locationLineEdit.text())
        input_jobtype = "{0}".format(self.jobtypeLabel.text())
        input_experience = "{0}".format(self.experienceSpinBar.text())

        results = "{0}".format(self.resultsSpinBar.text())

        js = JobSearch(title=input_title, location=input_location, time_type=input_jobtype,
                       minimum_experience=int(input_experience))

        search_results = js.jobs(max_results=int(results))

        filtered = search_results.filter()

        search_results.export(dataset='a')
        filtered.export(dataset='f')

        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
