import gi
import time
import sqlite3
import datetime

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib


class TimerApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Timer App")
        self.set_default_icon_name("clock-symbolic")
        self.set_border_width(10)
        
        clock_icon = Gtk.Image.new_from_icon_name("clock-symbolic", Gtk.IconSize.DIALOG)

        self.start_time = None
        self.running = False

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        vbox.pack_start(clock_icon, True, True, 0)

        self.timer_label = Gtk.Label()
        self.timer_label.set_markup("<big>00:00:00.0</big>")
        vbox.pack_start(self.timer_label, True, True, 0)

        self.total_time_label = Gtk.Label()
        vbox.pack_start(self.total_time_label, True, True, 0)
        
        self.category_label = Gtk.Label("Category")
        vbox.pack_start(self.category_label, True, True, 0)
        
        self.category_combo = Gtk.ComboBoxText()
        vbox.pack_start(self.category_combo, True, True, 0)       

        
        self.export_button = Gtk.Button(label="Export")
        self.export_button.connect("clicked", self.on_export_button_clicked)
        vbox.pack_start(self.export_button, True, True, 0)

        # Create a HBox for the category-related buttons
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vbox.pack_start(hbox, True, True, 0)

        # Add Category button
        add_category_button = Gtk.Button.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON)
        add_category_button.connect("clicked", self.on_add_category_button_clicked)
        hbox.pack_start(add_category_button, True, True, 0)

        # Edit Category button
        edit_category_button = Gtk.Button.new_from_icon_name("edit-symbolic", Gtk.IconSize.BUTTON)
        edit_category_button.connect("clicked", self.on_edit_category_button_clicked)
        hbox.pack_start(edit_category_button, True, True, 0)

        # Delete Category button
        delete_category_button = Gtk.Button.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON)
        delete_category_button.connect("clicked", self.on_delete_category_button_clicked)
        hbox.pack_start(delete_category_button, True, True, 0)

        self.categories_list_box = Gtk.ListBox()
        vbox.pack_start(self.categories_list_box, True, True, 0)

        self.button = Gtk.Button(label="Start")
        self.button.connect("clicked", self.on_button_clicked)
        vbox.pack_start(self.button, True, True, 0)

        self.init_db()

    def init_db(self):
        self.conn = sqlite3.connect("timer_records.db")
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS records
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          category_id INTEGER REFERENCES categories(id),
                          elapsed_time TEXT)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS total_time
                          (id INTEGER PRIMARY KEY, accumulated_time REAL)''')
        cursor.execute("INSERT OR IGNORE INTO total_time (id, accumulated_time) VALUES (1, 0)")
        self.conn.commit()

        cursor.execute("SELECT accumulated_time FROM total_time WHERE id = 1")
        self.total_time = cursor.fetchone()[0]
        self.total_time_label.set_markup(f"<big>Total time: {self.format_time(self.total_time)}</big>")

        self.load_categories()

    def format_time(self, elapsed):
        mins, sec = divmod(int(elapsed), 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02d}:{mins:02d}:{sec:02d}.{int((elapsed % 1) * 10)}"

    def load_categories(self, new_category_id=None):
        current_active_id = self.category_combo.get_active_id()

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM categories")
        self.category_combo.remove_all()
        for row in self.categories_list_box.get_children():
            self.categories_list_box.remove(row)

        grid = Gtk.Grid()
        self.categories_list_box.add(grid)

        col1 = Gtk.Label("Category")
        col2 = Gtk.Label("Total Time")
        grid.attach(col1, 0, 0, 1, 1)
        grid.attach(col2, 1, 0, 1, 1)

        row = 1
        for category_id, name in cursor.fetchall():
            self.category_combo.append(str(category_id), name)

            total_time = self.get_category_total_time(category_id)
            category_label = Gtk.Label(name)
            category_label.set_halign(Gtk.Align.START)
            total_time_label = Gtk.Label(self.format_time(total_time))
            grid.attach(category_label, 0, row, 1, 1)
            grid.attach(total_time_label, 1, row, 1, 1)
            row += 1
        
        # Set the active category back to the previously active category ID
        if current_active_id is not None:
            self.category_combo.set_active_id(current_active_id)
        else:
            self.category_combo.set_active(0)
        
        # Set the active category
        if new_category_id is not None:
            self.category_combo.set_active_id(str(new_category_id))

        self.categories_list_box.show_all()
        
    def on_export_button_clicked(self, widget):
        # Create a new file chooser dialog
        dialog = Gtk.FileChooserDialog(
            "Export Categories",
            self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        )

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
                f.write(f"Date/Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
                # Write the categories and their times to the file
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name FROM categories")
                for category_id, name in cursor.fetchall():
                    total_time = self.get_category_total_time(category_id)
                    f.write(f"{name}: {self.format_time(total_time)}\n")

            print(f"Categories exported to {filename}")

        dialog.destroy()
        
    def on_edit_category_button_clicked(self, widget):
        category_id = self.category_combo.get_active_id()
        if category_id is not None:
            category_name = self.category_combo.get_active_text()
            dialog = Gtk.Dialog(title="Edit Category", parent=self, flags=0)

            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK)

            content_area = dialog.get_content_area()
            label = Gtk.Label("New Category Name:")
            content_area.add(label)

            entry = Gtk.Entry()
            entry.set_text(category_name)
            content_area.add(entry)

            dialog.show_all()
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                new_name = entry.get_text().strip()
                if new_name:
                    cursor = self.conn.cursor()
                    cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id))
                    self.conn.commit()
                    self.load_categories()

        dialog.destroy()
        
    def on_delete_category_button_clicked(self, widget):
        category_id = self.category_combo.get_active_id()
        if category_id is not None:
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
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM records WHERE category_id = ?", (category_id,))
                cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                self.conn.commit()
                self.load_categories()
                self.update_total_time()
                
                # Set the combo-box to the first element after deleting a category
                self.category_combo.set_active(0)

            dialog.destroy()
            
    def update_total_time(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT elapsed_time FROM records")
        times = cursor.fetchall()

        self.total_time = 0
        for elapsed_time, in times:
            time_parts = elapsed_time.split(':')
            hours, mins, secs = [int(part) for part in time_parts[:-1]] + [float(time_parts[-1])]
            self.total_time += hours * 3600 + mins * 60 + secs

        self.total_time_label.set_markup(f"<big>Total time: {self.format_time(self.total_time)}</big>")
        cursor.execute("UPDATE total_time SET accumulated_time = ? WHERE id = 1", (self.total_time,))
        self.conn.commit()


    def get_category_total_time(self, category_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT elapsed_time FROM records WHERE category_id = ?", (category_id,))
        times = cursor.fetchall()

        total_time = 0
        for elapsed_time, in times:
            time_parts = elapsed_time.split(':')
            hours, mins, secs = [int(part) for part in time_parts[:-1]] + [float(time_parts[-1])]
            total_time += hours * 3600 + mins * 60 + secs
        return total_time

    def update_label(self):
        elapsed_time = time.perf_counter() - self.start_time
        self.timer_label.set_markup(f"<big>{self.format_time(elapsed_time)}</big>")
        return self.running

    def on_button_clicked(self, widget):
        if not self.running:
            self.start_time = time.perf_counter()
            self.running = True
            GLib.timeout_add(100, self.update_label)
            self.button.set_label("Stop")
        else:
            self.running = False
            elapsed_time = time.perf_counter() - self.start_time
            formatted_time = self.format_time(elapsed_time)
            self.timer_label.set_markup(f"<big>{formatted_time}</big>")
            self.button.set_label("Start")

            category_id = int(self.category_combo.get_active_id())
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO records (category_id, elapsed_time) VALUES (?, ?)", (category_id, formatted_time))
            self.conn.commit()

            self.total_time += elapsed_time
            self.total_time_label.set_markup(f"<big>Total time: {self.format_time(self.total_time)}</big>")
            cursor.execute("UPDATE total_time SET accumulated_time = ? WHERE id = 1", (self.total_time,))
            self.conn.commit()

            self.load_categories()
            self.update_total_time()

    def on_add_category_button_clicked(self, widget):
        dialog = Gtk.Dialog(title="Add Category", parent=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        label = Gtk.Label("New Category Name:")
        content_area.add(label)

        entry = Gtk.Entry()
        content_area.add(entry)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            category_name = entry.get_text().strip()
            if category_name:
                cursor = self.conn.cursor()
                try:
                    cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
                    self.conn.commit()
                    # Get the ID of the new category
                    new_category_id = cursor.lastrowid
                    self.load_categories(new_category_id)
                except sqlite3.IntegrityError:
                    print(f"Category '{category_name}' already exists")

        dialog.destroy()

    def on_destroy(self):
        self.conn.close()

app = TimerApp()
app.connect("destroy", Gtk.main_quit)
app.show_all()
Gtk.main()

