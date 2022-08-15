import fortnitepy
import json
from termcolor import colored
import os


#import sanic
#import response,time
import logging,os,time
from flask import Flask
import aioconsole
from typing import Any, Union, Optional

from fortnitepy.ext import commands
import BenBotAsync
from threading import Thread
from functools import partial

import asyncio
# Third party imports.

import requests
#import functools

import crayons

loop = asyncio.get_event_loop()



with open('config.json') as f:
    try:
        data = json.load(f)
    except json.decoder.JSONDecodeError as e:
        print(colored("An error has occurred in config.json, join our discord server for help https://discord.gg/hmXa5cQCJH - ", "red"))
        print(colored(f'\n {e}', 'red'))
        exit(1)

    os.system('clear')
    print(colored('Thank you for using.', 'cyan'))

server = None
filename = 'device_auths.json'



def getNewSkins():
    r = requests.get('https://benbotfn.tk/api/v1/files/added')

    response = r.json()

    cids = []

    for cid in [item for item in response if item.split('/')[-1].upper().startswith('CID_')]:
        cids.append(cid.split('/')[-1].split('.')[0])
    
    return cids

def getNewEmotes():
    r = requests.get('https://benbotfn.tk/api/v1/files/added')

    response = r.json()

    eids = []

    for cid in [item for item in response if item.split('/')[-1].upper().startswith('EID_')]:
        eids.append(cid.split('/')[-1].split('.')[0])
    
    return eids

def get_device_auth_details():
    if os.path.isfile(filename):
        with open(filename, 'r') as fp:
            return json.load(fp)
    return {}

def store_device_auth_details(Email, details):
    existing = get_device_auth_details()
    existing[Email] = details


    with open(filename, 'w') as fp:
        json.dump(existing, fp)

def is_admin():
    async def predicate(ctx):
        return ctx.author.id in data['Control']['Give full access to']
    return commands.check(predicate)

async def keep_alive() -> None:
        url = f'https://{os.getenv("REPL_SLUG")}--{os.getenv("REPL_OWNER")}.repl.co'
        url2 = f'https://{os.getenv("REPL_SLUG")}.{os.getenv("REPL_OWNER")}.repl.co'
        requests.post('https://pinger.pirxcy.xyz/api/add', json={'url': url})
        requests.post('https://pinger.pirxcy.xyz/api/add', json={'url': url2})

async def get_authorization_code():
    while True:
        response = await aioconsole.ainput("Sign into https://rebrand.ly/authcode and sign in with "  + data['Account']['Email'] + " and enter the response: ")
        if "redirectUrl" in response:
            response = json.loads(response)
            if "?code" not in response["redirectUrl"]:
                print(colored("Invalid response.", "red"))
                continue
            code = response["redirectUrl"].split("?code=")[1]
            return code
        else:
            if "https://accounts.epicgames.com/fnauth" in response:
                if "?code" not in response:
                    print(colored("invalid response.", "red"))
                    continue
                code = response.split("?code=")[1]
                return code
            else:
                code = response
                return code
                os.system('clear')

device_auth_details = get_device_auth_details().get(data['Account']['Email'], {})
bot = commands.Bot(
    command_prefix=data['Account']['Prefix'],case_insensitive=True,
    auth=fortnitepy.AdvancedAuth(
        Email=data['Account']['Email'],
        prompt_authorization_code=True,
        delete_existing_device_auths=True,
        authorization_code=get_authorization_code,
        **device_auth_details
    ),
    status=data['Party']['Status'],
    platform=fortnitepy.Platform(data['Party']['Platform'])
)

@bot.event
async def event_device_auth_generate(details, Email):
    store_device_auth_details(data['Account']['Email'], details)

app=Flask("")

@app.route('/')
def main():
  return "Thank you for using silverbot!"

@bot.event
async def event_ready():
    loop.create_task(keep_alive())
    log = logging.getLogger('werkzeug')
    log.disabled = True
    Thread(target=app.run,args=("0.0.0.0",8080)).start()
    time.sleep(1)
    print(colored('Connecting to server...', 'cyan'))
    print(colored('Connected!', 'cyan'))
    print(colored('Starting SilverBot...', 'cyan'))
    print(colored('Started', 'cyan'))
    member = bot.party.me
    

    await member.edit_and_keep(
        partial(
            fortnitepy.ClientPartyMember.set_outfit,
            asset=data['Party']['Cosmetics']['Skin']
        ),
        partial(
            fortnitepy.ClientPartyMember.set_backpack,
            asset=data['Party']['Cosmetics']['Backpack']
        ),
        partial(
            fortnitepy.ClientPartyMember.set_pickaxe,
            asset=data['Party']['Cosmetics']['Pickaxe']
        ),
        partial(
            fortnitepy.ClientPartyMember.set_emote,
            asset=data['Party']['Cosmetics']['Emote']
        ),
        partial(
            fortnitepy.ClientPartyMember.set_banner,
            icon=data['Party']['Cosmetics']['Banner']['Banner Name'],
            color=data['Party']['Cosmetics']['Banner']['Banner Color'],
            season_level=data['Party']['Cosmetics']['Banner']['Season Level']
        ),
        partial(
            fortnitepy.ClientPartyMember.set_battlepass_info,
            has_purchased=True,
            level=data['Party']['Cosmetics']['Banner']['battle pass tier']
        )
    )

    bot.set_avatar(fortnitepy.Avatar(asset=' cid_757_athena_commando_f_wildcat', background_colors=['#ffffff', '#ee1064', '#ff0000']))



