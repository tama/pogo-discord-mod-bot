import os
import json
import pprint

def read_config(path):
    print("reading configuration")
    if os.path.exists(path) is False:
        return {}

    with open(path, 'r') as f:
        conf = json.load(f)
    load_guilds_config(conf)
    return conf

def load_guilds_config(conf):
    if "filepath" in conf and "listen_to" in conf:
        for gid in list(conf["listen_to"]):
            load_guild_config(gid, conf)

def load_guild_config(gid, conf):
        gconf_path = "{0}/{1}/config.json".format(conf["filepath"], gid)
        if os.path.exists(gconf_path):
            with open(gconf_path) as f:
                conf["listen_to"][gid]["conf"] = json.load(f)

def get(gid, path, conf):
    # Try to find the key in the specific configuration file for this guild
    val = None
    if gid is not None:
        subpath = 'listen_to.{0}.conf'.format(gid)
        if get_key(subpath, conf) is not None:
            val = get_key('{0}.{1}'.format(subpath, path), conf)

    if val is None:
        # Not found in specific configuration, try the global configuration
        val = get_key(path, conf)
    return val


def has_key(path, conf):
    return get_key(path, conf) is not None

def get_key(path, conf):
    # Parse the path passed as parameter
    parts = path.split('.')

    ptr = conf
    for part in parts:
        if part not in ptr:
            # Invalid path
            #print('Invalid path at {0}'.format(part))
            return None
        ptr = ptr[part]
    return ptr

def set_key(path, conf, gid, value):
    if has_key('filepath', conf) is False:
        print("No 'filepath' found in global config file, can't continue")
        return

    gconf_path = '{0}/{1}/config.json'.format(conf['filepath'], gid)
    cur_config = read_config(gconf_path)
    parts = path.split('.')
    ptr = cur_config
    for part in parts[:-1]:
        if part not in ptr:
            ptr[part] = {}
        ptr = ptr[part]
    ptr[parts[-1]] = value

    # Update values so that the next read returns the new value
    with open(gconf_path, 'w') as f:
        json.dump(cur_config, f)
    
    load_guild_config(gid, conf)

def dump(obj):
    pprint.pprint(obj, indent=4)
