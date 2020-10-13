# from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic)

# Limitations:
# * Cannot update canvas width / height by updating the global variables width / height. Need to use size() method or canvas object.


from ipycanvas import Canvas, hold_canvas
from IPython.display import Code, display
from math import pi
import threading, time, random


DEFAULT_CANVAS_SIZE = (100, 100)
FRAME_RATE = 30
NO_ACTIVITY_THRESHOLD = 5 * 60 # 5 minutes

_sparkplug_active_thread_id = None
_sparkplug_last_activity = 0


class Core():
    # All constants that will be injected into global scope in the user"s cell
    global_constants = {
        "pi": pi
    }
    
    # All methods/fields from this class that will be exposed as global in user"s scope
    global_fields = {
        "canvas", "mouse_x", "mouse_y", "mouse_is_pressed", 
        "width", "height", 
        "size", "fill_style", "fill_rect", "clear"
    }
    
    # All methods that user will be able to define and override
    global_methods = {
        "draw", "setup",
        "mouse_down", "mouse_up", "mouse_moved"
    }
    
    
    def __init__(self, globals_dict):
        self._globals_dict = globals_dict
        self._methods = {}
        
        self.canvas = Canvas()
        self.width, self.height = DEFAULT_CANVAS_SIZE
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_is_pressed = False
    
    
    ### Properties ###

    @property
    def mouse_x(self):
        return self._globals_dict["mouse_x"]
    @mouse_x.setter
    def mouse_x(self, val):
        self._globals_dict["mouse_x"] = val
        
    @property
    def mouse_y(self):
        return self._globals_dict["mouse_y"]
    @mouse_y.setter
    def mouse_y(self, val):
        self._globals_dict["mouse_y"] = val
        
    @property
    def mouse_is_pressed(self):
        return self._globals_dict["mouse_is_pressed"]
    @mouse_is_pressed.setter
    def mouse_is_pressed(self, val):
        self._globals_dict["mouse_is_pressed"] = val
        
    @property
    def width(self):
        return self._globals_dict["width"]
    @width.setter
    def width(self, val):
        self._globals_dict["width"] = val
        self.canvas.width = val
        
    @property
    def height(self):
        return self._globals_dict["height"]
    @height.setter
    def height(self, val):
        self._globals_dict["height"] = val
        self.canvas.height = val
    

    ### Library init ###
    
    # Updates last activity time
    def refresh_last_activity(self):
        global _sparkplug_last_activity
        _sparkplug_last_activity = time.time()

    # Creates canvas and starts thread
    def start(self, methods):
        display(self.canvas)
        
        self.error_text = display(Code(""), display_id=True)
        self._methods = methods

        self.canvas.on_mouse_down(self.on_mouse_down)
        self.canvas.on_mouse_up(self.on_mouse_up)
        self.canvas.on_mouse_move(self.on_mouse_move)

        thread = threading.Thread(target=self.loop)
        thread.start()
    
    # Loop method that handles drawing and setup
    def loop(self):
        global _sparkplug_active_thread_id
        
        # Set active thread to this thread. This will stop any other active thread.
        current_thread_id = threading.current_thread().native_id
        _sparkplug_active_thread_id = current_thread_id
        self.refresh_last_activity()
        
        draw = self._methods.get("draw", None)
        setup = self._methods.get("setup", None)
    
        if setup:
            try:
                setup()
            except Exception as e:
                self.print_error("Error in setup() function: " + str(e))
                return
    
        while True:
            if _sparkplug_active_thread_id != current_thread_id or time.time() - _sparkplug_last_activity > NO_ACTIVITY_THRESHOLD:
                print("stop", current_thread_id)
                return
            
            if not draw:
                return
            
            with hold_canvas(self.canvas):
                try:
                    draw()
                except Exception as e:
                    self.print_error("Error in draw() function: " + str(e))
                    return

            time.sleep(1/FRAME_RATE)
    
    # Prints error to embedded error box
    def print_error(self, msg):
        self.error_text.update(Code(msg))
    
    # Update mouse_x, mouse_y, and call mouse_down handler
    def on_mouse_down(self, x, y):
        self.refresh_last_activity()
        self.mouse_x, self.mouse_y = int(x), int(y)
        self.mouse_is_pressed = True
        
        mouse_down = self._methods.get("mouse_down", None)
        if mouse_down:
            mouse_down()
    
    # Update mouse_x, mouse_y, and call mouse_up handler
    def on_mouse_up(self, x, y):
        self.refresh_last_activity()
        self.mouse_x, self.mouse_y = int(x), int(y)
        self.mouse_is_pressed = False
        
        mouse_up = self._methods.get("mouse_up", None)
        if mouse_up:
            mouse_up()
    
    # Update mouse_x, mouse_y, and call mouse_moved handler
    def on_mouse_move(self, x, y):
        self.refresh_last_activity()
        self.mouse_x, self.mouse_y = int(x), int(y)
            
        mouse_moved = self._methods.get("mouse_moved", None)
        if mouse_moved:
            mouse_moved()
    

    ### Global functions ###
    
    # Sets canvas size
    def size(self, *args):
        if len(args) == 2:
            self.width = args[0]
            self.height = args[1]
    
    # Sets fill style
    # TODO: Only accepts one argument, should also be able to accept: r, g, b 
    def fill_style(self, *args):
        if len(args) == 1:
            self.canvas.fill_style = args[0]
    
    # Draws filled rect
    def fill_rect(self, *args):
        if len(args) < 4:
            raise TypeError("{} expected at least {} arguments, got {}".format("rect", 4, len(args)))
        if len(args) == 4:
            x, y, w, h = args
            self.canvas.fill_rect(x, y, w, h)
        else:
            raise TypeError("{} expected at most {} arguments, got {}".format("rect", 4, len(args)))
    
    # Clears canvas
    def clear(self, *args):
        self.canvas.clear()
    