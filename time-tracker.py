# Time Tracker - A simple time tracking application using Python and GTK

import gi
import time
import sqlite3
import datetime

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk


class TimerApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Timer App")
        self.set_default_icon_name("clock-symbolic")
        self.set_border_width(10)
        
        clock_icon = Gtk.Image.new_from_icon_name("clock-symbolic", Gtk.IconSize.DIALOG)

        self.start_time = None
        self.running = False

        # New variable to hold the currently selected category ID
        self.current_category_id = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        vbox.pack_start(clock_icon, True, True, 0)

        self.timer_label = Gtk.Label()
        self.timer_label.set_markup("<big>00:00:00.0</big>")
        vbox.pack_start(self.timer_label, True, True, 0)

        self.total_time_label = Gtk.Label()
        vbox.pack_start(self.total_time_label, True, True, 0)
        
        self.category_label = Gtk.Label(label="Category")
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

        # Set up the CSS style
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(self.load_css())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Load the CSS styles
        self.set_button_color("stop")

        vbox.pack_start(self.button, True, True, 0)

        self.init_db()

        # Load the last active category from the database
        cursor = self.conn.cursor()
        cursor.execute("SELECT active_category_id FROM settings WHERE id = 1")
        active_category_id = cursor.fetchone()[0]

        # Set the default value of the category_combo to the last active category
        if active_category_id is not None:
            self.category_combo.set_active_id(str(active_category_id))

    def set_button_color(self, color_class):
        style_context = self.button.get_style_context()
        if color_class == "start":
            style_context.remove_class("stop")
            style_context.add_class("start")
        elif color_class == "stop":
            style_context.remove_class("start")
            style_context.add_class("stop")

    def load_css(self):
        return b"""
        .start {
            background-image: linear-gradient(to bottom, #990000, #990000);
            color: #ffffff;
            border-radius: 3px;
        }
        .start:hover {
            background-image: linear-gradient(to bottom, #800000, #800000);
            color: #ffffff;
            border-radius: 3px;
        }

        .stop {
            background-image: linear-gradient(to bottom, #009933, #009933);
            color: #ffffff;
            border-radius: 3px;
        }
        .stop:hover {
            background-image: linear-gradient(to bottom, #006622, #006622);
            color: #ffffff;
            border-radius: 3px;
        }
        #active_category {
            color: #a30000
        }
        """
        self.css_provider.load_from_data(css)

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

        cursor.execute('''CREATE TABLE IF NOT EXISTS settings
                      (id INTEGER PRIMARY KEY, active_category_id INTEGER)''')
        cursor.execute("INSERT OR IGNORE INTO settings (id, active_category_id) VALUES (1, NULL)")


        cursor.execute("SELECT accumulated_time FROM total_time WHERE id = 1")
        self.total_time = cursor.fetchone()[0]
        self.total_time_label.set_markup(f"<big>Total time: {self.format_time(self.total_time)}</big>")

        self.load_categories()

    def format_time(self, elapsed_time):
        is_negative = elapsed_time < 0
        if is_negative:
            elapsed_time = -elapsed_time

        hours, rem = divmod(elapsed_time, 3600)
        mins, secs = divmod(rem, 60)
        rounded_secs = round(secs, 2)  # Round seconds to 2 decimal places

        formatted_time = f"{int(hours):02d}:{int(mins):02d}:{rounded_secs:04.1f}"
        if is_negative:
            formatted_time = f"-{formatted_time}"

        return formatted_time
        

    def load_categories(self, new_category_id=None):
        current_active_id = self.category_combo.get_active_id()

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM categories")
        self.category_combo.remove_all()
        for row in self.categories_list_box.get_children():
            self.categories_list_box.remove(row)

        grid = Gtk.Grid()
        self.categories_list_box.add(grid)

        col1 = Gtk.Label(label="Category")
        col2 = Gtk.Label(label="Total Time")
        grid.attach(col1, 0, 0, 1, 1)
        grid.attach(col2, 1, 0, 1, 1)

        row = 1
        for category_id, name in cursor.fetchall():
            self.category_combo.append(str(category_id), name)

            total_time = self.get_category_total_time(category_id)

            # if str(category_id) == current_active_id:
            #     category_label = Gtk.Label(label=name, name="active_category")
            # else:
            category_label = Gtk.Label(label=name)

            category_label.set_halign(Gtk.Align.START)
            category_label.set_margin_top(2)
            category_label.set_margin_bottom(2)
            category_label.set_margin_start(5)
            category_label.set_margin_end(5)

            total_time_label = Gtk.Label(label=self.format_time(total_time))
            total_time_label.set_margin_top(2)
            total_time_label.set_margin_bottom(2)
            total_time_label.set_margin_start(5)
            total_time_label.set_margin_end(5)
            grid.attach(category_label, 0, row, 1, 1)
            grid.attach(total_time_label, 1, row, 1, 1)
            row += 1

       
        # Set the active category back to the previously active category ID
        if current_active_id is not None:
            self.category_combo.set_active_id(current_active_id)
        else:
            self.category_combo.set_active(0)
        
        # # Set the active category
        if new_category_id is not None:
            self.category_combo.set_active_id(str(new_category_id))

         # Store the current category ID
        if self.category_combo.get_active_id() is not None:
            self.current_category_id = int(self.category_combo.get_active_id())
 
        self.categories_list_box.show_all()
        
    def on_export_button_clicked(self, widget):
        # Create a new file chooser dialog
        dialog = Gtk.FileChooserDialog(
            "Export Categories",
            self,
            Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

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
            old_total_time = self.get_category_total_time(category_id)

            dialog = Gtk.Dialog(title="Edit Category", parent=self, flags=0)

            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK)

            content_area = dialog.get_content_area()
            label = Gtk.Label(label="New Category Name:")
            content_area.add(label)

            entry = Gtk.Entry()
            entry.set_text(category_name)
            content_area.add(entry)

            label_total_time = Gtk.Label(label="New Total Time (HH:MM:SS.ss):")
            content_area.add(label_total_time)

            entry_total_time = Gtk.Entry()
            entry_total_time.set_text(self.format_time(old_total_time))
            content_area.add(entry_total_time)

            dialog.show_all()
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                new_name = entry.get_text().strip()
                new_time_str = entry_total_time.get_text().strip()

                if new_name:
                    cursor = self.conn.cursor()
                    cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id))
                    self.conn.commit()

                if new_time_str:
                    new_total_time = round(sum(x * (int(t) if i != 2 else float(t)) for i, (x, t) in enumerate(zip([3600, 60, 1], new_time_str.split(":")))),2)
                    time_difference = round(new_total_time - round(old_total_time, 2), 2)

                    # print("CheckTime", self.format_time(time_difference), time_difference, new_total_time, old_total_time)
                    cursor = self.conn.cursor()
                    cursor.execute("INSERT INTO records (category_id, elapsed_time) VALUES (?, ?)", (category_id, self.format_time(time_difference)))
                    self.conn.commit()

                    self.total_time += time_difference
                    self.total_time_label.set_markup(f"<big>Total time: {self.format_time(self.total_time)}</big>")
                    cursor.execute("UPDATE total_time SET accumulated_time = ? WHERE id = 1", (self.total_time,))
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
            sign = -1 if time_parts[0].startswith('-') else 1
            time_parts[0] = time_parts[0].lstrip('-')
            hours, mins, secs = [int(part) for part in time_parts[:-1]] + [float(time_parts[-1])]
            time_in_seconds = sign * (hours * 3600 + mins * 60 + secs)
            self.total_time += time_in_seconds

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
            sign = -1 if time_parts[0].startswith('-') else 1
            time_parts[0] = time_parts[0].lstrip('-')
            hours, mins, secs = [int(part) for part in time_parts[:-1]] + [float(time_parts[-1])]
            time_in_seconds = sign * (hours * 3600 + mins * 60 + secs)
            total_time += time_in_seconds
        return round(total_time,2)

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
            self.set_button_color("start")
        else:
            self.running = False
            elapsed_time = time.perf_counter() - self.start_time
            formatted_time = self.format_time(elapsed_time)
            self.timer_label.set_markup(f"<big>{formatted_time}</big>")
            self.button.set_label("Start")
            self.set_button_color("stop")

            category_id = int(self.category_combo.get_active_id())
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO records (category_id, elapsed_time) VALUES (?, ?)", (category_id, formatted_time))
            self.conn.commit()

            # Store the current category ID
            self.current_category_id = category_id

            self.total_time += elapsed_time
            self.total_time_label.set_markup(f"<big>Total time: {self.format_time(self.total_time)}</big>")
            cursor.execute("UPDATE total_time SET accumulated_time = ? WHERE id = 1", (self.total_time,))
            self.conn.commit()

            self.load_categories()
            self.update_total_time()

            # Save the last active category to the database
            active_category_id = int(self.category_combo.get_active_id())
            cursor = self.conn.cursor()
            cursor.execute("UPDATE settings SET active_category_id = ?", (active_category_id,))
            self.conn.commit()

    def on_add_category_button_clicked(self, widget):
        dialog = Gtk.Dialog(title="Add Category", parent=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
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
                cursor = self.conn.cursor()
                try:
                    cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
                    self.conn.commit()
                    # Get the ID of the new category
                    new_category_id = cursor.lastrowid
                    self.load_categories(new_category_id)
                except sqlite3.IntegrityError:
                    print(f"Category '{category_name}' already exists")

            # Set the new category as the active category
            self.category_combo.append(str(new_category_id), category_name)
            self.category_combo.set_active_id(str(new_category_id))
        
            # Store the current category ID
            self.current_category_id = new_category_id

        dialog.destroy()

    def on_destroy(self):
        self.conn.close()

app = TimerApp()
app.connect("destroy", Gtk.main_quit)
app.show_all()
Gtk.main()

