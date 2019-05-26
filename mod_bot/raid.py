from datetime import datetime
from datetime import timedelta

raid_date_format = ['%Hh%M', '@%Hh%M', '%M', '%Mmn', '%Mmin', '%Mminutes']


def get_raid_hours(time, raid_duration, message_date):
    """
    Raid hour can be declare in 3 different ways:
    - @hh:mm|@h:mm raid starts at the given hour
    - hh:mm|h:mm raid ends at the given hour
    - mm|m raid ends in m|mm minutes
    :param time: hour or duration
    :param raid_duration: duration of a raid in minutes
    :param message_date: time the raid command was issued
    :return: starttime: time, endtime: time
    """

    is_at_time = '@' in time
    is_minutes_time = 'h' not in time

    raid_time = try_parsing_date(time)

    if raid_time is None:
        return None

    if is_at_time:
        starttime = raid_time
        endtime = raid_time + timedelta(minutes=raid_duration)
    else:
        if is_minutes_time:
            minutes = raid_time.minute
            starttime = message_date
            endtime = message_date + timedelta(minutes=minutes)
        else:  # Todo: might be not useful with the minutes remaining command
            starttime = raid_time - timedelta(minutes=raid_duration)
            endtime = raid_time

    return starttime.time(), endtime.time()


def try_parsing_date(text):
    for fmt in raid_date_format:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return None


def clean_raid_command(command):
    """
    - Remove empty parts
    - Attach '!' to 'raid' if it was incorrectly separated
    - Attach '@' to 'raid' if it was incorrectly separated
    :param command: raid command as a list
    :return: a properly formatted raid command
    """
    return fix_lone_exclamation_sign(fix_lone_at_sign(clean_empty_parts(command)))


def clean_empty_parts(command):
    return clean_char(command, '')


def clean_char(command, char):
    return list(filter(lambda part: part.strip() != char, command))


def fix_lone_exclamation_sign(command):
    return fix_lone_sign(command, '!')


def fix_lone_at_sign(command):
    return fix_lone_sign(command, '@')


def fix_lone_sign(command, char):
    """
    Find the first given char that is the only char in one part of the command, attach it to the next part
    :param command: a raid command
    :param char: the char to look for
    :return: the command with the char attach to the next part if it was alone
    """
    try:
        index = command.index(char)
        command.pop(index)
        command[index] = char + command[index]
        return command
    except ValueError:
        return command
