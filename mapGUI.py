# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mapGUI.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1311, 968)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.mapHBL = QtWidgets.QHBoxLayout()
        self.mapHBL.setObjectName("mapHBL")
        self.stopOverLV = QtWidgets.QListView(Dialog)
        self.stopOverLV.setResizeMode(QtWidgets.QListView.Adjust)
        self.stopOverLV.setWordWrap(True)
        self.stopOverLV.setObjectName("stopOverLV")
        self.mapHBL.addWidget(self.stopOverLV)
        self.verticalLayout.addLayout(self.mapHBL)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.exportPB = QtWidgets.QPushButton(Dialog)
        self.exportPB.setObjectName("exportPB")
        self.horizontalLayout.addWidget(self.exportPB)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Your Route"))
        self.stopOverLV.setToolTip(_translate("Dialog", "<html><head/><body><p>Recommends larger cities within 30 minutes of our route. </p></body></html>"))
        self.exportPB.setText(_translate("Dialog", "Export to shapefile"))
