class Format:
    def format_time(self, elapsed_time):
        if elapsed_time is None:
            return "00:00:00"
        else:
            is_negative = elapsed_time < 0
            if is_negative:
                elapsed_time = -elapsed_time

            hours, rem = divmod(elapsed_time, 3600)
            mins, secs = divmod(rem, 60)
            rounded_secs = round(secs, 0)  # Round seconds to 2 decimal places

            formatted_time = f"{int(hours):02d}:{int(mins):02d}:{rounded_secs:02.0f}"
            if is_negative:
                formatted_time = f"-{formatted_time}"

            return formatted_time
