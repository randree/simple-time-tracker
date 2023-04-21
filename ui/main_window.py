# Time Tracker - A simple time tracking application using Python and GTK

from ui.custom_widgets import StartButton
from ui.custom_widgets.spinning_icon import SpinningIcon
from utils.css_manager import CssManager
from utils.config import Config
from database import DatabaseManager
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk
from ui.list_elapsed import ListElapsedWindow
import gi
import os
import time
import sqlite3
import datetime
import configparser

from utils.format import Format

gi.require_version("Gtk", "3.0")


CONFIG_FILE = "app_config.ini"
DATABASE = "timer_records.db"
CSS_MAIN = "assets/css/main.css"


class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Time Tracker")
        self.set_default_icon_name("clock-symbolic")
        self.set_border_width(10)

        self.connect("delete-event", self.on_delete_event)

        self.db_manager = DatabaseManager(DATABASE)
        self.conn = self.db_manager.create_connection()

        self.config = Config(CONFIG_FILE)
        self.config.load_window_config(self, "Window", 200, 200, 200, 600)

        # clock_icon = Gtk.Image.new_from_icon_name(
        #     "clock-symbolic", Gtk.IconSize.DIALOG)
        self.clock_icon = SpinningIcon("clock-symbolic", 50)

        self.start_time = 0
        self.category_total_time = 0
        self.running = False

        # New variable to hold the currently selected category ID
        self.current_category_id = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        vbox.add(self.clock_icon)

        self.timer_label = Gtk.Label()
        self.timer_label.set_markup("<big>00:00:00</big>")
        vbox.add(self.timer_label)

        self.total_time_label = Gtk.Label()
        vbox.add(self.total_time_label)

        self.category_label = Gtk.Label(label="")
        vbox.add(self.category_label)

        self.export_button = Gtk.Button(label="Export")
        self.export_button.connect("clicked", self.on_export_button_clicked)
        vbox.add(self.export_button)

        self.show_times = Gtk.Button(label="Show Times")
        self.show_times.connect("clicked", self.on_show_records_clicked)
        vbox.add(self.show_times)

        # Create a HBox for the category-related buttons
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vbox.add(hbox)

        # Add Category
        self.add_category_button = Gtk.Button.new_from_icon_name(
            "list-add-symbolic", Gtk.IconSize.BUTTON)
        self.add_category_button.connect(
            "clicked", self.on_add_category_button_clicked)
        hbox.pack_start(self.add_category_button, True, True, 0)

        # Edit Category button
        self.edit_category_button = Gtk.Button.new_from_icon_name(
            "edit-symbolic", Gtk.IconSize.BUTTON)
        self.edit_category_button.connect(
            "clicked", self.on_edit_category_button_clicked)

        hbox.pack_start(self.edit_category_button, True, True, 0)

        # Delete Category button
        self.delete_category_button = Gtk.Button.new_from_icon_name(
            "edit-delete-symbolic", Gtk.IconSize.BUTTON)
        self.delete_category_button.connect(
            "clicked", self.on_delete_category_button_clicked)
        hbox.pack_start(self.delete_category_button, True, True, 0)

        self.categories_list_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL)
        self.list_store = Gtk.ListStore(int, str, str)
        vbox.pack_start(self.categories_list_box, True, True, 0)

        self.start_button = StartButton(self.on_start_button_clicked)
        self.start_button.set_button_color("stop")

        # Set up the CSS style
        style_provider = Gtk.CssProvider()
        css_manager = CssManager(CSS_MAIN)
        css_manager.load_css()

        self.load_current_category_id()
        self.load_categories_list_box()
        self.check_current_category()

        vbox.add(self.start_button)

        self.init_accumulated_time()

    def check_current_category(self):
        if self.current_category_id is None:
            self.edit_category_button.set_sensitive(False)
            self.delete_category_button.set_sensitive(False)
            self.export_button.set_sensitive(False)
            self.show_times.set_sensitive(False)
            self.start_button.set_sensitive(False)
        else:
            self.edit_category_button.set_sensitive(True)
            self.delete_category_button.set_sensitive(True)
            self.export_button.set_sensitive(True)
            self.show_times.set_sensitive(True)
            self.start_button.set_sensitive(True)

    def on_show_records_clicked(self, widget):
        category_id = self.current_category_id
        record_win = ListElapsedWindow(category_id, self.conn, CONFIG_FILE)
        record_win.show_all()

    def set_total_time_label(self, total_time):
        self.total_time_label.set_markup(
            f"Total time: {Format().format_time(total_time)}")

    def init_accumulated_time(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(elapsed_time) FROM records")
        self.total_time = cursor.fetchone()[0]
        self.set_total_time_label(self.total_time)

    def on_cursor_changed(self, tree_view):
        selection = tree_view.get_selection()
        model, tree_iter = selection.get_selected()

        if tree_iter is not None:
            self.current_category_id = model.get_value(tree_iter, 0)
            label = model.get_value(tree_iter, 1)

            self.category_label.set_label(label)

            # Save active category ID
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE settings SET active_category_id = ?", (self.current_category_id,))
            self.conn.commit()
        else:
            self.current_category_id = None
            self.category_label.set_label("")

        self.check_current_category()

        # Redraw the TreeView to update the background color
        tree_view.queue_draw()

    def load_current_category_id(self):
        # Load the last active category from the database
        cursor = self.conn.cursor()
        cursor.execute("SELECT active_category_id FROM settings WHERE id = 1")
        self.current_category_id = cursor.fetchone()[0]

    def insert_category(self, category_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO categories (name) VALUES (?)", (category_name,))
            self.conn.commit()
            # Get the ID of the new category
            new_category_id = cursor.lastrowid
            cursor.execute(
                "UPDATE settings SET active_category_id = ?", (new_category_id,))
            self.conn.commit()
            self.list_store.append(
                [new_category_id, category_name, Format().format_time(0)])

            # Store the current category ID
            self.current_category_id = new_category_id
        except sqlite3.IntegrityError:
            dialog = Gtk.MessageDialog(
                parent=None,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=f"Category '{category_name}' already exists",
            )
            dialog.run()
            dialog.destroy()

    def update_category_time_store(self, category_total_time):
        for row in self.list_store:
            if row[0] == self.current_category_id:
                self.list_store.set_value(row.iter, 2, Format().format_time(
                    category_total_time))
                break

    def update_category_time(self, category_id, elapsed_time):
        # Get the current timestamp
        current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert the new record with the current timestamp
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO records (category_id, elapsed_time, timestamp) VALUES (?, ?, ?)",
                       (self.current_category_id, elapsed_time, current_timestamp))
        self.conn.commit()

        self.update_category_time_store(
            self.get_category_total_time(category_id))

    def update_category_name(self, category_id, category_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE categories SET name = ? WHERE id = ?",
                           (category_name, category_id))
            self.conn.commit()

            for row in self.list_store:
                if row[0] == self.current_category_id:
                    self.list_store.set_value(row.iter, 1, category_name)
                    break

        except sqlite3.IntegrityError:
            dialog = Gtk.MessageDialog(
                parent=None,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=f"Category '{category_name}' already exists",
            )
            dialog.run()
            dialog.destroy()

    def delete_category(self, category_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM records WHERE category_id = ?", (category_id,))
        cursor.execute(
            "DELETE FROM categories WHERE id = ?", (category_id,))
        self.conn.commit()
        cursor.execute(
            "UPDATE settings SET active_category_id = ?", (None,))
        self.conn.commit()

        for row in self.list_store:
            if row[0] == category_id:
                self.list_store.remove(row.iter)

    def load_categories_list_box(self):
        # current_active_id = self.category_combo.get_active_id()

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM categories")

        # Create a ListStore and set it as the model for the TreeView
        tree_view = Gtk.TreeView(model=self.list_store)

        # Create TreeViewColumns and CellRenderers for the TreeView
        category_column = Gtk.TreeViewColumn("Category")
        total_time_column = Gtk.TreeViewColumn("Total Time")

        category_renderer = Gtk.CellRendererText()
        total_time_renderer = Gtk.CellRendererText()

        category_column.pack_start(category_renderer, True)
        total_time_column.pack_start(total_time_renderer, True)

        category_column.add_attribute(category_renderer, "text", 1)
        total_time_column.add_attribute(total_time_renderer, "text", 2)

        # Add the columns to the TreeView
        tree_view.append_column(category_column)
        tree_view.append_column(total_time_column)

        # Connect the 'cursor-changed' signal to update the active category
        tree_view.connect("cursor-changed", self.on_cursor_changed)

        # Remove the previous TreeView (if any) and add the new one
        for child in self.categories_list_box.get_children():
            self.categories_list_box.remove(child)

        self.categories_list_box.pack_start(tree_view, True, True, 0)

        for category_id, name in cursor.fetchall():
            total_time = self.get_category_total_time(category_id)
            total_time_str = Format().format_time(total_time)

            # Add a row to the ListStore with the data
            self.list_store.append([category_id, name, total_time_str])

        tree_iter = self.list_store.get_iter_first()

        while tree_iter is not None:
            # Assuming the ID field is at column index 0
            row_id = self.list_store.get_value(tree_iter, 0)
            if row_id == self.current_category_id:
                selection = tree_view.get_selection()
                selection.select_iter(tree_iter)
                self.on_cursor_changed(tree_view)
                break
            tree_iter = self.list_store.iter_next(tree_iter)

        self.categories_list_box.show_all()

    def on_export_button_clicked(self, widget):
        # Create a new file chooser dialog
        dialog = Gtk.FileChooserDialog(
            "Export Categories",
            self,
            Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        # Set the default filename
        dialog.set_current_name("categories.txt")

        # Add a filter to only show txt files
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        # Show the dialog and get the response
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            # Open the selected file for writing
            filename = dialog.get_filename()
            with open(filename, 'w') as f:
                # Write the header and current date/time to the file
                f.write("Exported Categories\n")
                f.write(
                    f"Date/Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Write the categories and their times to the file
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name FROM categories")
                for category_id, name in cursor.fetchall():
                    total_time = self.get_category_total_time(category_id)
                    f.write(f"{name}:\t{Format().format_time(total_time)}\n")

            print(f"Categories exported to {filename}")

        dialog.destroy()

    def on_add_category_button_clicked(self, widget):
        dialog = Gtk.Dialog(title="Add Category", parent=self, flags=0)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        label = Gtk.Label(label="New Category Name:")
        content_area.add(label)

        entry = Gtk.Entry()
        content_area.add(entry)

        dialog.show_all()
        response = dialog.run()

        new_category_id = 0
        category_name = ""

        if response == Gtk.ResponseType.OK:
            category_name = entry.get_text().strip()
            if category_name:
                self.insert_category(category_name)

        dialog.destroy()

    def on_edit_category_button_clicked(self, widget):
        if self.current_category_id is not None:
            for row in self.list_store:
                if row[0] == self.current_category_id:

                    old_total_time = self.get_category_total_time(
                        self.current_category_id)

                    dialog = Gtk.Dialog(
                        title="Edit Category", parent=self, flags=0)

                    dialog.add_buttons(
                        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_OK, Gtk.ResponseType.OK)

                    content_area = dialog.get_content_area()
                    content_area.set_spacing(10)
                    label = Gtk.Label(label="New Category Name:")
                    content_area.add(label)

                    entry = Gtk.Entry()
                    entry.set_text(row[1])
                    content_area.add(entry)

                    label_total_time = Gtk.Label(
                        label="New Total Time (HH:MM:SS.ss):")
                    content_area.add(label_total_time)

                    entry_total_time = Gtk.Entry()
                    entry_total_time.set_text(
                        Format().format_time(old_total_time))
                    content_area.add(entry_total_time)

                    dialog.show_all()
                    response = dialog.run()

                    if response == Gtk.ResponseType.OK:
                        new_name = entry.get_text().strip()
                        new_time_str = entry_total_time.get_text().strip()

                        if new_name:
                            self.update_category_name(
                                self.current_category_id, new_name)

                        if new_time_str:
                            new_total_time = round(sum(x * (int(t) if i != 2 else float(t))
                                                       for i, (x, t) in enumerate(zip([3600, 60, 1], new_time_str.split(":")))), 2)
                            time_difference = round(
                                new_total_time - round(old_total_time, 2), 2)

                            self.update_category_time(
                                self.current_category_id, time_difference)

                            self.update_total_time()

                    dialog.destroy()

    def on_delete_category_button_clicked(self, widget):
        if self.current_category_id is not None:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text="Delete Category",
            )
            dialog.format_secondary_text(
                "Are you sure you want to delete the selected category? All records associated with this category will be removed."
            )
            response = dialog.run()
            if response == Gtk.ResponseType.OK:

                self.delete_category(self.current_category_id)
                self.update_total_time()

            dialog.destroy()

    def get_total_time(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(elapsed_time) FROM records")
        self.total_time = cursor.fetchone()[0]

    def update_total_time(self):
        self.get_total_time()
        self.set_total_time_label(self.total_time)

    def get_category_total_time(self, category_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT elapsed_time FROM records WHERE category_id = ?", (category_id,))
        times = cursor.fetchall()

        total_time = 0
        for elapsed_time, in times:
            total_time += elapsed_time
        return round(total_time, 2)

    def update_label(self):
        if self.running:
            elapsed_time = time.perf_counter() - self.start_time
            self.timer_label.set_markup(
                f"<big>{Format().format_time(elapsed_time)}</big>")
            self.update_category_time_store(self.category_total_time + elapsed_time)
            # Making sure that timer is on
            self.set_total_time_label(self.total_time + elapsed_time)
        return self.running

    def on_start_button_clicked(self, widget):
        if not self.running:
            self.get_total_time()
            self.start_time = time.perf_counter()
            self.category_total_time = self.get_category_total_time(self.current_category_id)
            self.running = True
            GLib.timeout_add(1000, self.update_label)
            self.clock_icon.start()
        else:
            self.running = False
            elapsed_time = time.perf_counter() - self.start_time
            self.timer_label.set_markup(
                f"<big>{Format().format_time(elapsed_time)}</big>")

            self.update_category_time(self.current_category_id, elapsed_time)
            self.update_total_time()
            self.clock_icon.stop()

    def on_destroy(self):
        self.db_manager.close_connection(self.conn)

    def on_delete_event(self, widget, event):
        self.config.save_window_config(self, "Window")
