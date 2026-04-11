import wave
import os

import discord
from discord.ext import commands,voice_recv

from command_bot import CommandBot
import generation

class RecordingManager():
    def __init__(self):
        self.live_files = {}
        self.created_files = []

    def __enter__(self):
        return self

    def __exit__(self,exc_type, exc_val, exc_tb):
        # close any files that remain open
        for file in self.live_files.values():
            file.close()
        self.live_files = {}

        # delete temporary files 
        for file_list in self.created_files.values():
            for file in file_list:
                os.remove(file)
        self.created_files = {}
        return False


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


class AutocartographerBot(CommandBot):
    def __init__(self):

        self.intents = discord.Intents.default()
        self.intents.message_content = True

        super().__init__(command_prefix=commands.when_mentioned, intents=self.intents)

        self.active_voice_channels = VoiceChannelDirectory()
        self.recordings = None

        self.bot.event(self.on_ready)
        self.add_command_method("listen",AutocartographerBot.record)
        self.add_command_method("draw",AutocartographerBot.complete_recording)
        self.add_command_method("join",AutocartographerBot.join)
        self.add_command_method("leave",AutocartographerBot.leave)

        self.generation_model = generation.Model()


    async def on_ready(self):
        print(f'We have logged in as {self.bot.user}')

    async def record(self,ctx):
        """
        Has the bot start recording a voice channel containing
        the author of the message, in order to generate a map.
        """
        print("record not implemented")


    def generate_map(self,recording_filename : str):
        with wave.open(recording_filename,"rb") as recording:
            response = self.generation_model.generate_from_voice(recording)
        image_data = self.generation_model.extract_image_data(response)

        recording_prefix = ".".join(recording_filename.split(".")[:-1])

        result_filename = f"outputs/{recording_prefix}.png"
        
        with open(result_filename, "wb") as f:
            f.write(image_data[0])

        return result_filename

    async def complete_recording(self,ctx : commands.Context):
        """
        Has the bot stop recording from a channel and
        generate a map
        """

        listening_client = self.active_voice_channels.get_client_in_channel_with_user(ctx.message.user)
        listening_client.stop_listening()
        self.recordings.close(listening_client)

        recording_filename = self.recordings.get_last_file_for_client(listening_client)
        map_file = r"tests/test_data/slough_map.png"#= self.generate_map(recording_filename)

        await ctx.author.send(file=discord.File(map_file))

    async def join(self,ctx : commands.Context,target_channel):
        """
        Adds the bot to a voice channel.
        
        Either uses a voice channel mentioned in the message or, 
        if there isn't one, a voice mentioned after the join
        command
        """
        print(self,ctx,target_channel,flush=True)

        for channel in ctx.guild.voice_channels:
            if target_channel.strip() == channel.name.strip():
                await self.active_voice_channels.connect_to_channel(channel)
                return

        await ctx.message.channel.send("I am sorry. I cannot determine which voice channel you want me to join")

    async def leave(self,ctx,target_channel):
        """
        Removes bot from a voice channel

        Either uses a voice channel mentioned in the message or, 
        if there isn't one, a voice mentioned after the leave
        command
        """

        for channel in self.active_voice_channels:
            if target_channel.strip() == channel.name.strip():
                await self.active_voice_channels.disconnect_from_channel(channel)
                return

        await ctx.message.channel.send("I am sorry. I cannot determine which voice channel you want me to leave.\n It may be that I am not currently connected to the channel.")



    def run(self,token):
        with RecordingManager() as self.recordings:
            self.bot.run(token)

        self.recordings = None


if __name__ == "__main__":
    with open("secrets/discord_token.txt","r") as token_file:
        token = token_file.read()

    bot = AutocartographerBot()

    bot.run(token)

