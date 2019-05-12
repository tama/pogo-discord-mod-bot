import Levenshtein

candidates_key = "candidates"


def get_approx_name(gym_name, gym_list):
    try:
        command = clean_name(gym_name)

        # Try autocomplete
        keys = gym_list.keys()
        gyms = list(map(lambda x: clean_name(x), keys))

        candidates = [gym for gym in gyms if command in gym]
        candidates = list(map(lambda x: find_gym_in_list(x, gyms, gym_list), candidates))
        if len(candidates) >= 1:
            return candidates

        # Try short_name
        short_gyms = list(map(lambda x: clean_name(x[0]), gym_list.values()))
        candidates = [gym for gym in short_gyms if command in gym]
        candidates = list(map(lambda short_name: find_gym_in_list(short_name, short_gyms, gym_list), candidates))
        if len(candidates) >= 1:
            return candidates

        # Try graph autocomplete
        tree = build_full_name_graph(gym_list)
        candidates = autocomplete_from_tree(tree, command)
        candidates = list(map(lambda x: find_gym_in_list(x, gyms, gym_list), candidates))
        if len(candidates) >= 1:
            return candidates

        # Try Levenshtein distance
        for k, v in gym_list.items():
            d = Levenshtein.distance(command, k)
            if d < 3:
                return [v]
    except Exception as e:
        # Failed.
        print(e)
        pass
    return []


def find_gym_in_list(gn, gyms, gym_list):
    """
    Here we suppose the gyms are in the same order as the gym_list, and have the same size
    :param gn: the name of the gym we want to find
    :param gyms: list of equally formatted gyms name in the same order as gym_list
    :param gym_list: the original gym_list
    :return: a gym
    """
    index = gyms.index(gn)
    keys = list(gym_list.keys())
    return gym_list[keys[index]]


def load_gyms(guild_id, file_path):
    gym_list = {}
    lines = [line.strip() for line in open("{0}/{1}/gym_with_coords".format(file_path, guild_id), "r", encoding="utf8")]
    for l in lines:
        sections = l.split(';')
        short_name = sections[0]
        full_name = sections[3]
        address = sections[4] if len(sections) > 4 else None
        ex = len(sections) > 5 and sections[5] == 'EX'
        gym_list[full_name] = (short_name, full_name, address, sections[1], sections[2], ex)
    return gym_list


def clean_name(s):
    return s.lower()\
        .replace('é', 'e').replace('è', 'e').replace('ê', 'e') \
        .replace('à', 'a').replace('â', 'a') \
        .replace("\'", "").replace("’", "")


def build_full_name_graph(gym_list):
    tree = {}
    for fullname in map(lambda x: clean_name(x), gym_list.keys()):
        first_letter = fullname[0]
        add_to_dict(tree, first_letter, fullname)
        dictionary = tree[first_letter]
        for letter in fullname[1::]:
            add_to_dict(dictionary, letter, fullname)
            dictionary = dictionary[letter]
    return tree


def add_to_dict(dictionary, letter, name):
    if letter not in dictionary:
        dictionary[letter] = {candidates_key: []}
    dictionary[letter][candidates_key].append(name)


def autocomplete_from_tree(tree, gn):
    result = []
    step = tree
    count = 0
    for letter in gn:
        if letter in step:
            result = step[letter][candidates_key]
            step = step[letter]
            count += 1
        else:
            break
    if count > 3:
        return result
    else:
        return []
