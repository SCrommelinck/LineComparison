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
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .LineComparison_dialog import LineComparisonDialog
import os.path
from .ComparisonController import *


class LineComparison:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            ComparisonController.appName + '_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&'+ComparisonController.appName)
        self.toolbar = self.iface.addToolBar(ComparisonController.appName)
        self.toolbar.setObjectName(ComparisonController.appName)
        self.canvas = qgis.utils.iface.mapCanvas()

        ComparisonController.mainWidget = self

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate(ComparisonController.appName, message)

    def initGui(self):
        # Create action that will start plugin configuration
        action = QAction(QIcon(os.path.dirname(os.path.realpath(__file__)) +
                                    "/icon.png"), ComparisonController.appName, self.iface.mainWindow())
        self.actions.append(action)

        # Add information
        action.setWhatsThis(ComparisonController.appName)

        # Add toolbar button to the Plugins toolbar
        self.iface.addToolBarIcon(action)

        # Add menu item to the Plugins menu
        self.iface.addPluginToMenu("&" + ComparisonController.appName, action)

        # Connect the action to the run method
        action.triggered.connect(self.run)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&'+ComparisonController.appName),
                action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        # Create the dialog (after translation) and keep reference
        dlg = LineComparisonDialog()

        # Show the plugin window and ensure that it stays the top level window
        dlg.setWindowFlags(Qt.WindowStaysOnTopHint)

        # Show the dialog
        dlg.show()

        # Run the dialog event loop
        dlg.exec_()