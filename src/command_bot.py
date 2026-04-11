from functools import wraps, partial

from discord.ext import commands

class CommandBot():
    """
    A class which allows subclasses to register methods as commands with discord.py
    """
    def __init__(self,*args,**kwargs):
        self.bot = commands.Bot(*args,**kwargs)

    def add_command_method(self,name,f):
        """
        Registers a method, f, of this class as a command with discord.py, called name
        """
        self.bot.command(name=name)(wraps(f)(partial(f, self)))