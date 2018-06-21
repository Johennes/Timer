#!/usr/bin/python

import pygtk, gtk, gobject, cairo
import math
import ConfigParser
import os
import StringIO

class Timer(gobject.GObject):
    """
    Timer.
    """
    
    def __init__(self, interval = 0.0, timeout = 0.0, time = 0.0):
        """
        Constructor.
        """
        
        super(Timer, self).__init__() # Call constructor of super-class
        
        # Register signals
        gobject.signal_new('timer-updated', Timer, gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE, (Timer,))
        gobject.signal_new('timer-finished', Timer, gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE, (Timer,))
        
        # Initialize private variables
        self._running = False
        self.interval = interval
        self.timeout = timeout
        self.time = time
    
    def running():
        """
        Holds the timer's event source id or false if the timer is not
        running.
        """
        
        def fget(self): return self._running
        
        return locals()
    
    running = property(**running())
    
    def interval():
        """
        Update-interval in milliseconds as float.
        """
        
        def fget(self): return self._interval
        
        def fset(self, interval):
            assert not self._running
            self._interval = interval
        
        return locals()
    
    interval = property(**interval())
    
    def timeout():
        """
        Global timeout in seconds as float.
        """
        
        def fget(self): return self._timeout
        
        def fset(self, timeout):
            assert not self._running
            self._timeout = timeout
        
        return locals()
    
    timeout = property(**timeout())
    
    def time():
        """
        Current time in seconds as float.
        """
        
        def fget(self): return self._time
        
        def fset(self, time):
            self._time = time
            if self._running: self.emit('timer-updated', self)
        
        return locals()
    
    time = property(**time())
    
    def start(self):
        """
        Starts the timer.
        """
        
        self._running = gobject.timeout_add(int(self._interval * 1000.0),
            self.update)
        self.emit('timer-updated', self)
    
    def stop(self):
        """
        Stops the timer.
        """
        
        gobject.source_remove(self._running)
        self._running = False
    
    def update(self):
        """
        Updates current time. Stops the timer when zero is reached.
        """
        
        if self._time <= self._interval:
            self._time = 0.0
            self._running = False
            self.emit('timer-finished', self)
        else: self._time -= self._interval
        
        self.emit('timer-updated', self)
        
        return self._running

class PieDrawer(object):
    """
    Performs the actual pie drawing.
    """
    
    def __init__(self, fg_color = (0, 0, 0), bg_color = (1, 1, 1),
                 graphic_path = None):
        """
        Constructor.
        """
        
        # Initialize private variables
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.graphic_path = graphic_path
    
    def fg_color():
        """
        Foreground color as rgb tuple.
        """
        
        def fget(self): return self._fg_color
        
        def fset(self, color): self._fg_color = color
        
        return locals()
    
    fg_color = property(**fg_color())
    
    def bg_color():
        """
        Background color as rgb tuple in [(0,0,0)..(1,1,1)].
        """
        
        def fget(self): return self._bg_color
        
        def fset(self, color): self._bg_color = color
        
        return locals()
    
    bg_color = property(**bg_color())
    
    def graphic_path():
        """
        Path to graphic file.
        """
        
        def fget(self): return self._graphic_path
        
        def fset(self, path):
            self._graphic_path = path
            if path:
                self._graphic_surface = cairo.ImageSurface.create_from_png(
                    self._graphic_path)
                self._graphic_pattern = cairo.SurfacePattern(
                    self._graphic_surface)
                self._graphic_scaler = cairo.Matrix()
                self._graphic_pattern.set_filter(cairo.FILTER_BEST)
                self._graphic_dimension = max(self._graphic_surface.get_width(),
                    self._graphic_surface.get_height())
                self._scale = 1.0
            else:
                self._graphic_surface = None
                self._graphic_pattern = None
                self._graphic_scaler = None
                self._graphic_dimension = 0
                self._scale = 0.0
        
        return locals()
    
    graphic_path = property(**graphic_path())
    
    def draw_partial_pie(self, context, x, y, radius, angle):
        """
        Draws a partial pie.
        """
        
        context.move_to(x, y)
        context.arc(x, y, radius, -math.pi / 2.0, -math.pi / 2.0 + angle)
        context.close_path()
        context.fill()
    
    def draw(self, fraction, context, x, y, radius):
        """
        Draws the pie.
        """
        
        angle = 2.0 * math.pi * fraction # Calculate angle
        
        # Draw foreground pie
        if self._graphic_path:
            # Potentially scale image
            scale = self._graphic_dimension / 2.0 / radius
            if scale != self._scale and scale > 1.0:
                self._graphic_scaler.scale(scale / self._scale,
                    scale / self._scale)
                self._scale = scale
                self._graphic_pattern.set_matrix(self._graphic_scaler)
            
            # Potentially translate image
            translate_x = x - self._graphic_surface.get_width() / self._scale / 2.0 
            translate_y = y - self._graphic_surface.get_height() / self._scale / 2.0 
            context.translate(translate_x, translate_y)
            x -= translate_x
            y -= translate_y
            
            # Setup source and radius to include square
            context.set_source(self._graphic_pattern)
            radius *= math.sqrt(2.0)
        else: context.set_source_rgb(*self._fg_color)
        self.draw_partial_pie(context, x, y, radius, angle)
        
        # Draw background pie
        if self._bg_color and not self._graphic_path:
            context.set_source_rgb(*self._bg_color)
            self.draw_partial_pie(context, x, y, radius, angle)

