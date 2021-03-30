# Copyright 2020 nunopenim @github
# Copyright 2020 prototype74 @github
# Copyright 2021 githubcatw @github
#
# Licensed under the PEL (Penim Enterprises License), v1.0
#
# You may not use this file or any of the content within it, unless in
# compliance with the PE License

from userbot.include.language_processor import GeneralMessages as msgsLang
from userbot.sysutils.configuration import getConfig
from telethon.tl.types import PeerUser, PeerChannel, User
from telethon.tl.functions.users import GetFullUserRequest
from logging import getLogger
import os
from subprocess import check_output, CalledProcessError
from asyncio import create_subprocess_exec as asyncr
from asyncio.subprocess import PIPE as asyncPIPE
from shutil import which

log = getLogger(__name__)

async def fetch_user(event=None, full_user=False, get_chat=False, org_author=False):
    """
    Fetch the user (and chat) information from event

    Args:
        event (Event): any event e.g. NewMessage
        full_user (bool): fetch FullUser object instead
        get_chat (bool): fetches Chat/Channel object to. This changes the return to a tuple
        org_author (bool): focus to original author of a replied message

    Example:
        @client.on(NewMessage(pattern="^\.example$", outgoing=True))
        async def example_handler(event):
            user, chat = fetch_user(event, full_user=True, get_chat=True)
            await event.edit(f"hi {user.first_name}, welcome in {chat.title}!")

    Returns:
        - User object (default) or
        - FullUser object if full_user is set to True or
        - A tuple ((User, Chat/Channel) or (FullUser, Chat/Channel)) if get_chat is set to True
    """
    if not event:
        return (None, None) if get_chat else None
    if event.reply_to_msg_id:
        message = await event.get_reply_message()
        if message.fwd_from and isinstance(message.fwd_from.from_id, PeerChannel):
            # focus to forwarder if forwarded message is from a channel
            if message.from_id and isinstance(message.from_id, PeerUser):
                user = message.from_id.user_id
            else:
                await event.edit(msgsLang.CHAT_NOT_USER)
                return (None, None) if get_chat else None
        # focus to original author and skip forwarder
        elif message.fwd_from and message.fwd_from.from_id and org_author:
            user = message.fwd_from.from_id.user_id
        else:
            user = message.from_id.user_id if message.from_id else message.sender_id
        chat_obj = await event.get_chat() if get_chat else None  # current chat
        if not user:
            await event.edit(msgsLang.PERSON_ANONYMOUS)
            return (None, None) if get_chat else None
            return
    else:
        try:
            # args_from_event becomes a list. it takes maximum of 2 arguments,
            # more than 2 will be appended to second element.
            args_from_event = event.pattern_match.group(1).split(" ", 1)
            if len(args_from_event) == 2:
                user, chat = args_from_event
                try:
                    chat = int(chat)  # chat ID given
                except:
                    pass

                try:
                    chat_obj = await event.client.get_entity(chat) if get_chat else None
                    if type(chat_obj) is User:  # entity is not a chat or channel object
                        chat_obj = None
                except Exception as e:
                    log.warning(e)
                    chat_obj = None
            else:
                user = args_from_event[0]
                chat_obj = await event.get_chat() if get_chat else None
        except Exception as e:
            log.warning(e)
            await event.edit(msgsLang.FAIL_FETCH_USER)
            return (None, None) if get_chat else None

        try:
            user = int(user)
        except:
            pass

        if not user:
            oh_look_its_me = await event.client.get_me()
            user = oh_look_its_me.id

    try:
        if full_user:
            user_obj = await event.client(GetFullUserRequest(user))
        else:
            user_obj = await event.client.get_entity(user)
            if not type(user_obj) is User:
               await event.edit(msgsLang.ENTITY_NOT_USER)
               user_obj = None
        return (user_obj, chat_obj) if get_chat else user_obj
    except Exception as e:
        log.warning(e)
        await event.edit(msgsLang.CANT_FETCH_REQ_AS_USER.format(user))
    return (None, chat_obj) if get_chat else None

async def event_log(event, event_name: str, user_name=None, user_id=None, username=None,
                    chat_title=None, chat_link=None, chat_id=None, custom_text=None):
    """
    Log any event by sending a message to the targeted chat

    Args:
        event (Event): any event e.g. NewMessage
        event_name (str): name of event (not Telethon event) e.g. ban
        user_name: name of user. Default to None
        user_id: ID from user. Default to None
        username: username from user. Default to None
        chat_title: Title of the specific chat. Default to None
        chat_link: link of the specific chat e.g. @example. Default to None
        chat_id: link of the specific chat e.g. -100123456789. Default to None
        custom_text: any custom text e.g. a note to the event. Default to None

    Example:
        @client.on(NewMessage(pattern="^\.example$", outgoing=True))
        async def example_handler(event):
            user = fetch_user(event)
            await event_log(event, "BAN", user_name=user.first_name, chat_id=event.chat_id)
    """
    log_chat_id = getConfig("LOGGING_CHATID")

    if not log_chat_id:
        log.warning(f"EVENT_LOG logging event '{event_name}' failed: LOGGING_CHATID is not set")
        return

    text = f"**{event_name}**\n"
    if user_name and user_id and not username:
        text += f"{msgsLang.LOG_USER}: [{user_name}](tg://user?id={user_id})\n"
    elif user_name:
        text += f"{msgsLang.LOG_USER}: {user_name}\n"
    if username:
        text += f"{msgsLang.LOG_USERNAME}: @{username}\n"
    if user_id:
        text += f"{msgsLang.LOG_USER_ID}: `{user_id}`\n"
    if chat_title:
        text += f"{msgsLang.LOG_CHAT_TITLE}: {chat_title}\n"
    if chat_link:
        text += f"{msgsLang.LOG_CHAT_LINK}: @{chat_link}\n"
    if chat_id:
        text += f"{msgsLang.LOG_CHAT_ID}: `{chat_id}`\n"
    if custom_text:
        text += f"{custom_text}"

    try:
        await event.client.send_message(log_chat_id, text)
    except Exception as e:
        log.warning(f"EVENT_LOG ({event_name}): {e}")
    return

