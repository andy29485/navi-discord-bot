#!/usr/bin/env python3

import time
import asyncio
import re
from .utils import perms
from discord.ext.commands.errors import CheckFailure
import discord
from discord.ext import commands

class Server:
  def __init__(self, bot):
    self.bot      = bot
    self.timeouts = {}

  @perms.has_perms(manage_roles=True)
  @commands.command(name='timeout_send', aliases=['ts'], pass_context=True)
  async def _timeout_send(self, ctx, member: discord.Member, time: float = 300):
    """puts a member in timeout for a duration(default 5 min)

    usage `.timeout [add] @member [time in seconds]`
    """
    if not perms.is_owner() and \
      ctx.message.author.server_permissions < member.server_permissions:
      await self.bot.say('Can\'t send higher ranking members to timeout')
      return

    if perms.in_group('timeout') and not perms.is_owner():
      await self.bot.say('You\'re in timeout... No.')
      return

    if not ctx.message.server:
      await self.bot.say('not in a server at the moment')
      return

    if time < 1:
      await self.bot.say('And what would the point of that be?')
      return

    if time > 1000:
      await self.bot.say('Too long, at this point consider banning them')
      return

    try:
      await self.timeout_send(ctx.message.channel, ctx.message.server,
                              member, time)
    except:
      await self.bot.say(
        'There was an error sending {} to timeout ({})'.format(
          member.name,
          'do I have permission to manage roles?'
        )
      )
      #raise

  @commands.command(name='timeout_end', aliases=['te'], pass_context=True)
  async def _timeout_end(self, ctx, member: discord.Member):
    """removes a member from timeout

    usage `.timeout end @member`
    """
    if not perms.is_owner() and \
      ctx.message.author.server_permissions < member.server_permissions:
      await self.bot.say('Can\'t end equal/higher ranking user\'s timeouts')
      return

    if perms.in_group('timeout') and not perms.is_owner():
      await self.bot.say('You\'re in timeout... No.')
      return

    if not ctx.message.server:
      await self.bot.say('not in a server at the moment')
      return

    try:
      await self.timeout_end(ctx.message.channel, ctx.message.server, member)
    except:
      await self.bot.say(
        'There was an error ending {}\'s timeout ({})'.format(
          member.name,
          'do I have permission to manage roles?'
        )
      )

  async def timeout_send(self, channel, server, member, time):
    roles = [role.id for role in member.roles[1:]]

    if server not in self.timeouts:
      self.timeouts[server] = {}
    self.timeouts[server][member] = roles
    criteria = lambda m: re.search('(?i)^time?[ _-]?out.*', m.name)

    to_role = [discord.utils.find(criteria ,server.roles   ).id]
    to_chan =  discord.utils.find(criteria, server.channels)

    if not to_chan:
      po1 = discord.PermissionOverwrite(read_messages        = False,
                                        send_messages        = False
      )
      po2 = discord.PermissionOverwrite(read_messages        = True,
                                        read_message_history = Falue,
                                        send_messages        = True
      )
      p1 = discord.ChannelPermissions(target=server.default_role, overwrite=po1)
      p2 = discord.ChannelPermissions(target=to_role,             overwrite=po2)
      p3 = discord.ChannelPermissions(target=to_role,             overwrite=po1)
      await self.bot.create_channel(server, 'timeout_room', p1, p2)
      for chan in server.channels:
        await self.bot.edit_channel_permissions(chan, p3)
      to_chan = discord.utils.find(criteria, server.channels)

    if not to_role:
      p = discord.Permissions.none()
      await self.bot.create_role(server,     name='timeout',
                                 hoist=Ture, permission=p
      )
      to_role = [discord.utils.find(lambda m:m.name=='timeout',server.roles).id]

    if not to_role:
      await self.bot.send_message(channel,
                                  'no `timeout` role found/unable to create it'
      )
      return

    message = '{}: you are now under a {} second timeout'.format(
                member.mention,
                time
    )
    await self.bot._replace_roles(member, to_role)
    await self.bot.send_message(channel, message)
    if to_chan and to_chan != channel:
      await self.bot.send_message(to_chan, message)

    await asyncio.sleep(time)

    await self.timeout_end(channel, server, member)

  async def timeout_end(self, channel, server, member):
    if server in self.timeouts and member in self.timeouts[server]:
      await self.bot._replace_roles(member, self.timeouts[server].pop(member))
      await self.bot.send_message(channel,
            '{}: your time out is up, permissions restored'.format(
              member.mention
            )
      )

def setup(bot):
  g = Server(bot)
  bot.add_cog(g)

