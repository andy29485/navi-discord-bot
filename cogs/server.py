#!/usr/bin/env python3

import time
import asyncio
from .utils import perms
from discord.ext.commands.errors import CheckFailure
import discord
from discord.ext import commands

class Server:
  def __init__(self, bot):
    self.bot      = bot
    self.timeouts = {}

  @commands.command(name='timeout_send', aliases=['ts'], pass_context=True)
  async def _timeout_send(self, ctx, member: discord.Member, time: float = 300):
    """puts a member in timeout for a duration(default 5 min)
    
    usage `.timeout [add] @member [time in seconds]`
    """
    if not perms.is_owner() and \
      ctx.message.author.server_permissions < member.server_permissions:
      await self.bot.say('Can\'t send higher ranking members to timeout')
      return
    
    if not ctx.message.server:
      await self.bot.say('not in a server at the moment')
      return
    
    if time < 1:
      await self.bot.say('And what would the point of that be?')
      return
    
    try:
      await self.timeout_send(ctx.message.channel, ctx.message.server,
                              member, time)
    except:
      await self.bot.say('There was an error sending {} to timeout'.format(
        member.name
      ))
      
  @commands.command(name='timeout_end', aliases=['te'], pass_context=True)
  async def _timeout_end(self, ctx, member: discord.Member):
    """removes a member from timeout
    
    usage `.timeout end @member`
    """
    if not perms.is_owner() and \
      ctx.message.author.server_permissions < member.server_permissions:
      await self.bot.say('Can\'t end equal/higher ranking user\'s timeouts')
      return

    if perms.in_group('timeout'):
      await self.bot.say('You\'re in timeout... No.')
      return
    
    if not ctx.message.server:
      await self.bot.say('not in a server at the moment')
      return
    
    try:
      await self.timeout_end(ctx.message.channel, ctx.message.server, member)
    except:
      await self.bot.say('There was an error ending {}\'s timeout'.format(
        member.name
      ))

  async def timeout_send(self, channel, server, member, time):
    roles = [role.id for role in member.roles[1:]]
    
    if server not in self.timeouts:
      self.timeouts[server] = {}
    self.timeouts[server][member] = roles
    
    to_role = [discord.utils.find(lambda m: m.name=='timeout',server.roles).id]
    
    if not to_role:
      await self.bot.send_message(channel, 'not `timeout` role found')
      return
    
    await self.bot._replace_roles(member, to_role)
    await self.bot.send_message(channel,
          '{}: you are now under a {} second timeout'.format(
      member.mention,
      time
    ))
    
    await asyncio.sleep(time)

    await self.timeout_end(channel, server, member)

  async def timeout_end(self, channel, server, member):
    if server in self.timeouts and member in self.timeouts[server]:
      await self.bot._replace_roles(member, self.timeouts[server].pop(member))
      await self.bot.send_message(channel,
            '{}: your time out is up, permissions restored'.format(
        member.mention
      ))

def setup(bot):
  g = Server(bot)
  bot.add_cog(g)

