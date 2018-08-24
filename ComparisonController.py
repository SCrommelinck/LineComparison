# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LineComparison
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

# Import required modules
from PyQt5.QtCore import QSettings, QTranslator, qVersion, Qt,  QVariant
from PyQt5.QtGui import QIcon, QColor, QPixmap
from PyQt5.QtWidgets import QAction, QFileDialog, QToolBar

import qgis
from qgis.core import *
from qgis.utils import *

import processing
import os

import numpy as np
import matplotlib.pyplot as plt

class ComparisonController:
    
    # Define layer and plugin name
    appName = 'LineComparison'
    pluginName = appName + ' plugin'
    lineLayerName = 'input lines'
    refLayerName = 'reference lines'
    
    mainWidget = None

    @staticmethod
    def showMessage(message, level=Qgis.Info, duration=5):
        qgis.utils.iface.mainWindow().statusBar().clearMessage()
        qgis.utils.iface.messageBar().pushMessage(ComparisonController.pluginName, message, level, duration)
        qgis.utils.iface.mainWindow().repaint()

    @staticmethod
    def getActiveLayer():
        return qgis.utils.iface.activeLayer()
    
    @staticmethod
    def setActiveLayer(layer):
        if not isinstance(layer, QgsMapLayer):
            layer = getLayerByName(layer)
        if layer is not None:
            qgis.utils.iface.setActiveLayer(layer)
    
    @staticmethod
    def setLayerVisibility (layer, visible):
        if layer is not None:
            layerNode = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
            if layerNode is not None:
                layerNode.setItemVisibilityChecked(visible)
                return True
        return False

    @staticmethod
    def getLayerByName (name, showError=False):
        try:
            return QgsProject.instance().mapLayersByName(name)[0]
        except:
            if showError:
                ComparisonController.showMessage("Layer %s not found" % name, Qgis.Critical)
            return None

    @staticmethod
    def addRasterLayer (layerName, fileName):
        return qgis.utils.iface.addRasterLayer(fileName, layerName)

    @staticmethod
    def checkRasterLayer (layerName, fileName):
        layer = ComparisonController.getLayerByName(layerName)
        if layer is None:
            if fileName:
                try:
                    return ComparisonController.addRasterLayer(layerName, fileName)
                except:
                    ComparisonController.showMessage("Unable to open %s" % fileName, Qgis.Critical)
            return None
        ComparisonController.showMessage("%s already loaded" % layerName, Qgis.Warning)
        return layer

    @staticmethod
    def addVectorLayer (layerName, fileName):
        layer = qgis.utils.iface.addVectorLayer(fileName, layerName, 'ogr')
        if layer is not None:
            layer.setName(layerName)
        return layer

    @staticmethod
    def checkVectorLayer (layerName, fileName, showMsg=True):
        layer = ComparisonController.getLayerByName(layerName)
        if layer is None:
            if fileName:
                try:
                    return ComparisonController.addVectorLayer(layerName, fileName)
                except:
                    ComparisonController.showMessage("Unable to open %s" % fileName, Qgis.Critical)
            return None
        if showMsg:
            ComparisonController.showMessage("%s already loaded" % layerName, Qgis.Warning)
        return layer

    @staticmethod
    def getLineLayer(showError=True):
        return ComparisonController.getLayerByName(ComparisonController.lineLayerName, showError)

    def getrefLineLayer(showError=True):
        return ComparisonController.getLayerByName(ComparisonController.refLayerName, showError)

    # Load layer to canvas
    @staticmethod
    def openVector(layerName, vectorFile, red, green, blue, size):
        # Check if layer is already loaded
        vectorLayer = ComparisonController.checkVectorLayer(layerName, vectorFile)
        if vectorLayer is not None:
            ComparisonController.setActiveLayer(vectorLayer)
            ComparisonController.updateSymbology(vectorLayer, red, green, blue, size)
        return vectorLayer

    # Get layer extent
    @staticmethod
    def getExtent(layer):
        extent = layer.extent()
        xmin = extent.xMinimum()
        xmax = extent.xMaximum()
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()
        return "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax)

    # Set symbology for vector layer
    @staticmethod
    def updateSymbology(layer, red, green, blue, size):
        if layer is not None:
            # Get symbology renderer
            singleSymbolRenderer = layer.renderer()
            symbol = singleSymbolRenderer.symbol()

            # Set color and width
            symbol.setColor(QColor.fromRgb(red, green, blue))
            # For lines
            if type(symbol) == QgsLineSymbol:
                symbol.setWidth(size)
            # For points
            if type(symbol) == QgsMarkerSymbol:
                symbol.setSize(size)

            # Repaint layer
            layer.triggerRepaint()

            # Repaint layer legend
            qgis.utils.iface.layerTreeView().refreshLayerSymbology(layer.id())


    @staticmethod
    def createClipPolygon(layer):
        # Define extent
        extent = layer.extent()
        xmin = extent.xMinimum()
        xmax = extent.xMaximum()
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()

        # Create new layer to clip layer to extent
        extentLayer = QgsVectorLayer("Polygon?crs=EPSG:4326&field=ID:integer", "extentLayer", "memory")
        extentLayer.setCrs(layer.crs())
        provider = extentLayer.dataProvider()

        # Add a feature
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPolygonXY(
            [[QgsPointXY(xmin, ymin), QgsPointXY(xmin, ymax), QgsPointXY(xmax, ymax), QgsPointXY(xmax, ymin)]]))
        feat.setAttributes([1])
        provider.addFeatures([feat])
        return extentLayer


    @staticmethod
    def clipLayer(bottomLayer, overlayLayer):
        clipLineLayer = ComparisonController.checkVectorLayer(ComparisonController.lineLayerName + ' clipped', None, False)
        if clipLineLayer is None:
            # Create clip
            processing.runAndLoadResults('qgis:clip',
                                         {"INPUT": bottomLayer,
                                          "OVERLAY": overlayLayer,
                                          "OUTPUT": 'memory:clip'})

            # Update layer name and symbology
            clipLineLayer = ComparisonController.getActiveLayer()
            clipLineLayer.setName(ComparisonController.lineLayerName + ' clipped')
            ComparisonController.showMessage("%s clipped to the extent of the %s." %
                                             (ComparisonController.lineLayerName, ComparisonController.refLayerName),
                                             Qgis.Info)
        return clipLineLayer


    @staticmethod
    def bufferLayer(layer, layerName, bufferSize):
        bufferedLayer = ComparisonController.checkVectorLayer(layerName + ' buffered', None, False)
        if bufferedLayer is None:
            # Create buffer
            processing.runAndLoadResults('qgis:buffer',
                                         {"INPUT": layer,
                                          "DISTANCE": bufferSize,
                                          "SEGMENTS":5,
                                          "DISSOLVE": True,
                                          "END_CAP_STYLE": 0,
                                          "JOIN_STYLE": 0,
                                          "MITER_LIMIT":2,
                                          "OUTPUT":'memory:buffer'})

            # Update layer name and symbology
            bufferedLayer = ComparisonController.getActiveLayer()
            bufferedLayer.setName(layerName + ' buffered')

            ComparisonController.showMessage("%s buffered with %.2fm." %
                                             (layerName, bufferSize),
                                             Qgis.Info)
        return bufferedLayer

    @staticmethod
    def rasterizeLayer(layer, layerName, height, width):
        rasterizedLayer = ComparisonController.checkRasterLayer(layerName + ' rasterized', None)
        if rasterizedLayer is None:

            # Rasterize Layer
            rasterFilename = QgsProcessingUtils.generateTempFilename(layerName + '_rasterized.tif')
            processing.run('gdal:rasterize',
                                         {"INPUT": layer,
                                          "BURN": 1,
                                          "UNITS": 1,
                                          "HEIGHT": height,
                                          "WIDTH": width,
                                          "EXTENT": ComparisonController.getExtent(layer),
                                          "NODATA": 0,
                                          "DATA_TYPE":1,
                                          "INIT":0,
                                          "INVERT": False,
                                          "OUTPUT": rasterFilename})

            nulledRasterFilename = QgsProcessingUtils.generateTempFilename(layerName + '_nulled.sdat')
            processing.run('saga:rastercalculator',
                           {"GRIDS": rasterFilename,
                            "XGRIDS": '',
                            "FORMULA": 'a*1',
                            "RESAMPLING": 0,
                            "USE_NODATA": True,
                            "TYPE": 2,
                            "RESULT": nulledRasterFilename})

            translatedRasterFilename = QgsProcessingUtils.generateTempFilename(layerName + '_translated.tif')
            processing.run('gdal:translate',
                           {"INPUT": nulledRasterFilename,
                            "TARGET_CRS": None,
                            "NODATA": None,
                            "COPY_SUBDATASETS": False,
                            "OPTIONS": '',
                            "DATA_TYPE": 5,
                            "OUTPUT": translatedRasterFilename})

            rasterizedLayer = ComparisonController.checkRasterLayer(layerName + ' rasterized',
                                                                    translatedRasterFilename)

            ComparisonController.showMessage("%s rasterized." %
                                             layerName,
                                             Qgis.Info)

        return os.path.abspath(translatedRasterFilename)

    @staticmethod
    def computeConfusionMatrix(classificationLayer, referenceLayer, cellSize, outputFile):
        processing.run('grass7:r.kappa',
                       {"classification": classificationLayer,
                        "reference": referenceLayer,
                        "title": 'ACCURACY ASSESSMENT',
                        "-h": False,
                        "-w": False,
                        "GRASS_REGION_CELLSIZE_PARAMETER": cellSize,
                        "GRASS_REGION_PARAMETER": None,
                        "output": outputFile})

        ComparisonController.showMessage("Confusion matrix created and saved in %s" %
                                         outputFile,
                                         Qgis.Success)
    @staticmethod
    def plotAccuracy(txtFile):
        # Open input file
        try:
            accuracyFile = open(txtFile, 'r')
        except:
            ComparisonController.showMessage("%s could not be opened" %
                                             outputFile,
                                             Qgis.Critical)

        # Read error of commission from input file
        lines = accuracyFile.readlines()
        line = lines[17]
        vals = line.strip().split('\t')
        y = []
        y.append(float(vals[1]))
        y.append(100-y[0])
        accuracyFile.close()

        # Create plot
        fig, ax = plt.subplots(figsize=(4,3))
        index = np.arange(2)
        bar_width = 0.6
        ax.yaxis.grid()
        ax.set_ylim([0, 100])
        ax.set_xlim([-0.6,1.6])
        rects = plt.bar(index, y, bar_width,color= 'grey')
        def autolabel(rects):
            font = {'color': 'white',
                    'size': 10,
                    }
            for rect in rects:
                height = rect.get_height()
                ax.text(rect.get_x() + rect.get_width()/2., height-10,
                        '%d%%' % int(height), fontdict=font,
                        ha='center', va='bottom')
        autolabel(rects)
        plt.ylabel('error [%]')
        plt.title('Accuracy Assessment Overview')
        plt.xticks(index, ('error of \ncommission\n' + r'$\frac{FP}{FP+TP}$', 'correctness\n' + r'$\frac{TP}{FP+TP}$'))
        plt.legend()
        plt.tight_layout()
        plt.show()

"""
Code Snippets:
# Syntax for processing modules
    processing.algorithmHelp('grass7:r.kappa')
    
# Update attribute table
provider = bufferedLayer.dataProvider()
provider.addAttributes([QgsField("Line", QVariant.Int)])
bufferedLayer.updateFields()
bufferedLayer.startEditing()
for feature in bufferedLayer.getFeatures():
    feature.setAttribute("Line", 1)
    bufferedLayer.updateFeature(feature)
bufferedLayer.commitChanges()
"""