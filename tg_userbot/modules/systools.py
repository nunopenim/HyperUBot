# My stuff
from tg_userbot import VERSION, PROJECT, BOTLOG, BOTLOG_CHATID, HELP_DICT
from tg_userbot.include.watcher import watcher
from tg_userbot.include.language_processor import StatusText as msgRep, HelpDesignations as helpRep
from tg_userbot.include.aux_funcs import pinger, getGitReview
import tg_userbot.include.cas_api as cas
import tg_userbot.include.git_api as git

# Telethon stuff
from telethon import version

# Misc Imports
from platform import python_version, uname
from datetime import datetime, timedelta
import time
import psutil
from subprocess import check_output

# Module Global Variables
USER = uname().node # Maybe add a username in future
STARTTIME = datetime.now()

@watcher(outgoing=True, pattern=r"^\.status$")
async def statuschecker(stat):
    global STARTTIME
    uptimebot = datetime.now() - STARTTIME
    uptime_hours = uptimebot.seconds // 3600  # (60 * 60)
    uptime_mins = uptimebot.seconds // 60 % 60
    uptime_secs = uptimebot.seconds % 60
    uptimeSTR = f"{uptimebot.days} " + msgRep.DAYS + f", {uptime_hours:02}:{uptime_mins:02}:{uptime_secs:02}"
    uptimemachine = time.time() - psutil.boot_time()
    uptime_machine_converted = timedelta(seconds=uptimemachine)
    uptime_machine_array = str(uptime_machine_converted).split(" days, ")
    uptime_machine_days = uptime_machine_array[0]
    uptime_machine_time = uptime_machine_array[1].split(":")
    uptime_machine_hours = uptime_machine_time[0]
    if int(uptime_machine_hours) < 10:
        uptime_machine_hours = "0" + uptime_machine_hours
    uptime_machine_minutes = uptime_machine_time[1]
    uptime_machine_seconds = uptime_machine_time[2].split(".")[0]
    uptimeMacSTR = f"{uptime_machine_days} " + msgRep.DAYS + f", {uptime_machine_hours}:{uptime_machine_minutes}:{uptime_machine_seconds}"
    commit = await getGitReview()
    rtt = pinger("1.1.1.1") #cloudfare's
    reply = msgRep.SYSTEM_STATUS + "`" + msgRep.ONLINE + "`" + "\n\n"
    reply += msgRep.UBOT + "`" + PROJECT + "`" + "\n"
    reply += msgRep.VER_TEXT + "`" + VERSION + "`" + "\n"
    reply += msgRep.COMMIT_NUM + "`" + commit + "`" + "\n"
    if rtt:
        reply += msgRep.RTT + "`" + str(rtt) + "`" + "\n"
    else:
        reply += msgRep.RTT + "`" + msgRep.ERROR + "`" + "\n"
    reply += msgRep.BOT_UPTIMETXT + uptimeSTR + "\n"
    reply += msgRep.MAC_UPTIMETXT + uptimeMacSTR + "\n"
    reply += "\n"
    reply += msgRep.TELETON_VER + "`" + str(version.__version__) + "`" + "\n"
    reply += msgRep.PYTHON_VER + "`" + str(python_version()) + "`" + "\n"
    reply += msgRep.GITAPI_VER + "`" + git.vercheck() + "`" + "\n"
    reply += msgRep.CASAPI_VER + "`" + cas.vercheck() + "`" + "\n"
    await stat.edit(reply)
    return

@watcher(outgoing=True, pattern=r"^\.shutdown$")
async def shutdown(power_off):
    await power_off.edit(msgRep.SHUTDOWN)
    if BOTLOG:
        await power_off.client.send_message(BOTLOG_CHATID, msgRep.SHUTDOWN_LOG)
    await power_off.client.disconnect()

@watcher(outgoing=True, pattern=r"^\.sysd$")
async def neofetch(sysd):
    try:
        result = check_output("neofetch --stdout", shell=True).decode()
        await sysd.edit("`" + result + "`")
    except FileNotFoundError:
        await sysd.edit("`Install neofetch first !!`")
    return

HELP_DICT.update({"systools":helpRep.SYSTOOLS_HELP})