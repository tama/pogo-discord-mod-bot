#!/usr/bin/env python3.5
# coding: utf-8

import asyncio
import collections
import datetime
import json
import os
import pickle
import time

import discord
import pytz

import roulette
from gym import load_gyms, get_approx_name
from conf import read_config, get, has_key, set_key, dump
from raid import clean_raid_command, get_raid_hours

client = discord.Client()
is_connected = False

MAX_MESSAGE_SIZE = 2000
paris_tz = pytz.timezone('Europe/Paris')

ddb_list = {'timeouts': {}, 'messages':{}}

def get_token():
    token = None
    with open(".token", "r") as f:
        token = f.read()
    return token

def add_minutes(hstart, mstart, mn):
    if mn < 0 and mstart < int(-mn % 60):
        carry = -1
    elif mn > 0 and int(mstart + (mn % 60)) > 59:
        carry = 1
    else:
        carry = 0
        
    hend = int((hstart + int(mn / 60)) + carry) % 24
    mend = int((mstart + mn % 60) % 60)
    return (hend, mend)
    
@client.event
async def on_ready():
    global conf
    conf = read_config('config.json')
    print("on_ready")
    dump(conf)

@client.event
async def on_message(message):
    muted_users = {}
    if os.path.exists("muted"):
        muted_users = load("muted")
    words = message.content.split(' ')
    raid_words = clean_raid_command(words)

    # Message information
    author = message.author.name
    cid = str(message.channel.id)
    gid = str(message.channel.guild.id)

    mute_can_use = get(gid, 'mute.can_use_command', conf)
    if mute_can_use is not None and author in mute_can_use:
        if words[0] == '!mute':
            muted_until = int(time.time() + int(words[2]))
            muted_users[words[1]] = muted_until
            save("muted", muted_users)
            return

        if words[0] == '!unmute':            
            del(muted_users[words[1]])
            save("muted", muted_users)
            return

    # Mod commands
    roles = discord.utils.get(message.guild.members, name=message.author.name).roles
    mod_roles = get(gid, 'mod.roles', conf).split(';')
    is_mod = False
    for r in roles:
        if r.name in mod_roles:
            is_mod = True
            break

    if is_mod is True:
        if words[0] == "!setcfg" and len(words) > 2:
            scope = words[1].split(".")[0]
            if scope != "private":
                set_key(words[1], conf, gid, ' '.join(words[2:]))
            return

        if words[0] == "!getcfg" and len(words) > 1:
            scope = words[1].split(".")[0]
            if scope != "private":
                val = str(get(gid, words[1], conf))
                await message.channel.send("{0} = {1}".format(words[1], val))
            return

    if gid == '322379168048349185' and author in muted_users:
        if int(time.time()) < int(muted_users[author]):
            print("muted until {0} (current {1})".format(muted_users[author], int(time.time()))) 
            await message.delete()
            return
        else:
            del(muted_users[author])
            save("muted", muted_users)

    if is_listen_to(gid) and get(None, 'listen_to.{0}.channel'.format(gid), conf) == cid and author != 'modbot':
        should_delete = True
        message_to_send = ''

        gym_list = load_gyms(gid, get(None, "filepath", conf))

        if message.content == "LIST":
            should_delete = False
            od = collections.OrderedDict(sorted(gym_list.items()))
            for k in od:
                message_to_send += k + "\n"
            
        if raid_words[0] == "!raid":
            isOk = True

            words = raid_words
            if len(words) < 3:
                message_to_send = '''Commande incorrecte.
Format des messages : !raid *pokemon* *arene* *heureDeFin* (exemple : !raid latias tour tf1 13:15)
LIST pour avoir la liste des arènes reconnues'''
                isOk = False

            poke = words[1][:5].lower()
            gym_name = ' '.join(words[2:-1])
            gym_data = None
            if isOk is True:
                if gym_name not in gym_list:
                    gym_data = get_approx_name(gym_name, gym_list)
                else:
                    gym_data = [gym_list[gym_name]]

            if len(gym_data) == 0:
                message_to_send = 'Arène "{0}" inconnue\n'.format(gym_name)
                isOk = False
                should_delete = False
            elif len(gym_data) > 10:
                message_to_send = "L'arène n'a pas pu être trouvée\n"
                message_to_send += "La requête n'est pas assez spécifique, {0} résultats possibles\n".format(len(gym_data))
                message_to_send += "Veuillez préciser votre recherche, utilisez `LIST` pour trouver votre arène\n"
                isOk = False
                should_delete = False
            elif len(gym_data) >= 2:
                message_to_send = "L'arène n'a pas pu être trouvée\n"
                message_to_send += "Vouliez vous dire l'un des choix suivants?\n"
                message_to_send += ", ".join(map(lambda x: x[1], gym_data)) + "\n"
                isOk = False
                should_delete = False
            else:
                gym_data = gym_data[0]

            raid_hour = words[-1]
            message_creation_date_localtz = pytz.utc.localize(message.created_at).astimezone(paris_tz)
            starttime, endtime = get_raid_hours(raid_hour, int(get(gid, 'raid_duration', conf)), message_creation_date_localtz)
            if starttime is None or endtime is None:
                message_to_send += 'Heure "{0}" incorrecte, formats possibles: 10:30, 10h30,' \
                                   ' @10h30, 30mn, 30min, 30minutes)\n'.format(raid_hour)
                isOk = False

            if isOk is True:
                pop_hour = starttime.strftime('%Hh%M')
                end_hour = endtime.strftime('%Hh%M')
                should_delete = False
                channel_name = "{0}-{1}-fin{2}".format(poke, gym_data[0], end_hour)

                similar_channel = get_similar_channel(message.channel.guild, gym_data[0], end_hour)
                if similar_channel is not None:
                    await message.channel.send("Un salon a déjà été crée pour ce raid : <#{0}>".format(similar_channel.id))
                    return
                
                new_channel = await message.channel.guild.create_text_channel(channel_name)

                # Get banner (message posted before the listing)
                banner_msg_file_loc = get(gid, 'private.banner_msg_file', conf)
                if banner_msg_file_loc is None:
                    banner_msg_file_loc = get(None, 'private.banner_msg_file', conf)
                if banner_msg_file_loc is not None:
                    with open(banner_msg_file_loc, "r", encoding="utf8") as bf:
                        banner_msg = bf.read()
                        await new_channel.send(banner_msg)
                
                raid_info = '''
**Horaires** : [[POP_HOUR]] -> [[END_HOUR]]
**Pokémon** : [[POKEMON]]
**Arène** : [[ARENE]]
**Adresse** : [[ADDRESS]]
**Google maps** : <https://maps.google.com/?daddr=[[lat]],[[lng]]>
'''
                raid_info = raid_info.replace('[[POP_HOUR]]', pop_hour)
                raid_info = raid_info.replace('[[END_HOUR]]', end_hour)
                raid_info = raid_info.replace('[[POKEMON]]', words[1].capitalize())
                raid_info = raid_info.replace('[[ARENE]]', gym_data[1].capitalize())
                raid_info = raid_info.replace('[[ADDRESS]]', gym_data[2] if gym_data[2] is not None else '')
                raid_info = raid_info.replace('[[lat]]', gym_data[3])
                raid_info = raid_info.replace('[[lng]]', gym_data[4])
                if gym_data[5] is True:
                    raid_info = raid_info + "\n\n**Cette arène est éligible pour un raid EX**"
                info_msg = await new_channel.send(raid_info)

                await info_msg.pin()

                async for message_in_channel in new_channel.history(limit = 10):
                    if len(message_in_channel.content) == 0:
                        await message_in_channel.delete()
                
                await message.add_reaction(u"\u2705")

        if len(message_to_send) > 0:
            # Hack to handle long messages
            size = len(message_to_send)
            if size >= MAX_MESSAGE_SIZE:
                lines = message_to_send.split("\n")
                chunk_message = ""
                for line in lines:
                    if len(chunk_message) + len(line) > MAX_MESSAGE_SIZE:
                        await message.channel.send(chunk_message)
                        chunk_message = ""
                    chunk_message += line + "\n"
                await message.channel.send(chunk_message)
            else:
                await message.channel.send(message_to_send)

        if should_delete is True:
            await message.delete()
        return

    if words[0] == '!reg' and len(words) > 1:
        ppath = '{0}/{1}/player_data'.format(get(None, 'filepath', conf), gid)
        if os.path.exists(ppath):
            d = load(ppath)
        else:
            d = {}

        pkey = '{0}#{1}'.format(message.author.name, message.author.discriminator)
        pkey = pkey.encode('utf8')
        tstr = words[1].lower()
        teams = [tstr.count('y'), tstr.count('b'), tstr.count('r')]
        d[pkey] = teams
        save(ppath, d)

    if words[0] == '!pokemon' and len(words) > 1 and 'fin' in message.channel.name:
        cwords = message.channel.name.split('-')
        pokemon_name = words[1].replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('à', 'a').replace('â', 'a')
        new_name = pokemon_name[:5] + '-' + '-'.join(cwords[-2:])
        await message.channel.edit(name=new_name)
        return

    if words[0] == '!time' and len(words) > 1 and 'fin' in message.channel.name:
        cwords = message.channel.name.split('-')
        new_time = None
        for fmt in ('%Hh%M', '%H:%M'):
            try:
                if new_time is None:
                    new_time = datetime.datetime.strptime(words[1], fmt).time()
            except ValueError:
                pass
        if new_time is not None:
            new_name = '-'.join(cwords[:-1] + [new_time.strftime('fin%Hh%M')])
            await message.channel.edit(name=new_name)
            await message.channel.send('@here Heure de fin de raid mise à jour : ' + new_time.strftime('%Hh%M'))
        else:
            await message.channel.send('Format invalide ex: 14h17, 9:34')
        return

