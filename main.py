#!/usr/bin/env python3
import json
from asyncio import create_task, Task, wait, FIRST_COMPLETED
from typing import Optional, Tuple, List

import nextcord
from nextcord.ext.commands import Bot, Context, command, has_permissions
from nextcord.ext import application_checks
from nextcord import SlashOption, User, Member, Role, application_command, Embed, Attachment
from nextcord.abc import GuildChannel, Messageable
from nextcord.activity import Activity, ActivityType
from nextcord.interactions import Interaction
from nextcord.message import Message
from nextcord.channel import TextChannel
from nextcord.threads import Thread
from nextcord.embeds import Embed
from nextcord.colour import Color
from nextcord.utils import get
from nextcord.ext.commands.errors import MissingPermissions
from nextcord.errors import Forbidden, HTTPException

CATEGORY_TEAMS = 1033500272372228277

OIS = Bot(
    command_prefix=("OIS)"),
    strip_after_prefix=True,
    description="OIS Bot for the OIS Discord Server",
    owner_id=797844636281995274,
    activity=Activity(type=ActivityType.competing, name="Olimpiadi Informatiche a Squadre"),
    status=nextcord.Status.online,
    intents=nextcord.Intents.all(),
)


@OIS.event
async def on_ready() -> None:
    print(f"{OIS.user.name}#{OIS.user.discriminator} is online")


@OIS.slash_command(name="delete", description="Delete the last N messages")
async def delete(
        interaction: Interaction,
        number: int = SlashOption(
            name="number",
            description="The number of messages to delete",
            required=True,
        )) -> None:
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You must be the owner of the server to use this command",
                                                ephemeral=True)
        return
    await interaction.channel.purge(limit=number + 1)
    await interaction.response.send_message(f"Deleted {number} messages", ephemeral=True)


@OIS.slash_command(name="create_team", description="Create your team")
async def create_team(
        interaction: Interaction,
        team_name: str = SlashOption(
            name="team_name",
            description="The name of your team",
            required=True,
        ),
        team_city: str = SlashOption(
            name="team_city",
            description="The city of your team",
            required=True,
        )) -> None:
    team_leader = interaction.user

    embed = Embed(title="Team Creation", description="Send :white_check_mark: if you are sure of the following.",
                  color=Color.green())
    embed.add_field(name="Team Name", value=team_name, inline=False)
    embed.add_field(name="Team City", value=team_city, inline=False)
    embed.add_field(name="Team Leader", value=team_leader.mention, inline=False)
    embed.set_footer(text="Send :white_check_mark: quickly to confirm the creation of the team")
    await interaction.response.send_message(embed=embed, ephemeral=False)

    if (role := get(interaction.guild.roles, name=team_name)) is not None:
        await interaction.channel.send("A team with this name already exists")
    else:
        role: Role = await interaction.guild.create_role(
            name=team_name,
            color=Color.random(),
            hoist=True
        )
        await interaction.channel.send("Role created successfully")

    # Assign the role to the team leader
    await team_leader.add_roles(role)
    await interaction.channel.send("Role assigned successfully")

    # Create channel (https://stackoverflow.com/questions/68235517/creating-a-channel-in-specific-category-the-category-id-is-should-be-variable)
    category = get(interaction.guild.categories, id=CATEGORY_TEAMS)
    channel: GuildChannel = await interaction.guild.create_text_channel(
        name=team_name,
        category=category,
        topic=f"{team_name} - {team_city}",
        reason=f"Team {team_name} creation"
    )
    await interaction.channel.send("Channel created successfully")

    # Manage permissions of the channel for @everyone
    channel_permissions = channel.permissions_for(interaction.guild.default_role)
    channel_permissions.send_messages = False
    channel_permissions.add_reactions = True

    # Manage permissions of the channel for the team members
    channel_permissions = channel.permissions_for(role)
    channel_permissions = nextcord.Permissions.all()


@OIS.slash_command(name="embed", description="Embed message given its url")
async def embed(interaction: Interaction, message_link: str) -> None:
    message_metadata = message_link.split("/")
    message_channel = interaction.guild.get_channel(int(message_metadata[5]))
    message = await message_channel.fetch_message(int(message_metadata[6]))
    embedded_response = make_embedded_message(message)
    if len(embedded_response) == 1:
        await interaction.response.send_message(embed=embedded_response[0])
    else:
        await interaction.response.send_message(embeds=embedded_response)


@OIS.slash_command(name="hall_of_fame", description="Create the Hall of Fame for a channel from its pinned messages")
async def hall_of_fame(interaction: Interaction, source_channel: TextChannel) -> None:
    target_channel: Thread = await source_channel.create_thread(
        name=f"Hall of Fame",
        reason="Hall of Fame",
        type=nextcord.ChannelType.public_thread
    )
    await interaction.channel.send(f"Creating Hall of Fame for {source_channel.mention} in {target_channel.mention}...")
    await target_channel.send(f"**Hall of Fame for {source_channel.mention}!**")
    pinned = await source_channel.pins()
    for message in reversed(pinned):
        try:
            embedded_response = make_embedded_message(message)
        except HTTPException:
            await target_channel.send("<Error-processing-message>")
        if len(embedded_response) == 1:
            try:
                await target_channel.send(embed=embedded_response[0])
            except HTTPException:
                await target_channel.send("<Error-processing-message>")
        else:
            await target_channel.send(embeds=embedded_response)
    await interaction.channel.send(f"Hall of Fame for {source_channel.mention} created in {target_channel.mention}!")


@OIS.slash_command(name="unpin_all", description="Unpin all pinned messages of a channel")
@application_checks.has_permissions(administrator=True)
async def unpin_all(interaction: Interaction,
                    target_channel: Optional[TextChannel] = SlashOption(required=False)) -> None:
    target_channel = target_channel or interaction.channel
    pinned = await target_channel.pins()
    for pin in pinned:
        await pin.unpin()
    await interaction.response.send_message(f"Unpinned all pins in {target_channel.mention}")


def make_embedded_message(message: Message) -> list[Embed]:
    embedded_response = Embed(
        title=f"Message from {message.channel.mention}",
        url=message.jump_url,
        description=message.content + f"\n\n[**Jump to message**]({message.jump_url})"
    )
    embedded_response.set_author(name=message.author, icon_url=message.author.display_avatar)
    embedded_response.set_footer(text=f"Message ID: {message.id}")
    embedded_response = [embedded_response]
    if len(message.attachments) == 1:
        embedded_response[0].set_image(url=message.attachments)
    elif len(message.attachments) > 1:
        for attachment in message.attachments:
            if attachment.content_type.startswith("video"):
                continue
            new_embed = Embed(url=message.jump_url)  # We need all embeds to have the same url for this to work
            new_embed.set_image(url=attachment)
            embedded_response.append(new_embed)
    return embedded_response


OIS.run(open("token.txt").read().strip())