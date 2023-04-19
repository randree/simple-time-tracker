import datetime
import sqlite3
from gi.repository import Gtk
import gi

from utils.config import Config
gi.require_version("Gtk", "3.0")


class ListElapsedWindow(Gtk.Window):
    def __init__(self, category_id, db_conn, config_file):
        Gtk.Window.__init__(self, title="Records")

        self.connect("delete-event", self.on_delete_event)

        self.category_id = category_id
        self.set_border_width(10)

        self.config = Config(config_file)
        self.config.load_window_config(self, "ListWindow", 100, 100, 500, 500)

        self.conn = db_conn

        self.liststore = Gtk.ListStore(str, str)

        self.treeview = Gtk.TreeView(model=self.liststore)

        timestamp_column = Gtk.TreeViewColumn("Timestamp")
        duration_column = Gtk.TreeViewColumn("Duration")
        self.treeview.append_column(timestamp_column)
        self.treeview.append_column(duration_column)

        timestamp_cell = Gtk.CellRendererText()
        duration_cell = Gtk.CellRendererText()
        timestamp_column.pack_start(timestamp_cell, True)
        duration_column.pack_start(duration_cell, True)

        timestamp_column.add_attribute(timestamp_cell, "text", 0)
        duration_column.add_attribute(duration_cell, "text", 1)

        self.load_records()

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.treeview)
        scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.add(scrolled_window)

    def load_records(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT timestamp, elapsed_time FROM records WHERE category_id=?", (self.category_id,))
        records = cursor.fetchall()

        for record in records:
            timestamp = datetime.datetime.strptime(record[0], "%Y-%m-%d %H:%M:%S")
            elapsed_time_parts = record[1].split(':')
            hours, minutes = int(elapsed_time_parts[0]), int(elapsed_time_parts[1])
            seconds = float(elapsed_time_parts[2])
            elapsed_time = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
            new_timestamp = timestamp - elapsed_time
            new_timestamp_str = new_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
            self.liststore.append([new_timestamp_str, record[1]])

    def on_delete_event(self, widget, event):
        self.config.save_window_config(self, "ListWindow")


def main():
    category_id = 1  # Change this to the desired category id
    win = ListElapsedWindow(category_id)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