def get_similar_channel(server, gym_name, end_hour):
    tz = pytz.timezone('Europe/Paris')
    this_etime = datetime.datetime.strptime(end_hour, '%Hh%M')
    this_loc_etime = tz.localize(this_etime)
    for channel in list(server.channels):
        if not 'fin' in channel.name:
            continue

        other_gym_name = channel.name.split('-')[-2]
        if other_gym_name != gym_name:
            continue

        other_end_time_str = channel.name.split('-')[-1].replace('fin', '')
        other_etime = datetime.datetime.strptime(other_end_time_str, '%Hh%M')
        other_loc_etime = tz.localize(other_etime)

        delta = this_loc_etime - other_loc_etime if this_loc_etime > other_loc_etime else other_loc_etime - this_loc_etime
        #print(this_loc_etime, other_loc_etime, delta)
        if delta < datetime.timedelta(seconds = 600):
            return channel

    # Not found.
    return None


async def run(token):
    await client.login(token.strip())
    await client.connect()

async def modtask():
    tz = pytz.timezone('Europe/Paris')

    while True:
        now = datetime.datetime.now()
        now_tz = tz.localize(now)
        
#        print("Doing mod tasks")
        for server in client.guilds:
            warn_interval = int(get(server.id, "mod.warn_interval", conf))
            delete_interval_after_warning = int(get(server.id, "mod.delete_interval_after_warning", conf))
            listen_to = get(None, 'listen_to.{0}.channel'.format(server.id), conf)
            clean_cmd_after = get(server.id, 'mod.delete_cmd_after', conf)

