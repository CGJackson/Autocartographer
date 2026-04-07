import discord


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

voiceclients = []

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
                new_voice_client = await channel.connect(self_mute=True)
                voiceclients.append(new_voice_client)
                return
    content = strip_mention(message.content)

    for channel in message.guild.voice_channels:
        if content.startswith("join " + channel.name):
            new_voice_client = await channel.connect(self_mute=True)
            voiceclients.append(new_voice_client)
            return

    await message.channel.send("I am sorry. I cannot determine which voice channel you want me to join")



commands = {
    "listen" : record,
    "stop" : stop_record,
    "join" : join
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