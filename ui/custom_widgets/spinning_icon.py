import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import cairo

class SpinningIcon(Gtk.DrawingArea):
    def __init__(self, icon_name, icon_size):
        super().__init__()

        self.angle = 0
        self.icon_name = icon_name
        self.icon_size = icon_size
        self.timeout_id = None
        self.connect("draw", self.on_draw)

        icon_theme = Gtk.IconTheme.get_default()
        pixbuf = icon_theme.load_icon(self.icon_name, self.icon_size, Gtk.IconLookupFlags.FORCE_SIZE)
        self.set_size_request(pixbuf.get_width(), pixbuf.get_height())

    def on_draw(self, widget, cr):
        width = self.get_allocated_width()
        height = self.get_allocated_height()

        icon_theme = Gtk.IconTheme.get_default()
        pixbuf = icon_theme.load_icon(self.icon_name, self.icon_size, Gtk.IconLookupFlags.FORCE_SIZE)

        surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, 1, None)

        # Move the drawing context to the center of the widget
        cr.translate(width // 2, height // 2)

        # Rotate the drawing context around the center of the image
        cr.rotate(self.angle)
        cr.translate(-pixbuf.get_width() // 2, -pixbuf.get_height() // 2)

        # Draw the icon at the rotated angle
        cr.set_source_surface(surface, 0, 0)
        cr.paint()

    def rotate(self):
        self.angle += 0.01
        if self.angle >= 2 * 3.14159265:
            self.angle -= 2 * 3.14159265
        self.queue_draw()

        # Return True to keep the timer running
        return True

    def start(self):
        if self.timeout_id is None:
            # Set a timer to call the rotate method every 50 milliseconds
            self.timeout_id = GLib.timeout_add(5, self.rotate)

    def stop(self):
        if self.timeout_id is not None:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None