#            print(warn_interval, delete_interval_after_warning, listen_to, clean_cmd_after)

            for channel in list(server.channels):
                try:
                    if listen_to is not None and clean_cmd_after is not None and str(listen_to) == str(channel.id) :
                        async for message in channel.history(limit = 10):
                            time_delta = now_tz - get_local_time(message.created_at)
                            if (time_delta > datetime.timedelta(seconds = 60 * int(clean_cmd_after))):
                                await message.delete()

                    if 'fin' not in channel.name or (channel.topic is not None and len(channel.topic) > 0):
                        continue

                    end_time_str = channel.name.split('-')[-1].replace('fin', '')
                    try:
                        etime = datetime.datetime.strptime(end_time_str, '%Hh%M')
                    except:
                        continue
                    
                    end_time = datetime.datetime(now.year, now.month, now.day, etime.hour, etime.minute)
                    end_time += datetime.timedelta(seconds = 60 * warn_interval)
                    end_time_tz = tz.localize(end_time)
                    
                    last_message_timestamp = None
                    last_modbot_tz = None
                    last_message_tz = None
                    
                    # Recherche dans les 5 derniers messages le dernier ne
                    # provenant pas de modbot
                    last_message = None
                    last_message_tz = None
                    #print(channel.name.encode())
                    async for message in channel.history(limit = 5):
                        if last_message is None:
                            last_message = message
                            
                        message_ts = get_local_time(message.created_at)
                        
                        if message.author.name != 'modbot':
                            last_message_tz = message_ts
                            break

                        if last_modbot_tz is None and message_ts > end_time_tz:
                            #print("MOD")
                            last_modbot_tz = message_ts


                    if last_message_tz is None:
                        continue

                    if last_modbot_tz is not None:
                        time_since_modbot = now_tz - last_modbot_tz
                    else:
                        time_since_modbot = datetime.timedelta(seconds=0)
        
                    time_delta = now_tz - last_message_tz
                    time_since_end = now_tz - end_time_tz

                    #print("now = {0}, end_time = {1}, last_message = {2} ({3}), last_modbot = {4} ({5})".format(now_tz, end_time_tz, last_message_tz, time_delta, last_modbot_tz, time_since_modbot))
                    
                    if now_tz < end_time_tz:
                        continue

                    if time_since_modbot > datetime.timedelta(seconds = 60 * delete_interval_after_warning):
                        #print("DELETE {0}".format(channel.name.encode('utf8')))
                        await channel.delete()  
                    elif time_delta > datetime.timedelta(seconds = 60 * warn_interval) and (last_message.author.name != 'modbot' or last_modbot_tz is None):
                        #print("Warning {0}".format(channel.name.encode('utf8')))
                        await channel.send("Aucun message n'a été posté depuis plus de {0} minutes après la fin du raid, ce salon sera automatiquement archivé dans {1} minutes.\n**Si ce salon n'est pas destiné à être supprimé, veuillez contacter un modérateur/administrateur**".format(warn_interval, delete_interval_after_warning))                    
                except Exception as e:
                    print(str(e))

        await asyncio.sleep(30)

