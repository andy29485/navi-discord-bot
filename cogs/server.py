#!/usr/bin/env python3

import time
import asyncio
import requests
import re
from cogs.utils import perms
from discord.ext.commands.errors import CheckFailure
import discord
from cogs.utils.format import *
from discord.ext import commands
from cogs.utils.config import Config
from discord.ext.commands.converter import MemberConverter

class EmWrap:
  def __init__(self, d):
    self.d = d
  def to_dict(self):
    return self.d

class Server:
  def __init__(self, bot):
    self.bot      = bot
    self.timeouts = {}
    self.conf     = Config('configs/server.json')
    self.cut      = {}

  @perms.has_perms(manage_messages=True)
  @commands.command(name='prune', pass_context=True)
  async def _prune(self, ctx, num_to_delete : int, *message):
    """
    deletes specified number of messages from channel
    if message is specified, message will be echoed by bot after prune

    USAGE: .prune <num> [user] [message...]

    NOTE: if first word after number is a user,
          only user's messages will be pruned
    """
    chan = ctx.message.channel
    if num_to_delete > 100:
      await self.bot.say('Sorry, only up to 100')
      return
    if num_to_delete < 1:
      await self.bot.say('umm... no')
      return

    try:
      conv    = MemberConverter(ctx, message[0])
      user    = conv.convert()
      message = message[1:]
    except:
      user = None

    message = ' '.join(message)

    if user:
      c       = lambda m: m.author.id == user.id
      deleted = await self.bot.purge_from(chan ,limit=num_to_delete, check = c)
    else:
      deleted = await self.bot.purge_from(chan ,limit=num_to_delete)
    await self.bot.say(ok('Deleted {} message{} {}'.format(
                             len(deleted),
                             '' if len(deleted) == 1    else 's',
                             '('+message+')' if message else ''
                           )
                         )
    )

  @commands.group(name='role', pass_context=True)
  async def _role(self, ctx):
    """
    Manage publicly available roles
    """
    if ctx.invoked_subcommand is None:
      await self.bot.say(error("Please specify valid subcommand"))

  @_role.command(name='add', pass_context=True)
  @perms.has_perms(manage_roles=True)
  async def _add(self, ctx, role : discord.Role):
    """
    adds role to list of public roles
    """
    await self._add_wrap(ctx, role)

  @_role.command(name='create', pass_context=True)
  @perms.has_perms(manage_roles=True)
  async def _create(self, ctx, role_name : str):
    """
    creates and adds a new role to list of public roles
    """
    serv = ctx.message.server
    role = await self.bot.create_role(serv, name=role_name, mentionable=True)
    await self._add_wrap(ctx, role)

  @_role.command(name='list', aliases=['ls'], pass_context=True)
  @perms.has_perms(manage_roles=True)
  async def _list(self, ctx):
    """
    lists public roles avalible in the server
    """
    serv            = ctx.message.server
    names           = []
    m_len           = 0
    available_roles = self.conf.get(serv.id, {}).get('pub_roles', [])

    if not available_roles:
      await self.bot.say('no public roles in this server\n' + \
                         ' see `.help role create` and `.help role add`'
      )
      return

    for role_id in available_roles:
      role = discord.utils.find(lambda r: r.id == role_id, serv.roles)
      if role:
        names.append(role.name)
        m_len = max(m_len, len(role.name))

    msg  = 'Roles:\n```'
    line = '{{:{}}} - {{}}\n'.format(m_len)
    for name,rid in zip(names, self.conf[serv.id]['pub_roles']):
      msg += line.format(name, rid)
    await self.bot.say(msg+'```')

  async def _add_wrap(self, ctx, role : discord.Role):
    serv = ctx.message.server

    if role.is_everyone:
      await self.bot.say(error('umm... no'))
      return

    if serv.id not in self.conf:
      self.conf[serv.id] = {'pub_roles': []}
    if 'pub_roles' not in self.conf[serv.id]:
      self.conf[serv.id]['pub_roles'] = []

    if role.id in self.conf[serv.id]['pub_roles']:
      await self.bot.say('role already in list')
      return

    self.conf[serv.id]['pub_roles'].append(role.id)
    self.conf.save()
    await self.bot.say(ok('role added to public role list'))

  @_role.command(name='delete', pass_context=True)
  @perms.has_perms(manage_roles=True)
  async def _delete(self, ctx, role : discord.Role):
    """
    removes role from list of public roles
    """
    serv = ctx.message.server

    available_roles = self.conf.get(serv.id, {}).get('pub_roles', [])
    if role.id in available_roles:
      self.conf[serv.id]['pub_roles'].remove(role.id)
      await self.bot.say(ok('role removed from public list'))
    else:
      await self.bot.say(error('role is not in the list'))

  @_role.command(name='request', pass_context=True)
  async def _request(self, ctx, role : discord.Role):
    """
    adds role to requester(if in list)
    """
    auth = ctx.message.author
    serv = ctx.message.server

    available_roles = self.conf.get(serv.id, {}).get('pub_roles', [])
    if role.id in available_roles:
      await self.bot.add_roles(auth, role)
      await self.bot.say(ok('you now have that role'))
    else:
      await self.bot.say(error('I\'m afraid that I can\'t give you that role'))

  @_role.command(name='unrequest', aliases=['requestrm'], pass_context=True)
  async def _unrequest(self, ctx, role : discord.Role):
    """removes role from requester(if in list)"""
    auth = ctx.message.author
    serv = ctx.message.server

    available_roles = self.conf.get(serv.id, {}).get('pub_roles', [])
    found           = discord.utils.find(lambda r: r.id == role.id, auth.roles)

    if role.id in available_roles and found:
      await self.bot.remove_roles(auth, role)
      await self.bot.say(ok('you no longer have that role'))
    else:
      await self.bot.say(error('I\'m afraid that I can\'t remove that role'))


  @perms.has_perms(manage_messages=True)
  @commands.command(name='cut', pass_context=True)
  async def _cut(self, ctx, num_to_cut : int, num_to_skip=0 : int):
    '''
    cuts num_to_cut messages from the current channel
    skips over num_to_skip messages (skips none if not specified)

    example:
    User1: first message
    User2: other message
    User3: final message
    Using ".cut 1 1" will cut User2's message
    Using ".cut 1" will cut User3's message

    messages will not be deleted until paste
    needs manage_messages perm in the current channel to use
    see .paste
    '''
    #if num_to_cut > 100:
    #  await self.bot.say('Sorry, only up to 100')
    #  return
    if num_to_cut < 1:
      await self.bot.say('umm... no')
      return

    aid  = ctx.message.author.id
    chan = ctx.message.channel
    cid  = chan.id
    bef = ctx.message.timestamp
    await self.bot.delete_message(ctx.message)

    if num_to_skip > 0:
      mes_to_skip = []
      async for m in self.bot.logs_from(chan, num_to_skip):
        mes_to_skip.insert(0, m)
      bef = mes_to_skip[0].timestamp

    logs = []
    async for m in self.bot.logs_from(chan, num_to_cut, bef):
      logs.insert(0, m)

    logs.insert(0, 'nsfw' in chan.name.lower())

    self.cut[aid] = logs

  @perms.has_perms(manage_messages=True)
  @commands.command(name='paste', pass_context=True)
  async def _paste(self, ctx):
    '''
    paste cutted messages to current channel

    needs manage_messages perm in the current channel to use
    deletes original messages
    see .cut
    '''
    aid  = ctx.message.author.id
    chan = ctx.message.channel
    logs = self.cut.pop(aid, [])

    if not logs:
      await self.bot.say('You have not cut anything')
      return

    if logs[0] and 'nsfw' not in chan.name.lower():
      await self.bot.say('That which hath been cut in nsfw, ' + \
                         'mustn\'t be pasted in such a place')
      return
    logs = logs[1:]

    await self.bot.delete_message(ctx.message)

    buf = ''
    out = []
    for message in logs:
      if message.content or message.attachments:
        tmp = '<{0.author.name}> {0.content}\n'.format(message)
        for a in message.attachments:
          tmp += '{filename}: {url}\n'.format(**a)
      else:
        tmp = ''
      if len(buf) + len(tmp) > 1900:
        out.append(buf)
        buf = tmp
      else:
        buf += tmp
      if message.embeds and not message.content:
        out.append(buf)
        buf = ''
        for embed in message.embeds:
          out.append(embed)
    if buf:
      out.append(buf)

    for mes in out:
      if type(mes) == str:
        if mes:
          await self.bot.say(mes)
      else:
        await self.bot.say(embed=EmWrap(mes))

    old = False
    while len(logs) > 0:
      if len(logs) > 1:
        if not old:
          try:
            await self.bot.delete_messages(logs[:100])
          except:
            old = True
        if old:
          for entry in logs[:100]:
            await self.bot.delete_message(entry)
        logs = logs[100:]
      else:
        await self.bot.delete_message(logs[0])
        logs.remove(logs[0])

    if aid in self.cut:
      del self.cut[aid]

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
