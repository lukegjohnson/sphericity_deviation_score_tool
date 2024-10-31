# SDSview.py

# Image viewer based on Mike Driscoll's here: https://www.blog.pythonlibrary.org/2021/02/16/creating-an-image-viewer-with-pysimplegui/ (wxWidgets license)
# 
# Changes made: 
# - Switched to FreeSimpleGUI
# - Opens with default image (tutorial for SDS measurement), 
# - Zoom in/out and move buttons
# - Automatic annotation function with undo button

import io
import os
import FreeSimpleGUI as sg
import numpy as np
from PIL import Image
import pyperclip

class ViewWindow:
    def __init__(self, window_title, image_filepath):
        self.file_types = [("JPEG (*.jpg)", "*.jpg"),
              ("All files (*.*)", "*.*")]
        
        self.zoom_level = 100
        self.zoom_in_multiplier = np.sqrt(2)
        self.zoom_out_multiplier = 1/self.zoom_in_multiplier
        self.graph_origin = -256 # canvas size is 512x512 so -256 would give graph resolution of 1 step per pixel.
                
        self.point_size = 5
        
        self.window_title = window_title
        self.image_filepath = image_filepath
        
        self.window = self.graph = None
        self.dragging = self.moving = False
        self.image = self.image_top_left = self.image_id = None
        self.start_point = self.end_point = self.prior_shape = self.prior_shape_centre = None
        self.sds_step = 0
        self.figs = []
        self.fig_centres = []
        self.net_x, self.net_y = 0, 0
        self.lastxy = None
        self.r_mcc = self.r_mic = None
              
    def open_viewer_window(self):
        layout = [
        	[
                sg.Text("Image File"),
                sg.Input(size=(25, 1), key="-FILE-"),
                sg.FileBrowse(file_types=self.file_types),
                sg.Button("Load Image"),
            ],
            [
                sg.Text("Image Controls"),
                sg.Button("Move", key="-MOVE-", button_color=None),
                sg.Button("Zoom in", key="-ZOOMIN-"),
                sg.Button("Zoom out", key="-ZOOMOUT-"),
                sg.Text("Zoom level:"),
                sg.Text(" " + str(self.zoom_level) + "%", key="-ZOOM-"),
                sg.Button("Undo", key="-UNDO-"),
            ],
            [sg.Graph(
                canvas_size=(512,512),
                graph_bottom_left= (self.graph_origin, self.graph_origin), # make (0, 0) be in middle
                graph_top_right= (-self.graph_origin,-self.graph_origin), # graph resolution = 1/10 pixel
                key="-GRAPH-",
                change_submits=True, # mouse click events
                drag_submits=True)],
        ]
    
        self.window = sg.Window(self.window_title, layout, finalize=True)
        
        self.graph = self.window["-GRAPH-"]
        
        self.load_image(self.image_filepath)        
    
        #while True:
            #event, values = self.window.read()
            
            #if self.handle_window_event(event, values):
                #break
                                
    # I should be able to sort out drawing the points and circles by stealing stuff from here. https://docs.pysimplegui.com/en/latest/cookbook/ecookbook/elements/graph/graph-element-drawing-and-dragging/
    
        #self.window.close()
        
    def handle_window_event(self, event, values):
        if event == "Exit" or event == sg.WIN_CLOSED:
            return 1
        if event == "Load Image":
            self.image_filepath = values["-FILE-"]
            self.load_image(self.image_filepath)
                
            self.net_x = self.net_y = 0
                            
        if event == "-MOVE-": # toggle graph move mode
            self.moving = not self.moving
            self.set_moving_vis(event)
            
        if event == "-ZOOMIN-":
            # Easier to zoom with consistent multiplier (square root of two means two button clicks doubles zoom level.
            
            if self.image is not None: 
                self.zoom_level = self.zoom_level*self.zoom_in_multiplier
                
                self.zoom_image(self.zoom_in_multiplier)
                
                self.window["-ZOOM-"].update(" " + str(np.round(self.zoom_level)) + "%")
                
        if event == "-ZOOMOUT-":
            # Easier to zoom with consistent multiplier (square root of two means two button clicks doubles zoom level.
            
            if self.image is not None: 
                self.zoom_level = self.zoom_level*self.zoom_out_multiplier

                self.zoom_image(self.zoom_out_multiplier)
                               
                self.window["-ZOOM-"].update(" " + str(np.round(self.zoom_level)) + "%")
                            
        if event == "-GRAPH-":
            x, y = values["-GRAPH-"]
            if not self.dragging:
                self.start_point = (x, y)
                self.end_point = (x, y)
                self.dragging = True
                drag_figures = self.graph.get_figures_at_location((x,y))
                self.lastxy = x, y
            else:
                self.end_point = (x, y)
            if self.prior_shape:
                self.graph.delete_figure(self.prior_shape)
            delta_x, delta_y = x - self.lastxy[0], y - self.lastxy[1]
            self.lastxy = x,y
            if None not in (self.start_point, self.end_point):
                if self.moving:
                    self.graph.move(delta_x, delta_y)
                    self.net_x += delta_x
                    self.net_y += delta_y
                    
                    # Add delta_x and delta_y to all of the stored points as well
                    for i in range(len(self.fig_centres)):
                        cx, cy = self.fig_centres[i]
                        cx += delta_x
                        cy += delta_y
                        self.fig_centres[i] = (cx, cy)
                        
                else:
                    if self.sds_step < 2:
                        self.prior_shape = self.graph.draw_point(self.end_point, size=self.point_size, color='white')
                        self.prior_shape_centre = self.end_point
                    elif self.sds_step == 2:
                        # Calculating circle through three points
                        circle = circle_c_r_from_three_points(self.fig_centres[0], self.fig_centres[1], self.end_point)
                        # circle[0] is centre (tuple), circle[1] is radius
                        
                        self.prior_shape = self.graph.draw_circle(circle[0], circle[1], fill_color=None, line_color='white')
                        self.prior_shape_centre = circle[0]
                        self.prior_shape_radius = circle[1]
                    elif self.sds_step == 3:
                        # Concentric circle
                        
                        # Calcululate radius from point
                        (px, py) = self.end_point
                        (ox, oy) = self.fig_centres[-1]
                        
                        p = px + py*1j
                        o = ox + oy*1j
                        
                        r = abs(p-o)
                        
                        self.prior_shape = self.graph.draw_circle(self.fig_centres[-1], r, fill_color=None, line_color='white')
                        self.prior_shape_centre = self.fig_centres[-1]
                        self.prior_shape_radius = r
                       
                    
        if event == "-UNDO-":
            # Delete most recently drawn figure, remove from figs list, 
            # decrement sds_step
            if self.sds_step == 0:
                pass
            else:
                self.graph.delete_figure(self.figs[-1])
                self.figs = self.figs[:-1]
                self.fig_centres = self.fig_centres[:-1]
                self.sds_step -= 1
            
                    
        elif event.endswith('+UP'):  # The drawing has ended because mouse up
            self.start_point, self.end_point = None, None  # enable grabbing a new rect
            self.dragging = False
            
            if not self.moving:
                if self.sds_step < 4:

                    self.figs.append(self.prior_shape)
                    self.fig_centres.append(self.prior_shape_centre)
                                                                
                    if self.sds_step == 2: self.r_mic = self.prior_shape_radius
                    if self.sds_step == 3: self.r_mcc = self.prior_shape_radius
                    
                    self.sds_step += 1
                
            self.prior_shape = self.prior_shape_centre = self.prior_shape_radius = None
            
        return 0
        
    def set_moving_vis(self, event):
        self.window[event].update(button_color='white on gray' if self.moving else ('white', sg.theme_button_color_background()))
        self.graph.Widget.config(cursor='fleur' if self.moving else 'arrow') 
        
    def load_image(self, filename):
                
        if os.path.exists(filename):
            # Delete previous image version
            if self.image is not None:
                self.graph.delete_figure(self.image_id)
            
            self.image = Image.open(filename)
            bio = io.BytesIO()
            self.image.save(bio, format="PNG")
            
            # Draw image centred on window
            (width, height) = self.image.size
            self.image_top_left = (-width/2, height/2)
            
            self.image_id = self.graph.draw_image(data=bio.getvalue(), location=self.image_top_left)
        else:
            print("file does not exist!")
            
    def zoom_image(self, zoom_multiplier):
        # First - delete image from graph
        self.graph.delete_figure(self.image_id)
        
        # Calculate image location prior to zoom
        (itl_x, itl_y) = self.image_top_left
        itl_x += self.net_x
        itl_y += self.net_y
        self.image_top_left = (itl_x, itl_y)
        
        # Then calculate new image size OR reload image if at 100%
        if np.round(self.zoom_level) == 100:
            self.image = Image.open(self.image_filepath)
        else:
            width, height = self.image.size
            new_dims = (int(width*zoom_multiplier), int(height*zoom_multiplier))
            self.image = self.image.resize(new_dims)
            
        bio = io.BytesIO()
        self.image.save(bio, format="PNG")
        
        # Redraw resized image at original location
        self.image_id = self.graph.draw_image(data=bio.getvalue(), location=self.image_top_left)
        self.net_x = self.net_y = 0
        
        # Scale figures and image top left point (not image itself)
        self.graph.Widget.scale("all", 256, 256, zoom_multiplier, zoom_multiplier)
        self.point_size = self.point_size/zoom_multiplier
        
        # Calculate new graph coordinates
        self.graph_origin = self.graph_origin/zoom_multiplier
        self.graph.change_coordinates((self.graph_origin,self.graph_origin), (-self.graph_origin,-self.graph_origin))
       
        self.graph.send_figure_to_back(self.image_id)
        