@client.event
async def on_reaction_add(reaction, user):
    global ddb_list

    if str(reaction.message.guild.id) != '322379168048349185':
        return

    channel_name = reaction.message.channel.name
    if channel_name not in ['blablabla', 'archive']:
        return
    
    if 'ddb' not in str(reaction).lower():
        return

    if reaction.message.id not in ddb_list['messages']:
        ddb_list['messages'][reaction.message.id] = []

    if user.name not in ['tama'] and user.name in ddb_list['messages'][reaction.message.id]:
        return

    if user.name in ddb_list['timeouts'] and time.time() < ddb_list['timeouts'][user.name]:
        return

    ddb_list['messages'][reaction.message.id].append(user.name)
    ddb_list['timeouts'][user.name] = time.time() + 15
    
    muted_users = load("muted")
    if user.name in muted_users:
        return

    who = roulette.roulette(user.name)

    if who is not None:
        muted_time = 90
        if who is 'Fako':
            muted_time = muted_time * 2
            if user.name is 'Fako':
                muted_time = muted_time * 2
        maxTimeout = 0
        await reaction.message.channel.send('[**Roulette DDB**] {0} ne peut plus poster pendant {1} secondes ({2})'.format(who, muted_time, user.name))
        if who in muted_users:
            maxTimeout = muted_users[who]
        muted_users[who] = max(maxTimeout, time.time() + muted_time)
        save("muted", muted_users)
        ddb_list = {'messages': {}, 'timeouts':{}}

def load(f):
    try:
        muted = pickle.load(open(f, "rb"))
    except EOFError:
        muted = {}
    return muted

def save(f, data):
    pickle.dump(data, open(f, "wb"))

def get_local_time(dt, tz = None):
    if tz is None:
        tz = pytz.timezone('Europe/Paris')
    return pytz.utc.localize(dt, is_dst=None).astimezone(tz)

def is_listen_to(id):
    return get(None, 'listen_to.{0}'.format(id), conf) is not None

if __name__ == '__main__':
    token = get_token()
    if token is not None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(run(token), modtask()))
