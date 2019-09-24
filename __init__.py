"""
!/bin/python
-*- coding: utf-8 -*-
/*****************************************************************************
 LineComparison
                                 A QGIS plugin
                              -------------------
        begin                : 2018-08-01
        copyright            : (C) 2019 by Sophie Crommelinck, 
                                University of Twente
        email                : s.crommelinck@utwente.nl
        description          : LineComparison QGIS plugin.
                                This plugin supports line-based accuracy 
                                assessment by comparing two line layers. 
        funding              : H2020 EU project its4land 
                                (#687826, its4land.com)
                                Work package 5: Automate It
        development          : Sophie Crommelinck
        icon                 : Line Graph by Calvin Goodman from Noun Project
 *****************************************************************************/
 
 /*****************************************************************************
 *    This program is free software: you can redistribute it and/or modify    *
 *    it under the terms of the GNU General Public License as published by    *
 *    the Free Software Foundation, either version 3 of the License, or       *
 *    (at your option) any later version.                                     *
 *                                                                            *
 *    This program is distributed in the hope that it will be useful,         *
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           *
 *    GNU General Public License for more details.                            *
 *                                                                            *
 *    You should have received a copy of the GNU General Public License       *
 *    along with this program.  If not, see <https://www.gnu.org/licenses/>.  *
  *****************************************************************************/
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load LineComparison class from file LineComparison.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .LineComparison import LineComparison
    return LineComparison(iface)
