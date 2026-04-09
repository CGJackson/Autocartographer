import wave
import os

import discord
from discord.ext import voice_recv



class RecordingManager():
    def __init__(self):
        self.live_files = {}
        self.created_files = []

    def __enter__(self):
        return self

    def __exit__(self):
        # close any files that remain open
        for file in self.live_files.values():
            file.close()
        self.live_files = {}

        # delete temporary files 
        for file_list in self.created_files.values():
            for file in file_list:
                os.remove(file)
        self.created_files = {}


    def __getitem__(self, key):
        return self.live_files[key]
    
    def open(self,filename,voice_client):

        if voice_client in self.live_files:
            raise RuntimeError(f"There is already an open recording for client {voice_client}")

        f = wave.open(filename,"wb")
        self.created_files.setdefault(voice_client,default=[]).append(filename)

        self.live_files[voice_client] = f
        return f

    def close(self,voice_client):
        self.live_files.pop(voice_client).close()

    def get_client_archive(self,voice_client):
        return self.created_files[voice_client]

    def get_last_file_for_client(self,voice_client):
        return self.get_channel_archive(voice_client)[-1]


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

def strip_mention(msg : str):
    return "".join(msg.split(client.user.mention)).strip()

class AutocartographerBot():
    def __init__(self):
        self.active_voice_channels = VoiceChannelDirectory()
        self.recordings = None

        self.intents = discord.Intents.default()
        self.intents.message_content = True

        self.client = discord.Client(intents=self.intents)
        self.commands = {
            "listen" : self.record,
            "stop" : self.stop_record,
            "join" : self.join,
            "leave" : self.leave
        }


    @client.event
    async def on_ready(self):
        print(f'We have logged in as {self.client.user}')

    async def record(self,message : discord.Message):
        """
        Has the bot start recording a voice channel containing
        the author of the message, in order to generate a map.
        """
        wav = wave.open()
        print("record not implemented")


    def end_recording_and_generate_map(self,listener:voice_recv.VoiceRecvClient):
        if not listener.is_listening():
            raise RuntimeError("listener is not currently listening")

        listener.stop_listening()
        self.recordings.close(listener)

        recording_file_name = self.recordings.get_last_file_for_client(listener)

        with wave.open(recording_file_name,"rb") as recording:
            pass
            # TODO - pass file to generative model

    async def stop_record(self,message : discord.Message):
        """
        Has the bot stop recording from a channel and
        generate a map
        """
        listening_client = self.active_voice_channels.get_client_in_channel_with_user(message.user)
        self.end_recording_and_generate_map(listening_client)


    async def join(self,message : discord.Message):
        """
        Adds the bot to a voice channel.
        
        Either uses a voice channel mentioned in the message or, 
        if there isn't one, a voice mentioned after the join
        command
        """
        if message.channel_mentions:
            for channel in message.channel_mentions:
                if isinstance(channel,discord.VoiceChannel):
                    await self.active_voice_channels.connect_to_channel(channel)
                    return
        content = strip_mention(message.content)

        for channel in message.guild.voice_channels:
            if content.startswith("join " + channel.name):
                await self.active_voice_channels.connect_to_channel(channel)
                return

        await message.channel.send("I am sorry. I cannot determine which voice channel you want me to join")

    async def leave(self,message : discord.Message):
        """
        Removes bot from a voice channel

        Either uses a voice channel mentioned in the message or, 
        if there isn't one, a voice mentioned after the leave
        command
        """
        if message.channel_mentions:
            for channel in message.channel_mentions:
                if isinstance(channel,discord.VoiceChannel) and channel in self.active_voice_channels:
                    await self.active_voice_channels.disconnect_from_channel(channel)
                    return
        content = strip_mention(message.content)

        for channel in self.active_voice_channels:
            if content.startswith("leave " + channel.name):
                await self.active_voice_channels.disconnect_from_channel(channel)
                return

        await message.channel.send("I am sorry. I cannot determine which voice channel you want me to leave.\n It may be that I am not currently connected to the channel.")



    @client.event
    async def on_message(self,message):
        if message.author == client.user:
            return
        
        if not self.client.user.mentioned_in(message):
            return

        content = strip_mention(message.content)

        print(content)

        for (command,action) in self.commands.items():
            if content.startswith(command):
                await action(message)
                break

    def run(self,token):
        with RecordingManager() as self.recordings:
            self.client.run(token)

        self.recordings = None


if __name__ == "__main__":
    with open("secrets/discord_token.txt","r") as token_file:
        token = token_file.read()

    bot = AutocartographerBot()

    bot.run(token)