@bot.event
async def event_friend_add(Friend):
    if not data['Control']['Public Bot']:
        if not Friend.id in data['Control']['Give full access to']:
            return
    
    try:
        await Friend.invite()
    except:
        pass




    

@bot.event
async def event_party_invite(invite):
    if data['Party']['Join party on invitation'].lower() == 'true':
        try:
            await invite.accept()
            print(colored(f'Accepted party invite from {invite.sender.display_name}', 'blue'))
        except Exception:
            pass
    elif data['Party']['Join party on invitation'].lower() == 'false':
        if invite.sender.id in data['Control']['Give full access to']:
            await invite.accept()
            print(colored(f'Accepted party invite from {invite.sender.display_name}', 'blue'))
        else:
            print(colored(f'Did not accept party invite from {invite.sender.display_name}', 'red'))
def lenFriends():
    friends = bot.friends
    return len(friends)

def lenPartyMembers():
    members = bot.party.members
    return len(members)
    
@bot.event
async def event_party_member_promote(old_leader, new_leader):
    if new_leader.id == bot.user.id:
        await bot.party.send(f"Thanks {old_leader.display_name} for promoting me ♥!")
        await bot.party.me.set_emote("EID_TrueLove")


@bot.event
async def event_friend_request(request):
    if data['Friends']['Accept all friend requests'].lower() == 'true':
        try:
            await request.accept()
            print(colored(f'Accepted friend request from {request.display_name}' + f' ({lenFriends()})', 'blue'))
        
        except Exception:
            pass
    elif data['Friends']['Accept all friend requests'].lower() == 'false':
        if request.id in data['Control']['Give full access to']:
            try:
                await request.accept()
                print(colored('Accepted friend request from '  + f'{request.display_name}' + f' ({lenFriends()})', 'blue'))
            except Exception:
                pass
        else:
            print(colored(f'Never accepted friend request from {request.display_name}', 'red'))
@bot.event
async def event_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f'That is not a command. Try !help')
    elif isinstance(error, IndexError):
        pass
    elif isinstance(error, fortnitepy.HTTPException):
        pass
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("You don't have access to that command.")
    elif isinstance(error, TimeoutError):
        await ctx.send("You took too long to respond!")
    else:
        print(error)

@bot.command()
async def hello(ctx):
    await ctx.send('Hello!')

async def set_and_update_party_prop(schema_key: str, new_value: str):
    prop = {schema_key: bot.party.me.meta.set_prop(schema_key, new_value)}
    await bot.party.patch(updated=prop)

@bot.command()
@is_admin()
async def unhide(ctx, *, epic_username: Optional[str] = None) -> None:
    if epic_username is None:
        user = await bot.fetch_user(ctx.author.display_name)
        member = bot.party.get_member(user.id)
    else:
        user = await bot.fetch_user(epic_username)
        member = bot.party.get_member(user.id)

    if member is None:
        await ctx.send("Failed to find that user, are you sure they're in the party?")
    else:
        try:
            await member.promote()
            await ctx.send(f"unhid everyone in the party")
        except fortnitepy.errors.Forbidden:
            await ctx.send(f"i found unhide report in server.")
            print(crayons.red("Failed to unhide members as I don't have the required permissions."))


@bot.command()
async def emote(ctx, *, content = None):
    if content is None:
        await ctx.send(f'No emote was given, try: !emote (emote name)')
    elif content.lower() == 'floss':
        await bot.party.me.clear_emote()
        await bot.party.me.set_emote(asset='EID_Floss')
        await ctx.send(f'Emote set to: Floss')
    elif content.lower() == 'none':
        await bot.party.me.clear_emote()
        await ctx.send(f'Emote set to: None')
    elif content.upper().startswith('EID_'):
        await bot.party.me.clear_emote()
        await bot.party.me.set_emote(asset=content.upper())
        await ctx.send(f'Emote set to: {content}')
    else:
        try:
            cosmetic = await BenBotAsync.get_cosmetic(
                lang="en",
                searchLang="en",
                matchMethod="contains",
                name=content,
                backendType="AthenaDance"
            )
            await bot.party.me.clear_emote()
            await bot.party.me.set_emote(asset=cosmetic.id)
            await ctx.send(f'Emote set to: {cosmetic.name}')
        except BenBotAsync.exceptions.NotFound:
            await ctx.send(f'Could not find an emote named: {content}')