def isRemoteCMD(event, chat_id: int) -> bool:
    """
    Check if chat id from event matches chat_id. By this we can ensure if
    the command is remotely used.

    Args:
        event (Event): any event e.g. NewMessage
        chat_id (int): ID from targeted chat

    Example:
        @client.on(NewMessage(pattern="^\.example$", outgoing=True))
        async def example_handler(event):
            user, chat = fetch_user(event, get_chat=True)
            isRemote = isRemoteCMD(event.chat_id, chat.id)
            if isRemote:
                await event.edit("Remote!")
            else:
                await event.edit("Not remote")

    Returns:
        A boolean
    """
    try:
        chat_from_event = int(str(event.chat_id)[3:]) if str(event.chat_id).startswith("-100") else event.chat_id
        return True if not chat_id == chat_from_event else False
    except Exception as e:
        log.error(e)
    return False

def module_info(name: str, version: str) -> dict:
    """
    Put name and version about a module to a new dictionary

    Args:
        name (str): name of module
        version (str): version of module

    Example:
        module_info("Example", "1.0")

    Returns:
        A dictionary with 2 keys
    """
    return {"name": name, "version": version}

def dependency(name: str, source: str) -> dict:
    """
    Put name and source of a dependency to a new dictionary

    Args:
        name (str): name of module
        source (str): should be either "pip" or "repo"

    Example:
        dependency("Pillow", "pip")
        dependency("example", "repo")

    Returns:
        A dictionary with 2 keys
    """
    return {"name": name, "source": source}

def shell_runner(commands: list):
    """
    Execute shell commands from given list with strings

    Args:
        commands (list): list of a shell command (with options)

    Example:
        output = shell_runner(["ls", "-l"])
        print(output)

    Returns:
        The output as a string
    """
    full_cmd = ""
    for cmd in commands:
        full_cmd += cmd + " "
    try:
        return check_output(full_cmd, shell=True).decode()
    except CalledProcessError:
        return None

# Systools/Webtools
def pinger(address):
    """
    Ping an IP or DNS server from given address

    Args:
        address (str): IP/DNS address e.g. "8.8.8.8"

    Example:
        ping = pinger("8.8.8.8")

    Returns:
        Ping result as a string
    """
    if os.name == "nt":
        output = check_output("ping -n 1 " + address + " | findstr time*", shell=True).decode()
        outS = output.splitlines()
        out = outS[0]
    else:
        out = check_output("ping -c 1 " + address + " | grep time=", shell=True).decode()
    splitOut = out.split(' ')
    under = False
    stringtocut = ""
    for line in splitOut:
        if (line.startswith('time=') or line.startswith('time<')):
            stringtocut = line
            break
    newstra = stringtocut.split('=')
    if len(newstra) == 1:
        under = True
        newstra = stringtocut.split('<')
    newstr = ""
    if os.name == 'nt':
        newstr = newstra[1].split('ms')
    else:
        newstr = newstra[1].split(' ')  # redundant split, but to try and not break windows ping
    ping_time = float(newstr[0])
    if os.name == 'nt' and under:
        return "<" + str(ping_time) + " ms"
    else:
        return str(ping_time) + " ms"

async def getGitReview():
    """
    Get the last commit ID from .git inside root directory

    Example:
        commit = getGitReview()

    Returns:
        Commit ID as stiring
    """
    commit = msgsLang.ERROR
    if which("git") is not None:
        ver = await asyncr("git", "describe", "--all", "--long", stdout=asyncPIPE, stderr=asyncPIPE)
        stdout, stderr = await ver.communicate()
        verout = str(stdout.decode().strip()) + str(stderr.decode().strip())
        verdiv = verout.split("-")
        commit = verdiv[2]
    return commit

# Package Manager
def sizeStrMaker(size: float, value: int = 0):
    """
    Convert given byte size recursively to a readable size

    Args:
        size (float): size in bytes
        value (int): just keep it 0

    Example:
        readable_size = sizeStrMaker(2048)
        print(readable_size)

    Returns:
        Converted size as string
    """
    if size < 1024:
        size_units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
        return str(round(size, 2)) + " " + size_units[value]
    else:
        size /= 1024
        value += 1
        return sizeStrMaker(size, value)
