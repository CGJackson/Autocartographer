import wave

import discord
from discord.ext import voice_recv


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

class RecordingManager():
    def __init__(self):
        self.live_files = {}

    def __enter__(self):
        return self

    def __exit__(self):
        for file in self.live_files.values():
            file.close()

    def __getitem__(self, key):
        return self.live_files[key]
    
    def open(self,filename,voice_client):
        f = wave.open(filename,"wb")
        if voice_client in self.live_files:
            raise RuntimeError(f"There is already an open recording for client {voice_client}")
        self.live_files[voice_client] = f
        return f

    def close(self,voice_client):
        self.live_files.pop(voice_client).close()


class VoiceChannelDirectory:
    """
    Manages a dictionary of the currently active voice clients in different channels.

    channels, and corresponding clients, are added when they connect and removed when
    they disconnect
    """
    def __init__(self):
        self.voice_clients = {}

    def __contains__(self, item):
        item in self.voice_clients

    def __getitem__(self, key):
        return self.voice_clients[key]

    def __iter__(self):
        return iter(self.voice_clients)

    def __next__(self):
        return next(self.voice_clients)

    async def connect_to_channel(self,channel):
        new_voice_client = await channel.connect(self_mute=True,cls=voice_recv.VoiceRecvClient)
        if channel in self:
            await self.voice_clients.pop(channel).disconnect()
        self.voice_clients[channel] = new_voice_client

    async def disconnect_from_channel(self,channel):
        client = self.voice_clients.pop(channel)
        client.stop()
        await client.disconnect()

    def get_client_in_channel_with_user(self,user : discord.User):
        for channel,client in self.voice_clients.items():
            if user in channel.members:
                return client
            
        raise self.NoChannelContainingUser(f"Could not find a connected voice channel containing user {user}")

    class NoChannelContainingUser(KeyError):
        def __init__(self,message):
            self.message = message
            super().__init__(self.message)


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
    wav = wave.open()
    print("record not implimented")


def end_recording_and_generate_map(listener:voice_recv.VoiceRecvClient):
    if not listener.is_listening():
        raise RuntimeError("listener is not currently listening")

    listener.stop_listening()
    wav.close()
    # TODO - Get audio file (from where?)
    # TODO - pass file to generative model

async def stop_record(message : discord.Message):
    """
    Has the bot stop recording from a channel and
    generate a map
    """
    listening_client = active_voice_channels.get_client_in_channel_with_user(message.user)
    end_recording_and_generate_map(listening_client)


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
                await active_voice_channels.disconnect_from_channel(channel)
                return
    content = strip_mention(message.content)

    for channel in active_voice_channels:
        if content.startswith("leave " + channel.name):
            await active_voice_channels.disconnect_from_channel(channel)
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


with RecordingManager() as recordings:
    client.run(token)