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
