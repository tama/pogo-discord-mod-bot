from datetime import datetime
from datetime import timedelta
import re

raid_date_format = [
    {
        'format': '%Hh%M',
        'is_at_time': False
    }, {
        'format': '@%Hh%M',
        'is_at_time': True
    }, {
        'format': '%H:%M',
        'is_at_time': False
    }, {
        'format': '@%H:%M',
        'is_at_time': True
    }
]

minutes_regex = "\d+(mn|min|minutes)"


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
    raid_time, is_at_time = try_parsing_date(time)

    if raid_time is None:
        minutes = parse_minutes(time)
        if minutes is not None:
            endtime = message_date + timedelta(minutes=minutes)
            return (endtime - timedelta(minutes=raid_duration)).time(), endtime.time()
        else:
            return None, None

    if is_at_time:
        starttime = raid_time
        endtime = raid_time + timedelta(minutes=raid_duration)
    else:
        # Todo: might be not useful with the minutes remaining command
        starttime = raid_time - timedelta(minutes=raid_duration)
        endtime = raid_time

    return starttime.time(), endtime.time()


def try_parsing_date(raid_command):
    for fmt in raid_date_format:
        try:
            return datetime.strptime(raid_command, fmt['format']), fmt['is_at_time']
        except ValueError:
            pass
    return None, None


def parse_minutes(raid_command):
    """
    Because we use match, it works only if the string starts with a number
    :return: minutes as an integer
    """
    matcher = re.match(minutes_regex, raid_command)
    if matcher is None:
        return None
    minutes = int(re.match("\d+", matcher.group(0)).group(0))
    if minutes > 0:
        return minutes
    else:
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
