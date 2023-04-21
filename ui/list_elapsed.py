from utils.config import Config
import datetime
import sqlite3
from gi.repository import Gtk
import gi
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

        self.list_store = Gtk.ListStore(str, str)

        self.treeview = Gtk.TreeView(model=self.list_store)

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
        cursor.execute(
            "SELECT timestamp, elapsed_time FROM records WHERE category_id=?", (self.category_id,))
        records = cursor.fetchall()

        for record in records:
            timestamp = datetime.datetime.strptime(
                record[0], "%Y-%m-%d %H:%M:%S")
            elapsed_time = datetime.timedelta(seconds=record[1])
            new_timestamp = timestamp - elapsed_time
            new_timestamp_str = new_timestamp.strftime("%Y-%m-%d %H:%M:%S")

            formatted_elapsed_time = str(datetime.timedelta(seconds=round(record[1])))
            self.list_store.append([new_timestamp_str, formatted_elapsed_time])


    def on_delete_event(self, widget, event):
        self.config.save_window_config(self, "ListWindow")
