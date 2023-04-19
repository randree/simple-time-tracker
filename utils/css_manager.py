import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

class CssManager:
    def __init__(self, css_path):
        self.css_path = css_path

    def load_css(self):
        css_provider = Gtk.CssProvider()

        try:
            css_provider.load_from_path(self.css_path)
        except Exception as e:
            print(f"Error loading CSS: {e}")
            return

        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