@bot.command()
@is_admin()
async def promote(ctx, *, epic_username: Optional[str] = None) -> None:
    if epic_username is None:
        user = await bot.fetch_user(ctx.author.display_name)
        member = bot.party.get_member(user.id)
    else:
        user = await bot.fetch_user(epic_username)
        member = bot.party.get_member(user.id)

    if member is None:
        await ctx.send("Failed to find that user, are you sure they're in the party?")
    else:
        try:
            await member.promote()
            await ctx.send(f"Promoted user: {member.display_name}.")
            print(colored(f"Promoted user: {member.display_name}", "blue"))
        except fortnitepy.errors.Forbidden:
            await ctx.send(f"Failed topromote {member.display_name}, as I'm not party leader.")
            print(crayons.red("Failed to promote member as I don't have the required permissions."))


@bot.command()
@is_admin()
async def hide(ctx, *, user = None):
    if bot.party.me.leader:
        if user != None:
            try:
                if user is None:
                    user = await bot.fetch_profile(ctx.message.author.id)
                    member = bot.party.members.get(user.id)
                else:
                    user = await bot.fetch_profile(user)
                    member = bot.party.members.get(user.id)

                raw_squad_assignments = bot.party.meta.get_prop('Default:RawSquadAssignments_j')["RawSquadAssignments"]

                for m in raw_squad_assignments:
                    if m['memberId'] == member.id:
                        raw_squad_assignments.remove(m)

                await set_and_update_party_prop(
                    'Default:RawSquadAssignments_j',
                    {
                        'RawSquadAssignments': raw_squad_assignments
                    }
                )

                await ctx.send(f"Hid {member.display_name}")
            except AttributeError:
                await ctx.send("I could not find that user.")
            except fortnitepy.HTTPException:
                await ctx.send("I am not party leader.")
        else:
            try:
                await set_and_update_party_prop(
                    'Default:RawSquadAssignments_j',
                    {
                        'RawSquadAssignments': [
                            {
                                'memberId': bot.user.id,
                                'absoluteMemberIdx': 1
                            }
                        ]
                    }
                )

                await ctx.send("Hid everyone in the party.")
            except fortnitepy.HTTPException:
                await ctx.send("I am not party leader.")
    else:
        await ctx.send("I need party leader to do this!")



@bot.command()
async def pickaxe(ctx, *, content = None):
    if content is None:
        await ctx.send(f'No pickaxe was given, try: !pickaxe (pickaxe name)')
    elif content.upper().startswith('Pickaxe_'):
        await bot.party.me.set_pickaxe(asset=content.upper())
        await ctx.send(f'Pickaxe set to: {content}')
    else:
        try:
            cosmetic = await BenBotAsync.get_cosmetic(
                lang="en",
                searchLang="en",
                matchMethod="contains",
                name=content,
                backendType="AthenaPickaxe"
            )
            await bot.party.me.set_pickaxe(asset=cosmetic.id)
            await ctx.send(f'Pickaxe set to: {cosmetic.name}')
        except BenBotAsync.exceptions.NotFound:
            await ctx.send(f'Could not find a pickaxe named: {content}')


@bot.command()
async def pet(ctx, *, content = None):
    if content is None:
        await ctx.send(f'No pet was given, try: !pet (pet name)')
    elif content.lower() == 'none':
        await bot.party.me.clear_pet()
        await ctx.send('Pet set to: None')
    else:
        try:
            cosmetic = await BenBotAsync.get_cosmetic(
                lang="en",
                searchLang="en",
                matchMethod="contains",
                name=content,
                backendType="AthenaPet"
            )
            await bot.party.me.set_pet(asset=cosmetic.id)
            await ctx.send(f'Pet set to: {cosmetic.name}')
        except BenBotAsync.exceptions.NotFound:
            await ctx.send(f'Could not find a pet named: {content}')


@bot.command()
async def pinkghoul(ctx):
    variants = bot.party.me.create_variants(material=3)

    await bot.party.me.set_outfit(
        asset='CID_029_Athena_Commando_F_Halloween',
        variants=variants
    )

    await ctx.send('Skin set to: Pink Ghoul Trooper')

@bot.command()
async def purpleskull(ctx):
    variants = bot.party.me.create_variants(clothing_color=1)

    await bot.party.me.set_outfit(
        asset='CID_030_Athena_Commando_M_Halloween',
        variants = variants
    )

    await ctx.send('Skin set to: Purple Skull Trooper')

