#!/usr/bin/env python3

import discord
import re

id_pattern   = re.compile('<?[@#][!&]?([0-9]{15,21})>?')
name_pattern = re.compile('^<?@?(.+)#(\\d{4})>?$')

def get_user(server, search_param):
  '''
  return user matching params in server
  search_param can be:
    - id as a string or int
    - @mention of the user
    - username#discriminator (name#0000 - not server nickname)
      - note: this has to be the discord username
      - note: case sensitive(unlike other options)
    - username
    - server nickname
  '''
  if hasattr(server, 'message'):  # if ctx was passed instead of a server
    server = server.message.server
  elif hasattr(server, 'server'): # if a message was passed instead of a server
    server = server.server

  if type(search_param) == int:
    user = server.get_member(str(search_param))
    if user:
      return user

  match = id_pattern.match(search_param)
  if match:
    user = server.get_member(match.group(1))
    if user:
      return user

  match = name_pattern.match(search_param)
  name  = match.group(1) if match else search_param.lower()
  discr = match.group(2) if match else ''

  for user in server.members:
    if name == user.name and discr in str(user.discriminator):
      return user
    if name in (user.name.lower(), user.nick.lower()):
      return user

  return None

def get_role(server, search_param):
  '''
  return role matching params in server
  search_param can be:
    - id as a string or int
    - @mention of the role
    - role name
  '''
  if hasattr(server, 'message'):  # if ctx was passed instead of a server
    server = server.message.server
  elif hasattr(server, 'server'): # if a message was passed instead of a server
    server = server.server

  if type(search_param) == int:
    search_param = str(search_param))
  else:
    match = id_pattern.match(search_param)
    search_param = match.group(1) if match else search_param.lower()

  for role in server.roles:
    if search_param in (str(role.id), role.name.lower()):
      return role

  return None

def get_channel(server, search_param):
  '''
  return channel matching params in server
  search_param can be:
    - id as a string or int
    - #mention of the channel
    - channel name
  '''
  chans = []
  if hasattr(server, 'message'):  # if ctx was passed instead of a server
    chans  = server.bot.get_all_channels()
    server = server.message.server
  elif hasattr(server, 'server'): # if a message was passed instead of a server
    server = server.server

  if type(search_param) == int:
    search_param = str(search_param))
  else:
    match = id_pattern.match(search_param)
    search_param = match.group(1) if match else search_param.lower()

  if server:
    chans = server.channels
    chan  = server.get_channel(search_param)
    if chan:
      return chan


  for chan in chans:
    if search_param in (str(role.id), role.name.lower()):
      return chan

  return None
