import configparser
import os


class Config:
    def __init__(self, config_file):
        self.config_file = config_file

    def load_window_config(self, window, window_name, x_0, y_0, width_0,  height_0):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            x = int(config.get(window_name, "x", fallback=x_0))
            y = int(config.get(window_name, "y", fallback=y_0))
            width = int(
                config.get(window_name, "width", fallback=width_0))
            height = int(
                config.get(window_name, "height", fallback=height_0))
            window.move(x, y)
            window.resize(width, height)

    def save_window_config(self, window, window_name):
        config = configparser.ConfigParser()

        # Read the existing configuration file
        if os.path.exists(self.config_file):
            config.read(self.config_file)

        x, y = window.get_position()
        width, height = window.get_size()

        if not config.has_section(window_name):
            config.add_section(window_name)

        config.set(window_name, "x", str(x))
        config.set(window_name, "y", str(y))
        config.set(window_name, "width", str(width))
        config.set(window_name, "height", str(height))

        # Write the changes back to the configuration file
        with open(self.config_file, "w") as config_file:
            config.write(config_file)