class PieWidget(gtk.DrawingArea):
    """
    Pie-meter GTK widget.
    """
    
    def __init__(self, fraction = 0.0, fg_color = (0, 0, 0),
                 bg_color = (1, 1, 1)):
        """
        Constructor.
        """
        
        super(PieWidget, self).__init__() # Call constructor of super-class
        
        # Initialize private variables
        self._fraction = fraction
        self._drawer = PieDrawer(fg_color, bg_color)
        
        self.connect('expose-event', self.expose) # Connect expose event
    
    def fraction():
        """
        The fraction of the pie that is to be displayed as float in the
        range 0.0 .. 1.0.
        """
        
        def fget(self): return self._fraction
        
        def fset(self, fraction):
            self._fraction = fraction
            self.redraw()
        
        return locals()
    
    fraction = property(**fraction())
    
    def drawer():
        """
        The PieDrawer instance.
        """
        
        def fget(self): return self._drawer
        
        return locals()
    
    drawer = property(**drawer())
    
    def expose(self, widget, event):
        """
        Callback funtion for expose events.
        """
        
        # Get context and setup clipping
        context = widget.window.cairo_create()
        context.rectangle(event.area.x, event.area.y, event.area.width,
            event.area.height)
        context.clip()
        
        self.draw(context) # Draw pie
        
        return False # Let event propagate further
    
    def draw(self, context):
        """
        Draws the pie.
        """
        
        # Calculate pie center and radius
        alloc = self.get_allocation()
        x = alloc.width / 2.0
        y = alloc.height / 2.0
        radius = min(alloc.width / 2.0, alloc.height / 2.0)
        
        # Draw the pie
        self._drawer.draw(self._fraction, context, x, y, radius)
    
    def redraw(self):
        """
        Triggers redrawing of widget.
        """
        
        if self.window:
            alloc = self.get_allocation()
            rect = gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
            self.window.invalidate_rect(rect, True)
            self.window.process_updates(True)

class TrayIcon(object):
    """
    Implements a tray icon for the timer application.
    """
    
    def __init__(self, file = None, fraction = 0.0, fg_color = (0, 0, 0),
                 bg_color = (1, 1, 1)):
        """
        Constructor.
        """
        
        super(TrayIcon, self).__init__() # Call constructor of super-class
        
        # Initialize private variables
        self._fraction = fraction
        self._drawer = PieDrawer(fg_color, bg_color)
        
        # Initialize status icon
        self._file = file
        if file:
            self._status_icon = gtk.status_icon_new_from_file(file)
            self._from_file = True
        else:
            self._status_icon = gtk.status_icon_new_from_pixbuf(
                self.draw_to_pixbuf())
            self._from_file = False
    
    def fraction():
        """
        The fraction of the pie that is to be displayed as float in the
        range 0.0 .. 1.0.
        """
        
        def fget(self): return self._fraction
        
        def fset(self, fraction):
            self._fraction = fraction
            self.update()
        
        return locals()
    
    fraction = property(**fraction())
    
    def drawer():
        """
        The PieDrawer instance.
        """
        
        def fget(self): return self._drawer
        
        return locals()
    
    drawer = property(**drawer())
    
    def status_icon():
        """
        The GTK StatusIcon widget.
        """
        
        def fget(self): return self._status_icon
        
        return locals()
    
    status_icon = property(**status_icon())
    
    def from_file():
        """
        If true, the tray icon is displayed from file.
        """
        
        def fget(self): return self._from_file
        
        return locals()
    
    def file():
        """
        Holds the relative path to the most recently used icon file.
        """
        
        def fget(self): return self._file
        
        return locals()
    
    file = property(**file())
    
    def set_from_file(self, file = None):
        """
        Sets the tray icon from file.
        """
        
        if not file:
            assert self._file
            file = self._file
        
        self._from_file = True
        self._status_icon.set_from_file(file)
    
    def unset_from_file(self):
        """
        Switches the tray icon to the dynamic pie display.
        """
        
        self._from_file = False
        self.update()
        
    def draw_to_pixbuf(self):
        """
        Draws a new icon and returns it as pixbuf.
        """
        
        # Calculate pie center and radius
        size = self.status_icon.get_size()
        x = y = size / 2.0
        radius = size / 2.0 - 1
        
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
        context = cairo.Context(surface)
        
        self._drawer.draw(self._fraction, context, x, y, radius)
        
        # Workaround to convert the Cairo surface to a GDK pixbuf. See
        # http://mikedesjardins.us/wordpress/category/cairo/ for more
        # information.
        file = StringIO.StringIO()
        surface.write_to_png(file)
        file.seek(0)
        loader = gtk.gdk.PixbufLoader()
        loader.write(file.getvalue())
        loader.close()
        file.close()
        
        return loader.get_pixbuf()
    
    def update(self):
        """
        Updates the status icon.
        """
        
        if not self._from_file:
            self._status_icon.set_from_pixbuf(self.draw_to_pixbuf())
    
    def alert(self):
        """
        Alerts about a finished timeout.
        """
        
        self._status_icon.set_blinking(True)
    
    def unalert(self):
        """
        Removes any alerts about a finished timeout.
        """
        
        self._status_icon.set_blinking(False)

