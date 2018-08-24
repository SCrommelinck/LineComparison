# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LineComparisonDialog
                                 A QGIS plugin
                             -------------------
        begin                : 2018-08-01
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Sophie Crommelinck
        email                : s.crommelinck@utwente.nl
        icon                 : Line Graph by Calvin Goodman from the Noun Project
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt5 import uic
from PyQt5.QtCore import QSettings, QTranslator, qVersion, Qt
from PyQt5.QtGui import QIcon, QColor, QPixmap
from PyQt5.QtWidgets import QDialog, QAction, QFileDialog, QToolBar

from .ComparisonController import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'LineComparison_dialog_base.ui'))


class LineComparisonDialog(QDialog, FORM_CLASS):

    vectorInput = None
    refInput = None
    textOutput = None

    def __init__(self, parent=None):
        """Constructor."""
        super(LineComparisonDialog, self).__init__(parent)
        self.setupUi(self)
        # Connect buttons to functions
        self.vectorInputButton.clicked.connect(self.selectVectorInput)
        self.vectorRefButton.clicked.connect(self.selectRefInput)
        self.textOutputButton.clicked.connect(self.selectTextOutput)
        self.createConfusionMatrixButton.clicked.connect(self.createConfusionMatrix)

        self.lineEdit1.setText(LineComparisonDialog.vectorInput)
        self.lineEdit2.setText(LineComparisonDialog.refInput)
        self.lineEdit3.setText(LineComparisonDialog.textOutput)

    def _setImage(self, label, fileName):
        label.setPixmap(QPixmap(os.path.dirname(os.path.realpath(__file__)) + fileName))

    # Open vector file provided by user in GUI
    def selectVectorInput(self):
        result = QFileDialog.getOpenFileName(self, 'Open File', '', '*.shp')
        if result:
            LineComparisonDialog.vectorInput = result[0]
            self.lineEdit1.setText(LineComparisonDialog.vectorInput)
            ComparisonController.openVector(ComparisonController.lineLayerName, LineComparisonDialog.vectorInput,
                                             255, 0, 0, 0.3)

    # Open reference vector file provided by user in GUI
    def selectRefInput(self):
        result = QFileDialog.getOpenFileName(self, 'Open File', '', '*.shp')
        if result:
            LineComparisonDialog.refInput = result[0]
            self.lineEdit2.setText(LineComparisonDialog.refInput)
            ComparisonController.openVector(ComparisonController.refLayerName, LineComparisonDialog.refInput,
                                            0, 255, 0, 0.3)

    # Set text output file according to file path provided by user in GUI
    def selectTextOutput(self):
        result = QFileDialog.getSaveFileName(self, 'Save File as', '', '*.txt')
        if result:
            LineComparisonDialog.textOutput = result[0]
            self.lineEdit3.setText(LineComparisonDialog.textOutput)

    # Process input data to create a confusion matrix
    def createConfusionMatrix(self):
        lineLayer = ComparisonController.getLineLayer()
        refLayer = ComparisonController.getrefLineLayer()

        if lineLayer is not None and refLayer is not None:
            if self.doubleSpinBox1.value() <= 0 or self.doubleSpinBox2.value() <= 0:
                ComparisonController.showMessage("Please define a buffer size > 0", Qgis.Critical)
            self.progressBar.setValue(20)

            # Clip data to reference layer
            try:
                extentLayer = ComparisonController.createClipPolygon(refLayer)
                clippedLineLayer = ComparisonController.clipLayer(lineLayer, extentLayer)
                ComparisonController.updateSymbology(clippedLineLayer, 255, 0, 0, 0.3)
                self.progressBar.setValue(40)
            except:
                ComparisonController.showMessage("Error in clipping a layer", Qgis.Critical)

            # Buffer layers
            try:
                bufferLineLayer = ComparisonController.bufferLayer(
                    clippedLineLayer, ComparisonController.lineLayerName, self.doubleSpinBox1.value())
                ComparisonController.updateSymbology(bufferLineLayer, 255, 0, 0, 0.3)

                bufferRefLayer = ComparisonController.bufferLayer(
                    refLayer, ComparisonController.refLayerName, self.doubleSpinBox2.value())
                ComparisonController.updateSymbology(bufferRefLayer, 0, 255, 0, 0.3)
                self.progressBar.setValue(60)
            except:
                ComparisonController.showMessage("Error in buffering a layer", Qgis.Critical)

            # Rasterize
            try:
                pixelSize = min(self.doubleSpinBox1.value(), self.doubleSpinBox2.value())
                rasterizedLineLayer = ComparisonController.rasterizeLayer(
                    bufferLineLayer,ComparisonController.lineLayerName, pixelSize,
                    pixelSize)
                rasterizedRefLayer = ComparisonController.rasterizeLayer(
                    bufferRefLayer,ComparisonController.refLayerName, pixelSize,
                    pixelSize)
                self.progressBar.setValue(80)
            except:
                ComparisonController.showMessage("Error in creating rasterized layer", Qgis.Critical)


            # Compute confusion matrix
            try:
                ComparisonController.computeConfusionMatrix(
                    rasterizedLineLayer, rasterizedRefLayer, pixelSize, LineComparisonDialog.textOutput)
                self.progressBar.setValue(100)
                ComparisonController.plotAccuracy(LineComparisonDialog.textOutput)
            except:
                ComparisonController.showMessage("Error in computing confusion matrix", Qgis.Critical)