@bot.command()
async def og(ctx):

   await bot.party.me.set.outfit('CID_039_Athena_Commando_F_Disco')

   await bot.party.me.set.emote('EID_Floss')

   await bot.party.me.set.backpack('BID_004_BlackKnight')

   await ctx.send('Set to an og combo')



@bot.command()
async def goldpeely(ctx):
    variants = bot.party.me.create_variants(progressive=4)

    await bot.party.me.set_outfit(
        asset='CID_701_Athena_Commando_M_BananaAgent',
        variants=variants,
        enlightenment=(2, 350)
    )

    await ctx.send('Skin set to: Golden Peely')


@bot.command()
async def hatlessrecon(ctx):
    variants = bot.party.me.create_variants(parts=2)

    await bot.party.me.set_outfit(
        asset='CID_022_Athena_Commando_F',
        variants=variants
    )

    await ctx.send('Skin set to: Hatless Recon Expert')



@bot.command()
async def hologram(ctx):
    await bot.party.me.set_outfit(
        asset='CID_VIP_Athena_Commando_M_GalileoGondola_SG'
    )
    
    await ctx.send("Skin set to: Hologram")




@bot.command()
async def new(ctx, content = None):
    newSkins = getNewSkins()
    newEmotes = getNewEmotes()

    previous_skin = bot.party.me.outfit

    if content is None:
        await ctx.send(f'There are {len(newSkins) + len(newEmotes)} new skins + emotes')

        for cosmetic in newSkins + newEmotes:
            if cosmetic.startswith('CID_'):
                await bot.party.me.set_outfit(asset=cosmetic)
                await asyncio.sleep(4)
            elif cosmetic.startswith('EID_'):
                await bot.party.me.clear_emote()
                await bot.party.me.set_emote(asset=cosmetic)
                await asyncio.sleep(4)

    elif 'skin' in content.lower():
        await ctx.send(f'There are {len(newSkins)} new skins')

        for skin in newSkins:
            await bot.party.me.set_outfit(asset=skin)
            await asyncio.sleep(4)

    elif 'emote' in content.lower():
        await ctx.send(f'There are {len(newEmotes)} new emotes')

        for emote in newEmotes:
            await bot.party.me.clear_emote()
            await bot.party.me.set_emote(asset=emote)
            await asyncio.sleep(4)

    await bot.party.me.clear_emote()
    
    await ctx.send('Done!')

    await asyncio.sleep(1.5)

    await bot.party.me.set_outfit(asset=previous_skin)

    if (content is not None) and ('skin' or 'emote' not in content.lower()):
        ctx.send(f"Not a valid option. Try: !new (skins, emotes)")



@bot.command()
async def ready(ctx):
    await bot.party.me.set_ready(fortnitepy.ReadyState.READY)
    await ctx.send('Set ready state to Ready!')



@bot.command()
async def unready(ctx):
    await bot.party.me.set_ready(fortnitepy.ReadyState.NOT_READY)
    await ctx.send('Set ready state to Unready!')



@bot.command()
async def skin(ctx, *, content = None):
    if content is None:
        await ctx.send(f'No skin was given, try: !skin (skin name)')
    elif content.upper().startswith('CID_'):
        await bot.party.me.set_outfit(asset=content.upper())
        await ctx.send(f'Skin set to: {content}')
    else:
        try:
            cosmetic = await BenBotAsync.get_cosmetic(
                lang="en",
                searchLang="en",
                name=content,
                backendType="AthenaCharacter"
            )
            await bot.party.me.set_outfit(asset=cosmetic.id)
            await ctx.send(f'Skin set to: {cosmetic.name}')
        except BenBotAsync.exceptions.NotFound:
            await ctx.send(f'Could not find a skin named: {content}')


@bot.command()
async def sitin(ctx):
    await bot.party.me.set_ready(fortnitepy.ReadyState.NOT_READY)
    await ctx.send('Sitting in')


@bot.command()
async def sitout(ctx):
    await bot.party.me.set_ready(fortnitepy.ReadyState.SITTING_OUT)
    await ctx.send('Sitting out')


@bot.command()
async def tier(ctx, tier = None):
    if tier is None:
        await ctx.send(f'No tier was given. Try: !tier (tier number)') 
    else:
        await bot.party.me.set_battlepass_info(
            has_purchased=True,
            level=tier
        )

        await ctx.send(f'Battle Pass tier set to: {tier}')


@bot.command()
async def level(ctx, level = None):
    if level is None:
        await ctx.send(f'No level was given. Try: !level (number)')
    else:
        await bot.party.me.set_banner(season_level=level)
        await ctx.send(f'Level set to: {level}')




copied_player = ""



@bot.command()
async def stop(ctx):
    global copied_player
    if copied_player != "":
        copied_player = ""
        await ctx.send(f'Stopped copying all users.')
        return
    else:
        try:
            await bot.party.me.clear_emote()
        except RuntimeWarning:
            pass



bot.run() 