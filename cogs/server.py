#!/usr/bin/env python3

import time
import asyncio
import re
from cogs.utils import perms
from discord.ext.commands.errors import CheckFailure
import discord
from cogs.utils.format import *
from discord.ext import commands

class Server:
  def __init__(self, bot):
    self.bot      = bot
    self.timeouts = {}

  @perms.has_perms(manage_messages=True)
  @commands.command(name='prune', pass_context=True)
  async def _prune(self, ctx, num_to_delete : int, *message):
    if num_to_delete > 100:
      await self.bot.say('Sorry, only up to 100')
      return
    if num_to_delete < 1:
      await self.bot.say('umm... no')
      return

    message = ' '.join(message)

    deleted = await self.bot.purge_from(ctx.message.channel,limit=num_to_delete)
    await self.bot.say(ok('Deleted {} message{} {}'.format(
                             len(deleted),
                             '' if len(deleted) == 1    else 's',
                             '('+message+')' if message else ''
                           )
                         )
    )

  @commands.command(name='topic', pass_context=True)
  async def _topic(self, ctx, *, new_topic = ''):
    """manage topic

    if a new_topic is specified, changes the topic
    otherwise, displays the current topic
    """
    c = ctx.message.channel
    if new_topic:
      if perms.check_permissions(ctx.message, manage_channels=True):
        await self.bot.edit_channel(c, topic = new_topic)
        await self.bot.say(ok('Topic for #{} has been changed'.format(c.name)))
      else:
        await self.bot.say(
           error('You cannot change the topic for #{}'.format(c.name))
        )
    elif c.topic:
      await self.bot.say('Topic for #{}: `{}`'.format(c.name, c.topic))
    else:
      await self.bot.say('#{} has no topic'.format(c.name))

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

    server  = ctx.message.server
    channel = ctx.message.channel

    if server in self.timeouts and member in self.timeouts[server]:
      await self.bot.say('{}\'s already in timeout...'.format(member.name))
      return

    if perms.in_group('timeout') and not perms.is_owner():
      await self.bot.say('You\'re in timeout... No.')
      return

    if not ctx.message.server:
      await self.bot.say('not in a server at the moment')
      return

    if time < 10:
      await self.bot.say('And what would the point of that be?')
      return

    if time > 4000:
      await self.bot.say('Too long, at this point consider banning them')
      return

    try:
      await self.timeout_send(channel, server, member, time)
    except:
      await self.bot.say(
        'There was an error sending {}\'s to timeout \n({}{}\n)'.format(
          member.name,
          '\n  - do I have permission to manage roles(and possibly channels)?',
          '\n  - is my highest role above {}\'s highest role?'.format(
             member.name
          )
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

    server  = ctx.message.server
    channel = ctx.message.channel

    if server not in self.timeouts or member not in self.timeouts[server]:
      await self.bot.say('{} is not in timeout...'.format(member.name))
      return


    if perms.in_group('timeout') and not perms.is_owner():
      await self.bot.say('You\'re in timeout... No.')
      return

    if not ctx.message.server:
      await self.bot.say('not in a server at the moment')
      return

    try:
      await self.timeout_end(channel, server, member)
    except:
      await self.bot.say(
        'There was an error ending {}\'s timeout \n({}{}\n)'.format(
          member.name,
          '\n  - do I have permission to manage roles(and possibly channels)?',
          '\n  - is my highest role above {}\'s highest role?'.format(
             member.name
          )
        )
      )

  async def timeout_send(self, channel, server, member, time):
    roles = member.roles[1:]

    if server not in self.timeouts:
      self.timeouts[server] = {}
    self.timeouts[server][member] = roles
    criteria = lambda m: re.search('(?i)^time?[ _-]?out.*', m.name)

    to_role = discord.utils.find(criteria, server.roles   )
    to_chan = discord.utils.find(criteria, server.channels)

    if not to_role:
      p = discord.Permissions.none()
      to_role = await self.bot.create_role(server,            name='timeout',
                                           hoist=True,        permissions=p,
                                           mentionable=False,
                                           colour=discord.Colour.dark_red()
      )
      if not to_role:
        await self.bot.send_message(channel,
                                   'no `timeout` role found/unable to create it'
        )
        return

    po1 = discord.PermissionOverwrite(read_messages        = False,
                                      read_message_history = False,
                                      send_messages        = False
    )
    po2 = discord.PermissionOverwrite(read_messages        = True,
                                      read_message_history = False,
                                      send_messages        = True
    )
    po3 = discord.PermissionOverwrite(read_messages        = True,
                                      read_message_history = True,
                                      send_messages        = True
    )

    for chan in server.channels:
      await self.bot.edit_channel_permissions(chan, to_role, po1)
    if not to_chan:
      p1 = discord.ChannelPermissions(target=server.default_role, overwrite=po1)
      p2 = discord.ChannelPermissions(target=to_role,             overwrite=po2)
      to_chan = await self.bot.create_channel(server, 'timeout_room', p1, p2)
    me = discord.utils.find(lambda m: m.id == self.bot.user.id,server.members)
    await self.bot.edit_channel_permissions(to_chan, me, po3)

    message = '{}: you are now under a {} second timeout'.format(
                member.mention,
                time
    )
    await self.bot.replace_roles(member, to_role)
    await asyncio.sleep(1)
    await self.bot.send_message(channel, message)
    if to_chan and to_chan != channel:
      try:
        await self.bot.send_message(to_chan, message)
      except:
        pass

    await asyncio.sleep(time)

    await self.timeout_end(channel, server, member)

  async def timeout_end(self, channel, server, member):
    if server in self.timeouts and member in self.timeouts[server]:
      await self.bot.replace_roles(member, *self.timeouts[server].pop(member))
      await self.bot.send_message(channel,
            '{}: your time out is up, permissions restored'.format(
              member.mention
            )
      )

def setup(bot):
  g = Server(bot)
  bot.add_cog(g)
