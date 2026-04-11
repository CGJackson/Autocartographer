from functools import wraps, partial

from discord.ext import commands

class CommandBot():
    def __init__(self,*args,**kwargs):
        self.bot = commands.Bot(*args,**kwargs)

    def add_command_method(self,name,f):
        self.bot.command(name=name)(wraps(f)(partial(f, self)))