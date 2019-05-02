#!/usr/bin/env python3.5
# coding: utf-8

import asyncio
import discord

import re
import datetime
import pytz

import os
import pickle
import collections

import Levenshtein
import time

from mod_bot import roulette

client = discord.Client()
is_connected = False

listen_to = {
    353624316585443329: 422859285622685708, #Sevres
    322379168048349185: 426716226274983957, #Boulbi
    353176435026034690: 441684675690364938, #Serveur de test
    387160186424655872: 462991996131344405  #Paris 16
}

MAX_MESSAGE_SIZE = 2000

conf = {}
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
    print("on_ready")
    print(conf)
    is_connected = True

@client.event
async def on_message(message):
    muted_users = load("muted")
    words = message.content.split(' ')

    if str(message.guild.id) == '322379168048349185' and message.author.name in ['tama', 'Killerlolo']:
        if words[0] == '!mute':
            muted_until = int(time.time() + int(words[2]))
            muted_users[words[1]] = muted_until
            save("muted", muted_users)
            return

        if words[0] == '!unmute':            
            del(muted_users[words[1]])
            save("muted", muted_users)
            return

    if str(message.guild.id) == '322379168048349185' and message.author.name in muted_users:
        if int(time.time()) < int(muted_users[message.author.name]):
            print("muted until {0} (current {1})".format(muted_users[message.author.name], int(time.time()))) 
            await message.delete()
            return
        else:
            del(muted_users[message.author.name])
            save("muted", muted_users)
    
    if message.channel.guild.id in listen_to and listen_to[message.channel.guild.id] == message.channel.id and message.author.name != 'modbot':
        should_delete = True
        message_to_send = ''

        gym_list = load_gyms(message.channel.guild.id, conf["filepath"])

        if message.content == "LIST":
            should_delete = False
            message_to_send += "```"
            od = collections.OrderedDict(sorted(gym_list.items()))
            for k in od:
                message_to_send += k + "\n"
            message_to_send += "```"
            
        if words[0] == "!raid":
            isOk = True
            
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
                    gym_data = gym_list[gym_name]

            if gym_data is None:
                message_to_send = 'Arène "{0}" inconnue\n'.format(gym_name)
                isOk = False
                should_delete = False
                
            if isOk is True:
                hour_pattern = re.compile("@*((0*[0-9])|(1[0-9])|(2[0-3]))[:hH]([0-5][0-9])")
                end_hour = words[-1]
                m = hour_pattern.match(end_hour)
                if m is None:
                    message_to_send += 'Heure "{0}" incorrecte (format 10:30, 10h30, ou @10h30)'.format(end_hour)
                    isOk = False

            if isOk is True:
                end_hour = end_hour.replace(':', 'h').lower()
                h = end_hour.replace('@', '').split('h')[0]
                if end_hour[0] == '@':
                    # Heure de pop, calcule l'heure de fin
                    pop_hour = ('0' if int(h) < 10 and len(h) < 2 else '') + end_hour[1:]
                    hend = int(pop_hour.split('h')[0])
                    mend = int(pop_hour.split('h')[1])
                    endtime = add_minutes(hend, mend, int(conf["raid_duration"]))
                    end_hour = "{0:02d}h{1:02d}".format(endtime[0], endtime[1])
                else:
                    end_hour = ('0' if int(h) < 10 and len(h) < 2 else '') + end_hour
                    hend = int(end_hour.split('h')[0])
                    mend = int(end_hour.split('h')[1])
                    starttime = add_minutes(hend, mend, -int(conf["raid_duration"]))
                    pop_hour = "{0:02d}h{1:02d}".format(starttime[0], starttime[1])

                should_delete = False
                channel_name = "{0}-{1}-fin{2}".format(poke, gym_data[0], end_hour)

                similar_channel = get_similar_channel(message.channel.guild, gym_data[0], end_hour)
                if similar_channel is not None:
                    await message.channel.send("Un salon a déjà été crée pour ce raid : <#{0}>".format(similar_channel.id))
                    return
                
                new_channel = await message.channel.guild.create_text_channel(channel_name)
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
        ppath = '/home/tama/bot/data/{0}/player_data'.format(message.channel.guild.id)
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