class SDSWindow:
    def __init__(self, window_title):
        self.r_mic_ap = self.r_mcc_ap = self.r_ap = self.r_mic_lat = self.r_mcc_lat = self.r_lat = self.RE_ap = self.RE_lat = self.ED = self.SDS = None
        self.window_title = window_title
        
        self.numeric_values = [None, None, None, None, None, None, None, None, None, None]
        self.text_values = ["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]
        
        self.table = sg.Table([self.text_values], headings=["r_mic_ap", "r_mcc_ap", "r_ap", "r_mic_lat", "r_mcc_lat", "r_lat", "RE_ap", "RE_lat", "ED", "SDS"], key="-TABLE-", col_widths = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10], auto_size_columns = False)
        
        layout = [[self.table],
            [sg.Button("Copy to clipboard", key="-COPY-")]]
        self.window = sg.Window(self.window_title, layout, finalize=True)
        
    def handle_window_event(self, event, values):
        if event == "Exit" or event == sg.WIN_CLOSED:
            return 1
        if event == "-COPY-":
            self.copy_values()
        
    def update_values(self, ap_window, lat_window):
        # can calculate various values based on the current measurement step in each window. 
        # if window.sds_step = 3, r and RE can be calculated for that window, and if sds_step = 3 in both, ED and SDS can also be calculated. 
        
        # Start with AP window
        if ap_window.sds_step < 3:
            self.r_mic_ap = self.r_mcc_ap = self.r_ap = self.RE_ap = None
        elif ap_window.sds_step == 3:
            self.r_mic_ap = ap_window.r_mic
            self.r_mcc_ap = self.r_ap = self.RE_ap = None
        elif ap_window.sds_step == 4:
            self.r_mic_ap = ap_window.r_mic
            self.r_mcc_ap = ap_window.r_mcc
            
            self.r_ap = (self.r_mic_ap + self.r_mcc_ap)/2
            self.RE_ap = 100*(self.r_mcc_ap - self.r_mic_ap)/self.r_ap
        else:
            # Something has gone wrong
            raise IndexError('SDS step should not be more than 4')
        
        # Then do lat window
        if lat_window.sds_step < 3:
            self.r_mic_lat = self.r_mcc_lat = self.r_lat = self.RE_lat = None
        elif lat_window.sds_step == 3:
            self.r_mic_lat = lat_window.r_mic
            self.r_mcc_lat = self.r_lat = self.RE_lat = None
        elif lat_window.sds_step == 4:
            self.r_mic_lat = lat_window.r_mic
            self.r_mcc_lat = lat_window.r_mcc
            
            self.r_lat = (self.r_mic_lat + self.r_mcc_lat)/2
            self.RE_lat = 100*(self.r_mcc_lat - self.r_mic_lat)/self.r_lat
        else:
            # Something has gone wrong
            raise IndexError('SDS step should not be more than 4')
        
        # If RE is not none for both, calculate ED and SDS
        if self.RE_ap is not None and self.RE_lat is not None:
            if self.r_ap > self.r_lat:
                self.ED = 100*(self.r_ap - self.r_lat)/self.r_lat
            else:
                self.ED = 100*(self.r_lat - self.r_ap)/self.r_ap
                
            self.SDS = self.RE_ap + self.RE_lat + self.ED
        else:
            self.ED = self.SDS = None
        
        # Add calculations into self.numeric_values and self.text_values every time
        self.numeric_values = [self.r_mic_ap, self.r_mcc_ap, self.r_ap, self.r_mic_lat, self.r_mcc_lat, self.r_lat, self.RE_ap, self.RE_lat, self.ED, self.SDS]
        
        for i in range(len(self.numeric_values)):
            if self.numeric_values[i] is not None:
                self.text_values[i] = str(np.round(self.numeric_values[i], decimals=4))
            else:
                self.text_values[i] = 'N/A'
                
        self.window["-TABLE-"].update([self.text_values])
        
    def copy_values(self):
        # copy text values as a tab-separated list into the clipboard
        output_string = ''
        
        # write all but last value with tab following
        for i in range(len(self.text_values)-1):
            output_string += str(self.text_values[i] + '\t')
            
        # write last value without tab afterward
        output_string += str(self.text_values[-1])
            
        pyperclip.copy(output_string)          
        

### Utility function!
def circle_c_r_from_three_points(p1, p2, p3):
    # Given three 2D tuples as input, return centre and radius of circle that passes through all three.
    # We're using imaginary numbers here! From: https://stackoverflow.com/questions/28910718/give-3-points-and-a-plot-circle
    #print(p1, p2, p3)
    
    # TODO integer arithmetic only! 
    
    x = p1[0] + p1[1]*1j
    y = p2[0] + p2[1]*1j
    z = p3[0] + p3[1]*1j
    
    w = z-x
    w /= y-x
    c = (x-y)*(w-abs(w)**2)/2j/w.imag-x
    
    centre = (-c.real, -c.imag)
    radius = abs(c + x)
    circ = [centre, radius]
    
    return circ