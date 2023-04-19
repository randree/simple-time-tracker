class Format:
    def format_time(elapsed_time):
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