#!/usr/bin/env python3

import time
import asyncio
import discord
import logging
import includes.utils.heap as heap
import includes.utils.discord_helper as dh

logger = logging.getLogger('navi.timeout')

class Timeout(heap.HeapNode):
  def __init__(self, chan, serv, user, end_time, roles=[]):
    # append an extraniouse role to the start
    #  to simulate the @everyone role
    roles.insert(0, None)

    self.end_time   =  end_time
    self.channel_id =  int(getattr(chan,    'id',  chan))
    self.server_id  =  int(getattr(serv,    'id',  serv))
    self.user_id    =  int(getattr(user,    'id',  user))
    self.roles      = [int(getattr(role,    'id',  role))
           for role in getattr(user, 'roles', roles)
    ]

    # remove the everyone role from the list
    self.roles = self.roles[1:]

  @staticmethod
  def from_dict(dct):
    chan     = int(dct.get('channel_id'))
    serv     = int(dct.get('server_id'))
    user     = int(dct.get('user_id'))
    end_time = int(dct.get('end_time'))
    roles    = int(dct.get('roles'))

    return Timeout(constr, chan, serv, user, end_time, roles)

  def to_dict(self):
    '''
    convert this timeout object to a dictionary
    used for exporting to json
    '''
    d = {'__timeout__':True}
    d['channel_id'] = int(self.channel_id)
    d['server_id']  = int(self.server_id)
    d['user_id']    = int(self.user_id)
    d['roles']      = int(self.roles)
    d['end_time']   = int(self.end_time)
    return d

  # ==
  def __eq__(self, other):
    if type(self) != type(other):
      return False
    return self.server_id == other.server_id and self.user_id == other.user_id

  # <
  def __lt__(self, other):
    return self.end_time < other.end_time

  # >
  def __gt__(self, other):
    return self.end_time > other.end_time

  async def begin(self, bot, timeout_role, timeout_channel):
    '''
    starts the timout:
      - user gets send to timeout
      - timeout gets stored in heap
      - timeout permissons for other channels get set
    '''
    # set end_time to proper time upon start of timeout
    self.end_time += time.time()
    serv   = bot.get_guild(self.server_id)
    chan   = dh.get_channel(serv, self.channel_id)
    member = dh.get_user(serv, self.user_id)

    # if matching timout obj exists... ignore this one
    for index,timeout_obj in enumerate(self.heap):
      if timeout_obj == self:
        self.heap.pop(index)
        await bot.say('user is in timout, their timout will be extend')
        break

    # if timeout_role does not exist, create it
    if not timeout_role:
      p = discord.Permissions.none()
      to_role = await server.create_role(
                name='timeout', mentionable=False,
                hoist=True,     permissions=p,
                colour=discord.Colour.dark_red()
      )
      if not to_role: # if it could not be created, stop
        await chan.send('no `timeout` role found/unable to create it')
        return

    # permission objects:
    #   po1 - dissallow read/send - for all channels (except next two)
    #   po2 - allow read/send     - for timeout channel only(for talk with mods)
    #   po2 - allow access        - for bot in timeout room
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

    # dissable access to all channels for timeout_role
    #   this is done each time in case a new channel gets created/modified/etc.
    for chan in serv.channels:
      await chan.set_permissions(to_role, overwrite=po1)

    # create channel if needed
    # set permissions:
    #   p1 - normal users(not in timeout) - cannot read
    #   p2 - timeout_role(not in timeout) - can read/send
    if not to_chan:
      overwrites = {
        server.default_role: po1,
        to_role:             po2,
      }
      to_chan = await server.create_text_channel(
            'timeout_room', overwrites=overwrites
      )
    await to_chan.set_permissions(bot.user, overwrite=po3)

    # format message
    message = '{}: you are now under a {} second timeout'.format(
                member.mention,
                time
    )
    # remove current roles, and apply timout role, then send message
    await member.edit(roles=to_role)
    await asyncio.sleep(1)  # wait so that the user does not get a notification
    await chan.send(message)# in a chan they can't access

    # send message to the channel where the timeout request was made
    if to_chan and to_chan != chan:
      try:
        await to_chan.send(message)
      except:
        pass

  async def end(self, bot, index=-1):
    '''
    Ends the timeout associated with this object
    '''
    # get data objects
    serv   = bot.get_guild(self.server_id)
    chan   = dh.get_channel(serv, self.channel_id)
    member = dh.get_user(serv, self.user_id)
    roles  = [dh.get_role(dh, role_id) for role_id in self.roles]

    # restore perms and notify user
    await member.edit(roles=roles)
    await chan.send('{}: your time out is up, permissions restored'.format(
        member.mention
    ))