def get_approx_name(gym_name, gym_list):
    result = None
    try:
        gn = gym_name.lower()
        gn = gn.replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('à', 'a').replace('â', 'a')

        # Try autocomplete
        gyms = list(gym_list.keys())
        candidates = [x for x in gyms if gym_name.lower() in x]
        if len(candidates) == 1:
            result = gym_list[candidates[0]]
        else:
            candidates = [x for x in gyms if gn in x.lower()]
            if len(candidates) == 1:
                result = gym_list[candidates[0]]
        
        # Try Levenshtein distance
        if result is None:
            for k,v in gym_list.items():
                if gn == k:
                    result = v
                    break

                d = Levenshtein.distance(gn, k)
                if d < 3:
                    result = v
                    break
    except Exception as e:
        # Failed.
        print(e)
        pass
    return result


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
    
async def run(token):
    await client.login(token)
    await client.connect()

async def modtask():
    tz = pytz.timezone('Europe/Paris')

    while True:
        try:
            print("Modtask")
            now = datetime.datetime.now()
            now_tz = tz.localize(now)

            ignored = conf["ignored"].split(";")

    #        print("Doing mod tasks")
            for server in client.guilds:
                for channel in list(server.channels):
                    #print("{} ({})".format(channel.name.encode(), channel.id))

                    if 'fin' not in channel.name or (channel.topic is not None and len(channel.topic) > 0) or str(channel.id) in ignored:
                        continue

                    end_time_str = channel.name.split('-')[-1].replace('fin', '')
                    try:
                        etime = datetime.datetime.strptime(end_time_str, '%Hh%M')
                    except:
                        continue

                    end_time = datetime.datetime(now.year, now.month, now.day, etime.hour, etime.minute)
                    end_time += datetime.timedelta(seconds = 60 * int(conf["warn_interval"]))
                    end_time_tz = tz.localize(end_time)

                    last_message_timestamp = None
                    last_modbot_tz = None

                    # Recherche dans les 5 derniers messages le dernier ne
                    # provenant pas de modbot
                    last_message = None
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

                    if time_since_modbot > datetime.timedelta(seconds = 60 * int(conf["delete_interval_after_warning"])):
                        #print("DELETE {0}".format(channel.name.encode('utf8')))
                        await channel.delete()  
                    elif time_delta > datetime.timedelta(seconds = 60 * int(conf["warn_interval"])) and (last_message.author.name != 'modbot' or last_modbot_tz is None):
                        #print("Warning {0}".format(channel.name.encode('utf8')))
                        await channel.send("Aucun message n'a été posté depuis plus de {0} minutes après la fin du raid, ce salon sera automatiquement archivé dans {1} minutes.\n**Si ce salon n'est pas destiné à être supprimé, veuillez contacter un modérateur/administrateur**".format(conf["warn_interval"], conf["delete_interval_after_warning"]))

            print("End modtask")
        except Exception as e:
            print(str(e))
        
        await asyncio.sleep(30)

async def cleantask():
    tz = pytz.timezone('Europe/Paris')

    while True:
        print("Cleaning")
        now = datetime.datetime.now()
        now_tz = tz.localize(now)

        lines = [line.strip() for line in open("cleanme", "r")]
        for server in client.guilds:
            for channel in list(server.channels):
                if str(channel.id) not in lines:
                    continue

                print("Clean {0}".format(channel.id))
                async for message in channel.history(limit = 100):
                    if message.author.name == 'modbot' and 'Roulette DDB' in message.content:
                        message_ts = get_local_time(message.created_at)
                        elapsed = now_tz - message_ts
                        if elapsed > datetime.timedelta(seconds = 600):
                            print("Delete : {0}".format(message.content.encode("utf8")))
                            await message.delete()
        print("Clean finished")
        await asyncio.sleep(60)

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
    return pickle.load(open(f, "rb"))

def save(f, data):
    pickle.dump(data, open(f, "wb"))

def get_local_time(dt, tz = None):
    if tz is None:
        tz = pytz.timezone('Europe/Paris')
    return pytz.utc.localize(dt, is_dst=None).astimezone(tz)

def read_config():
    global conf
    print("reading configuration")
    lines = [line.strip() for line in open("config", "r")]
    conf = {}
    for line in lines:
        key = line.split("=")[0]
        value = "=".join(line.split("=")[1:])
        conf[key] = value
    print("Done")
    print(conf)

        
if __name__ == '__main__':
    token = get_token()
    if token is not None:
        loop = asyncio.get_event_loop()
        read_config()
        loop.create_task(modtask())
        loop.create_task(cleantask())
        try:
            loop.run_until_complete(asyncio.gather(run(token)))
        except asyncio.CancelledError:
            pass