class TimerApp:
    """
    Timer application.
    """
    
    def __init__(self, root):
        """
        Constructor.
        """
        
        # Register stock items
        items = (
            ('timer-start', 'Start', 0, 0, None),
            ('timer-stop', 'Stop', 0, 0, None),
            ('timer-pause', 'Pause', 0, 0, None),
            ('timer-continue', 'Continue', 0, 0, None),
            ('timer-restart', 'Restart', 0, 0, None),
            ('timer-back', 'Back', 0, 0, None)
        )
        gtk.stock_add(items)
        
        # Set stock icons
        icons = (
            ('timer-start', gtk.STOCK_MEDIA_PLAY),
            ('timer-stop', gtk.STOCK_MEDIA_STOP),
            ('timer-pause', gtk.STOCK_MEDIA_PAUSE),
            ('timer-continue', gtk.STOCK_MEDIA_PLAY),
            ('timer-restart', gtk.STOCK_REDO),
            ('timer-back', gtk.STOCK_OK)
        )
        factory = gtk.IconFactory()
        factory.add_default()
        for id, stock in icons:
            icon_set = gtk.icon_factory_lookup_default(stock)
            factory.add(id, icon_set)
        
        # Parse configuration
        defaults = {
            'UI': {
                'advanced_mode': str(False)
            },
            'Presets': {}
        }
        self.config = os.path.join(root, 'timer.conf')
        self.parser = self.initialize_config(defaults, self.config)
        self.presets_model = self.parse_presets(self.parser)
        
        # Create and connect timer object
        self.timer = Timer()
        self.timer.connect('timer-updated', self.update_display)
        self.timer.connect('timer-finished', self.finished)
        
        # Construct window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_size_request(300, -1)
        self.window.set_border_width(10)
        self.window.set_title('Timer')
        self.window.set_icon_list(
            gtk.gdk.pixbuf_new_from_file(os.path.join(os.path.join(root, 'icon'), 'timer-24.png')),
            gtk.gdk.pixbuf_new_from_file(os.path.join(os.path.join(root, 'icon'), 'timer-48.png')))
        self.window.connect('destroy', gtk.main_quit)
        
        vbox = gtk.VBox()
        self.window.add(vbox)
        
        # We use containers to be able to quickly switch the display
        self.countdown_container = gtk.VBox(spacing = 10)
        vbox.pack_start(self.countdown_container)
        self.control_container = gtk.VBox()
        vbox.pack_start(self.control_container)
        
        self.simple_control_container = gtk.VBox()
        vbox.pack_start(self.simple_control_container)
        self.advanced_control_container = gtk.VBox()
        vbox.pack_start(self.advanced_control_container)
        self.button_box = gtk.HBox()
        vbox.pack_start(self.button_box, False)
        
        # Create the name label
        self.name_label = gtk.Label()
        self.countdown_container.pack_start(self.name_label, False)
        
        # Create the pie-meter
        self.pie_meter = PieWidget()
        self.countdown_container.pack_start(self.pie_meter)
        
        # Create the time label. The outer hbox is needed for horizontal
        # centering, the inner hbox to add padding between the label and
        # the frame.
        outer_hbox = gtk.HBox()
        self.countdown_container.pack_start(outer_hbox, False)
        
        frame = gtk.Frame()
        outer_hbox.pack_start(frame, True, False)
        
        inner_hbox = gtk.HBox()
        frame.add(inner_hbox)
        
        self.time_label = gtk.Label()
        inner_hbox.pack_start(self.time_label, padding = 5)
        
        # Create countdown control buttons
        button_box = gtk.HBox()
        self.countdown_container.pack_start(button_box, False)
        
        controls = (
            ('back', 'timer-back', self.stop_timer),
            ('restart', 'timer-restart', self.restart_timer),
            ('stop', 'timer-stop', self.stop_timer),
            ('pause', 'timer-pause', self.toggle_timer),
            ('continue', 'timer-continue', self.toggle_timer)
        )
        
        self.countdown_buttons = {}
        for name, stock, callback in controls:
            button = gtk.Button(stock = stock)
            button_box.pack_end(button, False, False)
            button.connect('clicked', callback)
            self.countdown_buttons[name] = button
        
        # Create timer-controll ui
        table = gtk.Table(8, 2)
        table.set_col_spacings(20)
        table.set_row_spacings(10)
        self.control_container.pack_start(table, False)
        
        bg_check = gtk.CheckButton()
        bg_check.set_active(self.parser.getboolean('Colors', 'background'))
        bg_button = gtk.ColorButton()
        bg_button.set_sensitive(self.parser.getboolean('Colors', 'background'))
        bg_check.connect('toggled', lambda b: b.get_active() \
            and [bg_button.set_sensitive(True)] or bg_button.set_sensitive(False))
        bg_box = gtk.HBox()
        bg_box.pack_start(bg_check, False)
        bg_box.pack_end(bg_button)
        
        img_check = gtk.CheckButton()
        img_check.set_active(self.parser.getboolean('Colors', 'background'))
        img_button = gtk.FileChooserButton(gtk.FileChooserDialog())
        img_button.set_sensitive(self.parser.getboolean('Colors', 'background'))
        img_check.connect('toggled', lambda b: b.get_active() \
            and [img_button.set_sensitive(True)] or img_button.set_sensitive(False))
        img_box = gtk.HBox()
        img_box.pack_start(img_check, False)
        img_box.pack_end(img_button)
        
        snd_check = gtk.CheckButton()
        snd_check.set_active(self.parser.getboolean('Colors', 'background'))
        snd_button = gtk.FileChooserButton(gtk.FileChooserDialog())
        snd_button.set_sensitive(self.parser.getboolean('Colors', 'background'))
        snd_check.connect('toggled', lambda b: b.get_active() \
            and [snd_button.set_sensitive(True)] or snd_button.set_sensitive(False))
        snd_box = gtk.HBox()
        snd_box.pack_start(snd_check, False)
        snd_box.pack_end(snd_button)
        
        controls = (
            ('hours', 'Hours', gtk.SpinButton(gtk.Adjustment(0, 0, 72, 1, 5))),
            ('minutes', 'Minutes', gtk.SpinButton(gtk.Adjustment(0, 0, 59, 1, 5))),
            ('seconds', 'Seconds', gtk.SpinButton(gtk.Adjustment(0, 0, 59, 1, 5))),
            ('name', 'Name', gtk.Entry()),
            ('fg', 'Foreground Color', gtk.ColorButton()),
            ('bg', 'Background Color', bg_box),
            ('img', 'Use Image', img_box),
            ('snd', 'Play Sound', snd_box)
        )
        
        self.timeout_editables = {}
        for i in range(0, len(controls)):
            name, label, widget = controls[i]
            alignment = gtk.Alignment(0.0, 0.5)
            alignment.add(gtk.Label(label))
            table.attach(alignment, 0, 1, i, i + 1, gtk.FILL)
            table.attach(widget, 1, 2, i, i + 1)
            #id = widget.connect('changed', self.unselect_preset)
            self.timeout_editables[name] = {}
            self.timeout_editables[name]['widget'] = widget
            self.timeout_editables[name]['handler'] = id
        
        # Create advanced timer-setup ui
        table = gtk.Table(3, 2)
        table.set_col_spacings(20)
        table.set_row_spacings(10)
        self.advanced_control_container.pack_start(table, False)
        
        controls = (
            ('name', 'Name', gtk.Entry()),
        )
        
        for i in range(0, len(controls)):
            name, label, widget = controls[i]
            alignment = gtk.Alignment(0.0, 0.5)
            alignment.add(gtk.Label(label))
            table.attach(alignment, 0, 1, i, i + 1, gtk.FILL)
            table.attach(widget, 1, 2, i, i + 1)
            id = widget.connect('changed', self.unselect_preset)
            self.timeout_editables[name] = {}
            self.timeout_editables[name]['widget'] = widget
            self.timeout_editables[name]['handler'] = id
        
        # Create presets control
        self.advanced_control_container.pack_start(
            gtk.HSeparator(), False, padding = 5)
        
        alignment = gtk.Alignment(0.0, 0.5)
        alignment.add(gtk.Label('Presets'))
        self.advanced_control_container.pack_start(alignment, False, False)
        
        hbox = gtk.HBox()
        self.advanced_control_container.pack_start(hbox)
        
        # Create presets treeview
        presets_view = gtk.TreeView(self.presets_model)
        presets_view.set_headers_visible(False)
        presets_view.append_column(gtk.TreeViewColumn(None,
            gtk.CellRendererText(), text = 0))
        
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.add(presets_view)
        hbox.pack_start(scroll)
        
        self.preset_selection = presets_view.get_selection()
        self.preset_selection.connect('changed', self.preset_selection_changed)
        
        # Create presets-control buttons
        button_box = gtk.VBox()
        hbox.pack_start(button_box, False)
        
        controls = (
            ('Save', gtk.STOCK_SAVE, self.save_preset),
            ('Delete', gtk.STOCK_DELETE, self.delete_preset)
        )
        
        self.preset_buttons = {}
        for label, stock, callback in controls:
            button = gtk.Button(stock = stock)
            button_box.pack_start(button, False)
            button.connect('clicked', callback)
            self.preset_buttons[label] = button
        
        self.advanced_control_container.pack_start(gtk.HSeparator(), False, padding = 5)
        
        # Create main control buttons
        start_button = gtk.Button(stock = 'timer-start')
        self.button_box.pack_start(start_button, False, False)
        start_button.connect('clicked', self.start_timer)
        
        advanced_mode_check = gtk.CheckButton()
        self.button_box.pack_end(gtk.Label('Advanced Mode'), False, False)
        self.button_box.pack_end(advanced_mode_check, False, False)
        advanced_mode_check.connect('clicked', self.toggle_advanced_mode)
        
        # Create tray icon
        self.tray = TrayIcon('timer-48.png')
        self.tray.fg_color = [self.parser.getfloat(
            'Colors', 'foreground_' + x) for x in ('r', 'g', 'b')]
        self.tray.bg_color = [self.parser.getfloat(
            'Colors', 'background_' + x) for x in ('r', 'g', 'b')]
        self.tray.status_icon.connect('activate', self.tray_activated)
        self.tray.status_icon.connect('popup-menu', self.show_tray_menu)
        
        # Create tray menu
        self.tray_menu = gtk.Menu()
        
        controls = (
            ('start', 'timer-start', self.start_timer),
            ('pause', 'timer-pause', self.toggle_timer),
            ('continue', 'timer-continue', self.toggle_timer),
            ('stop', 'timer-stop', self.stop_timer),
            ('restart', 'timer-restart', self.restart_timer),
            gtk.SeparatorMenuItem(),
            ('preferences', gtk.STOCK_PREFERENCES, self.pref_dialog),
            gtk.SeparatorMenuItem(),
            ('quit', gtk.STOCK_QUIT, gtk.main_quit)
        )
        
        self.tray_menu_items= {}
        for row in controls:
            if type(row) != tuple:
                self.tray_menu.add(row)
            else:
                name, stock, callback = row
                item = gtk.ImageMenuItem(stock)
                item.connect('activate', callback)
                self.tray_menu.add(item)
                self.tray_menu_items[name] = item
        
        self.tray_menu.show_all()
        
        # Finalize UI
        self.window.show_all()
        
        self.toggle_ui()
        
        self.countdown_buttons['back'].hide()
        self.countdown_buttons['continue'].hide()
        self.countdown_buttons['restart'].hide()
        
        self.tray_menu_items['continue'].hide()
        self.tray_menu_items['restart'].hide()
        
        self.preset_buttons['Delete'].set_sensitive(False)
    
    def main(self):
        """
        Hand over control to GTK's main function.
        """
        
        gtk.main()
    
    def initialize_config(self, defaults, path):
        """
        Returns an initialized instance of the configuration file parser
        based on the contents of the specified defaults dictionary and
        the config file under the specified path.
        """
        
        parser = ConfigParser.RawConfigParser()
        parser.optionxform = str # Parse case-sensitive
        
        if os.path.isfile(path):
            parser.read(path)
            
            save_flag = False
            
            for section in defaults:
                if not parser.has_section(section):
                    parser.add_section(section)
                    save_flag = True
                for option in defaults[section]:
                    if not parser.has_option(section, option):
                        parser.set(section, option, defaults[section][option])
                        save_flag = True
        else:
            save_flag = True
            
            for section in defaults:
                parser.add_section(section)
                for option in defaults[section]:
                    parser.set(section, option, defaults[section][option])
        
        if save_flag: self.save_config(parser, path)
        
        return parser
    
    def parse_presets(self, parser):
        """
        Parses presets from an initialized parser into a ListStore model
        and returns it.
        """
        
        model = gtk.ListStore(str, str, int)
        
        if parser.has_section('Presets'):
            for preset in parser.options('Presets'):
                timeout = parser.getint('Presets', preset)
                display = self.preset_to_string(preset, timeout)
                model.append((display, preset, timeout))
        
        return model
    
    def save_config(self, parser, path):
        """
        Saves the current configuration to path.
        """
        
        fp = open(path, 'w')
        parser.write(fp)
        fp.close()
    
    def seconds_to_hms(self, s):
        """
        Returns the hours-minutes-seconds representation of the seconds
        specified in s as 3-tuple.
        """
        
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        
        return h, m, s
    
    def hms_to_seconds(self, h, m, s):
        """
        Converts a timeout given in hours, minutes and seconds to seconds.
        """
        
        return s + 60 * (m + 60 * h)
    
    def preset_to_string(self, name, timeout):
        """
        Generates a string for display from a preset name and timeout.
        """
        
        h, m, s = self.seconds_to_hms(timeout)
        
        string = '%s (' % name
        if h: string += '%ih' % h
        if m:
            if h: string += ' '
            string += '%im' % m
        if s:
            if m or h: string += ' '
            string += '%is' % s
        string += ')'
        
        return string
    
    def ok_cancel_dialog(self, title, border = 10, resizable = False):
        """
        Returns a simple Ok / Cancel dialog.
        """
        
        dialog = gtk.Dialog(title, self.window, gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        dialog.set_border_width(border)
        dialog.set_resizable(resizable)
        
        return dialog
        
    
    def confirmation_dialog(self, title, msg):
        """
        Returns a confirmation dialog widget.
        """
        
        dialog = self.ok_cancel_dialog(title)
        
        hbox = gtk.HBox(spacing = 10)
        dialog.vbox.pack_start(hbox, padding = 10)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
        hbox.pack_start(image)
        
        label = gtk.Label(msg)
        label.set_use_markup(True)
        hbox.pack_start(label)
        
        dialog.vbox.show_all()
        
        dialog.set_icon_name(gtk.STOCK_DIALOG_QUESTION)
        
        return dialog
    
    def save_preset(self, button):
        """
        Saves a preset.
        """
        
        # Get timeout, name and display name
        h = int(self.timeout_editables['hours']['widget'].get_value())
        m = int(self.timeout_editables['minutes']['widget'].get_value())
        s = int(self.timeout_editables['seconds']['widget'].get_value())
        timeout = self.hms_to_seconds(h, m, s)
        
        name = self.timeout_editables['name']['widget'].get_text()
        
        display = self.preset_to_string(name, timeout)
        
        if timeout == 0 or len(name) == 0: return
        
        # Check if preset already exists
        if self.parser.has_option('Presets', name):
            # Alert the user
            dialog = self.confirmation_dialog('Overwrite preset?',
                'Overwrite existing preset <b><i>%s</i></b>?' % name)
            
            if dialog.run() == gtk.RESPONSE_ACCEPT:
                # Find the corresponding iter
                iter = self.presets_model.get_iter_first()
                while iter: # This actually sucks, but I can't think of a better way atm.
                    if self.presets_model.get_value(iter, 1) == name: break
                    iter = self.presets_model.iter_next(iter)
                
                # Update row
                self.presets_model.set(iter, 0, display, 1, name, 2, timeout)
            else: iter = None
            
            dialog.destroy()
        else:
            # Insert new row
            iter = self.presets_model.append((display, name, timeout))
        
        # Update and save config
        if iter:
            self.parser.set('Presets', name, timeout)
            self.save_config(self.parser, self.config)
            
            self.preset_selection.select_iter(iter)
    
    def delete_preset(self, button):
        """
        Deletes a preset.
        """
        
        # Get selected preset
        (model, iter) = self.preset_selection.get_selected()
        name = model.get_value(iter, 1)
        
        # Alert the user
        dialog = self.confirmation_dialog('Delete preset?',
                'Delete preset <b><i>%s</i>?</b>' % name)
        
        if dialog.run() == gtk.RESPONSE_ACCEPT:
            # Remove preset from liststore and config
            model.remove(iter)
            self.parser.remove_option('Presets', name)
            self.save_config(self.parser, self.config)
        
        dialog.destroy()
    
    def preset_selection_changed(self, selection):
        """
        Callback function to modify the UI when the preset selection has
        changes.
        """
        
        (model, iter) = selection.get_selected()
        
        if not iter:
            self.preset_buttons['Delete'].set_sensitive(False)
        else:
            self.preset_buttons['Delete'].set_sensitive(True)
            
            timeout = model.get_value(iter, 2)
            name = model.get_value(iter, 1)
            
            h, m, s = self.seconds_to_hms(timeout)
            
            # We need to block the 'changed' signal-handler on all timeout
            # editables here to not lose the selection.
            for key in self.timeout_editables:
                self.timeout_editables[key]['widget'].handler_block(
                    self.timeout_editables[key]['handler'])
            
            self.timeout_editables['hours']['widget'].set_value(h)
            self.timeout_editables['minutes']['widget'].set_value(m)
            self.timeout_editables['seconds']['widget'].set_value(s)
            self.timeout_editables['name']['widget'].set_text(name)
            
            # Unblock the 'changed' signal-handlers
            for key in self.timeout_editables:
                self.timeout_editables[key]['widget'].handler_unblock(
                    self.timeout_editables[key]['handler'])
    
    def unselect_preset(self, button):
        """
        Unselects any presets.
        """
        
        self.preset_selection.unselect_all()
    
    def color_component_cairo_to_gdk(self, c):
        """
        Converts a Cairo color component to a GDK color component.
        """
        
        return int(c * 65535)
    
    def color_gdk_to_cairo(self, r, g, b):
        """
        Converts a GDK color tuple to a Cairo color tuple.
        """
        
        return [x / 65535.0 for x in (r, g, b)]
    
    def pref_dialog(self, button):
        """
        Constructs and runs the preferences dialog.
        """
        
        # Construct dialog
        dialog = self.ok_cancel_dialog('Preferences', resizable = True)
        dialog.set_size_request(280, -1)
        dialog.set_icon_name(gtk.STOCK_PREFERENCES)
        
        # Create controls table
        table = gtk.Table(4, 2)
        table.set_col_spacings(20)
        table.set_row_spacings(10)
        dialog.vbox.pack_start(table)
        
        interval_spin = gtk.SpinButton(gtk.Adjustment(
            self.parser.getint('Display', 'update_interval'), 50, 1000,
            10, 100))
        
        r, g, b = [self.color_component_cairo_to_gdk(self.parser.getfloat(
            'Colors', 'foreground_' + c)) for c in ('r', 'g', 'b')]
        fg_button = gtk.ColorButton(gtk.gdk.Color(r, g, b))
        
        bg_check = gtk.CheckButton()
        bg_check.set_active(self.parser.getboolean('Colors', 'background'))
        
        r, g, b = [self.color_component_cairo_to_gdk(self.parser.getfloat(
            'Colors', 'background_' + c)) for c in ('r', 'g', 'b')]
        bg_button = gtk.ColorButton(gtk.gdk.Color(r, g, b))
        bg_button.set_sensitive(self.parser.getboolean('Colors', 'background'))
        
        bg_check.connect('toggled', lambda b: b.get_active() \
            and [bg_button.set_sensitive(True)] or bg_button.set_sensitive(False))
        
        bg_box = gtk.HBox()
        bg_box.pack_start(bg_check)
        bg_box.pack_start(bg_button)
        
        only_tray_check = gtk.CheckButton()
        only_tray_check.set_active(self.parser.getboolean('Display', 'only_in_tray'))
        only_tray_check.set_sensitive(self.tray.status_icon.is_embedded())
        
        controls = (
            ('Update Interval', interval_spin),
            ('Foreground Color', fg_button),
            ('Background Color', bg_box),
            ('Run in tray only', only_tray_check)
        )
        
        for i in range(0, len(controls)):
            name, widget = controls[i]
            if type(widget) != gtk.SpinButton:
                widget_align = gtk.Alignment(1.0, 0.5)
                widget_align.add(widget)
                widget = widget_align
            alignment = gtk.Alignment(0.0, 0.5)
            alignment.add(gtk.Label(name))
            table.attach(alignment, 0, 1, i, i + 1, gtk.FILL)
            table.attach(widget, 1, 2, i, i + 1)
        
        dialog.vbox.show_all()
        
        # Run dialog
        if dialog.run() == gtk.RESPONSE_ACCEPT:
            # Get and save all settings
            self.parser.set('Display', 'update_interval',
                int(interval_spin.get_value()))
            
            c = fg_button.get_color()
            r, g, b = self.color_gdk_to_cairo(c.red, c.green, c.blue)
            
            self.parser.set('Colors', 'foreground_r', r)
            self.parser.set('Colors', 'foreground_g', g)
            self.parser.set('Colors', 'foreground_b', b)
            
            if bg_check.get_active():
                c = bg_button.get_color()
                r, g, b = self.color_gdk_to_cairo(c.red, c.green, c.blue)
                
                self.parser.set('Colors', 'background_r', r)
                self.parser.set('Colors', 'background_g', g)
                self.parser.set('Colors', 'background_b', b)
            
            self.parser.set('Colors', 'background', str(bg_check.get_active()))
            
            if only_tray_check.get_property('sensitive'):
                self.parser.set('Display', 'only_in_tray',
                    str(only_tray_check.get_active()))
            
            self.save_config(self.parser, self.config)
        
        dialog.destroy()
    
    def toggle_ui(self):
        """
        Toggles the user interface between timer and control mode.
        """
        
        if not self.countdown_container.get_property('visible'):
            # Switch to timer mode
            self.countdown_container.show()
            self.simple_control_container.hide()
            self.advanced_control_container.hide()
            
            self.tray_menu_items['start'].hide()
            self.tray_menu_items['pause'].show()
            self.tray_menu_items['stop'].show()
            self.tray_menu_items['preferences'].set_sensitive(False)
            
            if self.parser.getboolean('Display', 'only_in_tray') and \
               self.tray.status_icon.is_embedded():
                self.window.hide()
        else: # Switch to control mode
            self.countdown_container.hide()
            self.simple_control_container.show()
            self.advanced_control_container.show()
            
            self.tray_menu_items['start'].show()
            self.tray_menu_items['pause'].hide()
            self.tray_menu_items['stop'].hide()
            self.tray_menu_items['preferences'].set_sensitive(True)
            
            if self.parser.getboolean('Display', 'only_in_tray'):
                self.window.show()
    
    def toggle_advanced_mode(self, button):
        """
        Callback to toggle between advanced and simple controll mode.
        """
        
        if button.get_active(): self.advanced_control_container.show()
        else: self.advanced_control_container.hide()
    
    def start_timer(self, button):
        """
        Callback to start the timer.
        """
        
        # Get timeout
        (model, iter) = self.preset_selection.get_selected()
        if not iter:
            h = self.timeout_editables['hours']['widget'].get_value()
            m = self.timeout_editables['minutes']['widget'].get_value()
            s = self.timeout_editables['seconds']['widget'].get_value()
            timeout = self.hms_to_seconds(h, m, s)
        else:
            timeout = model.get_value(iter, 2)
        if timeout == 0.0: return
        
        # Set timeout
        self.timer.timeout = self.timer.time = timeout
        self.pie_meter.fraction = self.tray.fraction = 0.0
        
        # Get and set name
        name = self.timeout_editables['name']['widget'].get_text()
        if len(name) > 0:
            self.name_label.set_text('<big><b>%s</b></big>' % name)
            self.name_label.set_use_markup(True)
            self.name_label.show()
        else: self.name_label.hide()
        
        # Set update interval
        self.timer.interval = self.parser.getint('Display', 'update_interval') / 1000.0
        
        # Set colors
        r = self.parser.getfloat('Colors', 'foreground_r')
        g = self.parser.getfloat('Colors', 'foreground_g')
        b = self.parser.getfloat('Colors', 'foreground_b')
        self.pie_meter.drawer.fg_color = self.tray.drawer.fg_color = (r, g, b)
        
        if self.parser.getboolean('Colors', 'background'):
            r = self.parser.getfloat('Colors', 'background_r')
            g = self.parser.getfloat('Colors', 'background_g')
            b = self.parser.getfloat('Colors', 'background_b')
            self.pie_meter.drawer.bg_color = self.tray.drawer.bg_color = (r, g, b)
        else: self.pie_meter.drawer.bg_color = self.tray.drawer.bg_color = None
        
        self.toggle_ui()
        self.tray.unset_from_file()
        
        self.timer.start()
    
    def toggle_timer(self, button):
        """
        Pauses / Continues the timer.
        """
        
        if self.timer.running: # Pause timer
            self.timer.stop()
            
            self.countdown_buttons['pause'].hide()
            self.countdown_buttons['continue'].show()
            self.countdown_buttons['restart'].show()
            
            self.tray_menu_items['pause'].hide()
            self.tray_menu_items['continue'].show()
            self.tray_menu_items['restart'].show()
        else: # Resume timer
            self.timer.start()
            
            self.countdown_buttons['pause'].show()
            self.countdown_buttons['continue'].hide()
            self.countdown_buttons['restart'].hide()
            
            self.tray_menu_items['pause'].show()
            self.tray_menu_items['continue'].hide()
            self.tray_menu_items['restart'].hide()
    
    def stop_timer(self, button):
        """
        Callback to stop the timer.
        """
        
        if self.timer.running:
            self.timer.stop()
        else:
            self.countdown_buttons['pause'].show()
            self.countdown_buttons['continue'].hide()
            self.countdown_buttons['stop'].show()
            self.countdown_buttons['restart'].hide()
            self.countdown_buttons['back'].hide()
            
            self.tray_menu_items['continue'].hide()
            self.tray_menu_items['restart'].hide()
        
        self.tray.set_from_file()
        self.tray.unalert()
        
        self.toggle_ui()
    
    def update_display(self, timer, data):
        """
        Callback to update the timer's display.
        """
        
        # Update pie-meter and tray icon
        self.pie_meter.fraction = self.tray.fraction = \
            1.0 - timer.time / timer.timeout
        
        # Update time label
        h, m, s = self.seconds_to_hms(math.ceil(timer.time))
        self.time_label.set_text('%02.0f : %02.0f : %02.0f' % (h, m, s))
    
    def finished(self, widget, data):
        """
        Actions to take when the timer has finished.
        """
        
        self.countdown_buttons['pause'].hide()
        self.countdown_buttons['stop'].hide()
        self.countdown_buttons['restart'].show()
        self.countdown_buttons['back'].show()
        
        self.tray_menu_items['pause'].hide()
        self.tray_menu_items['stop'].hide()
        self.tray_menu_items['restart'].show()
        
        self.tray.alert()
    
    def restart_timer(self, button):
        """
        Restarts the timer.
        """
        
        self.timer.time = self.timer.timeout
        self.pie_meter.value = self.tray.value = 0.0
        self.timer.start()
        
        self.countdown_buttons['pause'].show()
        self.countdown_buttons['continue'].hide()
        self.countdown_buttons['stop'].show()
        self.countdown_buttons['restart'].hide()
        self.countdown_buttons['back'].hide()
        
        self.tray_menu_items['pause'].show()
        self.tray_menu_items['continue'].hide()
        self.tray_menu_items['stop'].show()
        self.tray_menu_items['restart'].hide()
        
        self.tray.unalert()
    
    def tray_activated(self, status_icon):
        """
        Callback to show / hide the window on tray icon activation.
        """
        
        if self.window.get_property('visible'): self.window.hide()
        else: self.window.show()
    
    def show_tray_menu(self, status_icon, button, activate_time):
        """
        Presents the tray menu.
        """
        
        self.tray_menu.popup(None, None, gtk.status_icon_position_menu,
            button, activate_time, status_icon)

def main():
    root = os.path.dirname(os.path.realpath(__file__))
    timer = TimerApp(root)
    timer.main()

if __name__ == '__main__':
    main()
