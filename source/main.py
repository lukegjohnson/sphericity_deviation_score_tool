# main.py

# Simple tool to quickly measure the sphericity deviation score (SDS) from JPGs of anteroposterior and frog-lateral radiographs.
#
# Developed 2024 by Luke Johnson (University of British Columbia) luke.johnson@ubc.ca
#
# Some code derived from Mike Driscoll's blog "The Mouse vs the Python" (blog.pythonlibrary.org),
# under wxWidgets license.
#
# Licensed under GPL v3

# Step 1: open two image viewer windows - AP and frog lat. 

# Step 2: open a window with a calculations table.

# Step 3: populate calculations table with points placed on each figure viewer

from SDSView import ViewWindow, SDSWindow
import FreeSimpleGUI as sg
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

ap_title = "SDS measurement: AP view"
lat_title = "SDS measurement: lat view"
ap_default_image = resource_path("Tutorial AP.png")
lat_default_image = resource_path("Tutorial lat.png")
calc_title = "SDS calculations table"

ap_view = ViewWindow(ap_title, ap_default_image)
ap_view.open_viewer_window()

lat_view = ViewWindow(lat_title, lat_default_image)
lat_view.open_viewer_window()

calc_table = SDSWindow(calc_title)

while True:
	window, event, values = sg.read_all_windows()
	
	if window.Title == ap_title:
		if ap_view.handle_window_event(event, values):
			# handle_window_event returns 1 if window is closed
			break
		#print(ap_view.fig_centres)
		calc_table.update_values(ap_view, lat_view)
		
	elif window.Title == lat_title:
		if lat_view.handle_window_event(event, values):
			break
		#print(lat_view.fig_centres)
		calc_table.update_values(ap_view, lat_view)
		
	elif window.Title == calc_title:
		if calc_table.handle_window_event(event, values):
			break
		
	
	