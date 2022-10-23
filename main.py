#!/usr/bin/env python3
import json
from asyncio import create_task, Task, wait, FIRST_COMPLETED

import nextcord
from nextcord.ext.commands import Bot, Context, command, has_permissions
from nextcord import SlashOption, User, Member
from nextcord.abc import GuildChannel, Messageable
from nextcord.activity import Activity, ActivityType
from nextcord.interactions import Interaction
from nextcord.message import Message
from nextcord.embeds import Embed
from nextcord.colour import Color
from nextcord.ext.commands.errors import MissingPermissions
from nextcord.errors import Forbidden, HTTPException


OIS = Bot(
    command_prefix=("OIS)"),
    strip_after_prefix=True,
    description="OIS Bot for the OIS Discord Server",
    owner_id=797844636281995274,
    activity=Activity(type=ActivityType.competing, name="Olimpiadi Informatiche a Squadre"),
    status=nextcord.Status.online,
    intents=nextcord.Intents.all(),
)


OIS.run(open("token.txt", "r").read())