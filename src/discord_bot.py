import discord
from discord.ext import voice_recv


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

class VoiceChannelDirectory:
    """
    Manages a dictionary of the currently active voice clients in different channels.

    channels, and corresponding clients, are added when they connect and removed when
    they disconnect
    """
    def __init__(self):
        self.voiceclients = {}

    def __contains__(self, item):
        item in self.voiceclients

    def __getitem__(self, key):
        return self.voiceclients[key]

    def __iter__(self):
        return iter(self.voiceclients)

    def __next__(self):
        return next(self.voiceclients)

    async def connect_to_channel(self,channel):
        new_voice_client = await channel.connect(self_mute=True,cls=voice_recv.VoiceRecvClient)
        if channel in self:
            await self.voiceclients.pop(channel).disconect()
        self.voiceclients[channel] = new_voice_client

    async def disconect_from_channel(self,channel):
        await self.voiceclients.pop(channel).disconnect()



active_voice_channels = VoiceChannelDirectory()

def strip_mention(msg : str):
    return "".join(msg.split(client.user.mention)).strip()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

async def record(message : discord.Message):
    """
    Has the bot start recording a voice channel containing
    the author of the message, in order to generate a map.
    """
    print("record not implimented")

async def stop_record(message : discord.Message):
    """
    Has the bot stop recording from a channel and
    generate a map
    """
    # Should this require the user giving the command to be the user that started recording?
    print("stop_record not implimented")


async def join(message : discord.Message):
    """
    Adds the bot to a voice channel.
    
    Either uses a voice channel mentioned in the message or, 
    if there isn't one, a voice mentioned after the join
    command
    """
    if message.channel_mentions:
        for channel in message.channel_mentions:
            if isinstance(channel,discord.VoiceChannel):
                await active_voice_channels.connect_to_channel(channel)
                return
    content = strip_mention(message.content)

    for channel in message.guild.voice_channels:
        if content.startswith("join " + channel.name):
            await active_voice_channels.connect_to_channel(channel)
            return

    await message.channel.send("I am sorry. I cannot determine which voice channel you want me to join")

async def leave(message : discord.Message):
    """
    Removes bot from a voice channel

    Either uses a voice channel mentioned in the message or, 
    if there isn't one, a voice mentioned after the leave
    command
    """
    if message.channel_mentions:
        for channel in message.channel_mentions:
            if isinstance(channel,discord.VoiceChannel) and channel in active_voice_channels:
                await active_voice_channels.disconect_from_channel(channel)
                return
    content = strip_mention(message.content)

    for channel in active_voice_channels:
        if content.startswith("leave " + channel.name):
            await active_voice_channels.disconect_from_channel(channel)
            return

    await message.channel.send("I am sorry. I cannot determine which voice channel you want me to leave.\n It may be that I am not currently connected to the channel.")


commands = {
    "listen" : record,
    "stop" : stop_record,
    "join" : join,
    "leave" : leave
}

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if not client.user.mentioned_in(message):
        return

    content = strip_mention(message.content)

    print(content)

    for (command,action) in commands.items():
        if content.startswith(command):
            await action(message)
            break


with open("secrets/discord_token.txt","r") as token_file:
    token = token_file.read()


client.run(token)