#!/usr/bin/env python3

import re
import time
import asyncio
import requests
import discord
from collections import namedtuple
from discord.ext import commands
from discord.ext.commands.errors import CheckFailure
from discord.ext.commands.converter import MemberConverter
from cogs.utils import perms
from cogs.utils.format import *
from cogs.utils.config import Config
from cogs.utils.timeout import Timeout
from cogs.utils import discord_helper as dh

# wrapper class for embeds,
#   just stores a dict, and returns the dict when to_dict is called
# This was created for the cut/paste commands,
#   when cutting messages, embeds were returned as dicts. Creating an Embed
#   object from these embeds is currently not possible (directly at least).
#   Insted, I created an class that can be passed to the api as an embed, since
#   discordpy just uses the to_dict method when passing the call up the the web.
class EmWrap:
  def __init__(self, d):
    self.d = d
  def to_dict(self):
    return self.d

class Server:
  def __init__(self, bot):
    self.bot      = bot
    self.conf     = Config('configs/server.json')
    self.cut      = {}                             # cuts get lost on restart

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
    # tmp channel/server pointer
    chan = ctx.message.channel
    serv = ctx.message.server

    if num_to_delete > 100:                       # api only allows up to 100
      await self.bot.say('Sorry, only up to 100') # TODO - copy thing done in
      return                                      #        self._paste
    if num_to_delete < 1:                         # delete nothing?
      await self.bot.say('umm... no')             #  answer: no
      return

    # if the first word in the message matches a user,
    #   remove that word from the message, store the user
    try:
      user = dh.get_user(serv, message[0])
      if user:
        message = message[1:]
    except:
      user = None

    message = ' '.join(message) #make the message a string

    if user: # if a user was matched, delete messages from tat user only
      c       = lambda m: m.author.id == user.id
      deleted = await self.bot.purge_from(chan, limit=num_to_delete, check = c)
    else:    # other wise just delete messages
      deleted = await self.bot.purge_from(chan, limit=num_to_delete)

    #report that prume was complete, how many were prunned, and the message
    await self.bot.say(ok('Deleted {} message{} {}'.format(
                             len(deleted),
                             '' if len(deleted) == 1    else 's',
                             '('+message+')' if message else ''
                           )
                         )
    )

  @commands.group(name='role', pass_context=True)
  async def _role(self, ctx, role : str = ''):
    """
    Manage publicly available roles
    """
    if ctx.invoked_subcommand is None:
      await self.bot.say('Are you trying to [a]dd a new role' + \
                         'or are you [r]equesting this role for yourself?'
      )
      try:
        msg = await self.bot.wait_for_message(30, author=ctx.message.author,
                                                  channel=ctx.message.channel
        )
      except:
        msg = None
      if msg:
        msg = msg.content.lower()
        if msg.startswith('a') or 'add' in msg:
          await self._add_wrap(ctx, role)
        elif msg.startswith('r') or 'request ' in msg:
          await self._add_wr_request_wrap(ctx, role)
        else:
          await self.bot.say(error('I have no idea what you are attempting' + \
                                   ' to do, maybe look at the help?')
          )
      else:
        await self.bot.say(error('Response timeout, maybe look at the help?'))

  @_role.command(name='add', pass_context=True)
  @perms.has_perms(manage_roles=True)
  async def _add(self, ctx, role : str):
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
  async def _request(self, ctx, role : str):
    await _request_wrap(ctx, role)

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


  async def _add_wrap(self, ctx, role):
    serv = ctx.message.server

    if type(role) != discord.Role:
      role = dh.get_role(role)

    if not role:
      await self.bot.say(error("could not find role"))
      # honestly I could probably just do:
      #role = await self.bot.create_role(serv, name=role_name, mentionable=True)
      # but instead, error and return
      return

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

  async def _request_wrap(self, ctx, role):
    """
    adds role to requester(if in list)
    """
    auth = ctx.message.author
    serv = ctx.message.server

    if type(role) != discord.Role:
      role = dh.get_role(role)
      await self.bot.say(error("could not find role, ask a mod to create it"))
      return

    available_roles = self.conf.get(serv.id, {}).get('pub_roles', [])
    if role.id in available_roles:
      await self.bot.add_roles(auth, role)
      await self.bot.say(ok('you now have that role'))
    else:
      await self.bot.say(error('I\'m afraid that I can\'t give you that role'))

  @perms.has_perms(manage_messages=True)
  @commands.command(name='cut', pass_context=True)
  async def _cut(self, ctx, num_to_cut : int, num_to_skip : int = 0):
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
    if num_to_cut < 1: # can't cut no messages
      await self.bot.say('umm... no')
      return

    # store info in easier to access variables
    aid  = ctx.message.author.id
    chan = ctx.message.channel
    cid  = chan.id
    bef  = ctx.message.timestamp

    # delete the original `.cut` message(not part of cutting)
    # also sorta serves as confirmation that messages have been cut
    await self.bot.delete_message(ctx.message)

    # if messages should be skipped when cutting
    # save the timestamp of the oldest message
    if num_to_skip > 0:
      async for m in self.bot.logs_from(chan, num_to_skip, reverse=True):
        bef = m.timestamp
        break

    # save the logs to a list
    logs = []
    async for m in self.bot.logs_from(chan,num_to_cut,before=bef,reverse=True):
      logs.append(m)

    #store true in position 0 of list if channel is a nsfw channel
    logs.insert(0, 'nsfw' in chan.name.lower())

    # save logs to dict (associate with user)
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
    # get messages that were cut and other variables
    aid  = ctx.message.author.id
    chan = ctx.message.channel
    logs = self.cut.pop(aid, [])

    # if nothing was cut, stop
    if not logs:
      await self.bot.say('You have not cut anything')
      return

    # it messages were cut in a nsfw channel,
    #   do not paste unless this is a nsfw channel
    # NOTE: cutting/pasting to/from PMs is not possible(for now)
    if logs[0] and 'nsfw' not in chan.name.lower():
      await self.bot.say('That which hath been cut in nsfw, ' + \
                         'mustn\'t be pasted in such a place'
      )
      return

    # remove the nsfw indicator(since it's not really part of the logs)
    logs = logs[1:]

    # delete the `.paste` message
    await self.bot.delete_message(ctx.message)

    # compress the messages - many messages can be squished into 1 big message
    # but ensure that output messages do not exceede the discord message limit
    buf = ''  # current out message that is being compressed to
    out = []  # output messages that have been compressed
    for message in logs:
      # save messages as:
      #   <nick> message
      # and attachments as(after the message):
      #   filename: url_to_attachment
      if message.content or message.attachments:
        tmp = '<{0.author.name}> {0.content}\n'.format(message)
        for a in message.attachments:
          tmp += '{filename}: {url}\n'.format(**a)
      else:
        tmp = ''
      # if this message would make the current output buffer too long,
      #   append it to the output message list and reset the buffer
      # or just append to the buffer if it's not going to be too long
      if len(buf) + len(tmp) > 1900:
        out.append(buf)
        buf = tmp
      else:
        buf += tmp

      # if the message is composed of *only* embeds,
      #   flush buffer,
      #   and append embed to output list
      if message.embeds and not message.content:
        if buf:
          out.append(buf)
          buf = ''
        for embed in message.embeds:
          out.append(embed)

    # if there is still content in the buffer after messages have been traversed
    #   treat buffer as complete message
    if buf:
      out.append(buf)

    # send each message in output list
    for mes in out:
      if type(mes) == str:
        if mes:
          await self.bot.say(mes)
      else:                                   # if it's an embed, n
        await self.bot.say(embed=EmWrap(mes)) #   it needs to be wrapped

    # once all messages have been pasted, delete(since cut) the old ones

    old = False # messages older than 2 weeks cannot be batch deleted

    while len(logs) > 0:     # while there are messages to delete
      if len(logs) > 1:      #   if more than one left to delete and not old,
        if not old:          #     attempt batch delete [2-100] messages
          try:
            await self.bot.delete_messages(logs[:100])
          except:            #   if problem when batch deleting
            old = True       #     then the messages must be old
        if old:              # if old, traverse and delete individually
          for entry in logs[:100]:
            await self.bot.delete_message(entry)
        logs = logs[100:]
      else:                   # if only one message, delete individually
        await self.bot.delete_message(logs[0])
        logs.remove(logs[0])

    # remove cut entry from dict of cuts
    if aid in self.cut:
      del self.cut[aid]

  @commands.command(name='topic', pass_context=True)
  async def _topic(self, ctx, *, new_topic = ''):
    """manage topic

    if a new_topic is specified, changes the topic
    otherwise, displays the current topic
    """
    # store channel in tmp pointer
    c = ctx.message.channel

    if new_topic:
      # if a topic was passed,
      #   change it if user has the permisssions to do so
      #   or tell user that they can't do that
      if perms.check_permissions(ctx.message, manage_channels=True):
        await self.bot.edit_channel(c, topic = new_topic)
        await self.bot.say(ok('Topic for #{} has been changed'.format(c.name)))
      else:
        await self.bot.say(
           error('You cannot change the topic for #{}'.format(c.name))
        )
    elif c.topic:
      # if no topic has been passed,
      #   say the topic
      await self.bot.say('Topic for #{}: `{}`'.format(c.name, c.topic))
    else:
      # if not topic in channel,
      #   say so
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

    if perms.in_group('timeout') and not perms.is_owner():
      await self.bot.say('You\'re in timeout... No.')
      return

    if not ctx.message.server:
      await self.bot.say('not in a server at the moment')
      return

    if time < 10:
      await self.bot.say('And what would the point of that be?')
      return

    if time > 10000:
      await self.bot.say('Too long, at this point consider banning them')
      return

    criteria = lambda m: re.search('(?i)^time?[ _-]?out.*', m.name)

    to_role = discord.utils.find(criteria, server.roles   )
    to_chan = discord.utils.find(criteria, server.channels)

    try:
      timeout_obj = Timeout(channel, server, member, time)
      await timeout_obj.start(self.bot, to_role, to_chan)
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

  @perms.has_perms(manage_roles=True)
  @commands.command(name='timeout_end', aliases=['te'], pass_context=True)
  async def _timeout_end(self, ctx, member: discord.Member):
    """removes a member from timeout

    usage `.timeout end @member`
    """
    server  = ctx.message.server
    channel = ctx.message.channel

    if perms.in_group('timeout') and not perms.is_owner():
      await self.bot.say('You\'re in timeout... No.')
      return

    if not ctx.message.server:
      await self.bot.say('not in a server at the moment')
      return

    # test timeout object for comparison
    test  = namedtuple({'server_id':server.id, 'user_id':member.id})
    index = 0 # inext is used to more efficently pop from heap

    # error message in case ending timeout fails
    error_msg = 'There was an error ending {}\'s timeout \n({}{}\n)'.format(
      member.name,
      '\n  - do I have permission to manage roles(and possibly channels)?',
      '\n  - is my highest role above {}\'s highest role?'.format(
         member.name
      )
    )

    for timeout in Timeout.conf['timeouts']:  # look trhough all timouts
      if timeout == test:                     #   if found
        try:
          await timeout.end(self.bot, index)  #     attempt to end
        except:
          await self.bot.say(error_msg)       #     if error when ending, report
        return
      index += 1                              #   not found increment index
    else:                                     # not found at all, report
      await self.bot.say('{} is not in timeout...'.format(member.name))
      return

  async def check_timeouts(self):
    while self == self.bot.get_cog('Server'): # in case of cog reload
      # while timeouts exist, and the next one's time has come,
      #   end it
      while Timeout.conf['timeouts'] and \
            Timeout.conf['timeouts'][0].time_left < 1:
        await Timeout.conf['timeouts'][0].end(self.bot, 0)

      # wait a bit and check again
      #   if the next one ends in < 15s, wait that much instead of 15s
      if Timeout.conf['timeouts']:
        delay = min(Timeout.conf['timeouts'].time_left, 15)
      else:
        delay = 15
      await asyncio.sleep(delay+0.5)

def setup(bot):
  g = Server(bot)
  bot.add_cog(g)
