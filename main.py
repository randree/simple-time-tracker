import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ui.main_window import MainWindow

def main():
    app = Gtk.Application()
    app.connect("activate", on_activate)
    app.run(None)

def on_activate(application):
    window = MainWindow()
    window.set_application(application)
    window.show_all()

if __name__ == "__main__":
    main()