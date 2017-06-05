#!/usr/bin/env python3

from discord.ext import commands
import discord.utils
from cogs.utils.config import Config

config = Config('configs/perms.json')

if 'owner' not in config:
  import re
  owner = ''
  while not owner or not re.search('^\\d{15,}$', owner):
    owner = input('please enter YOUR id(use `\\@NAME` to find yours): ')
  config['owner'] = owner

def is_owner():
  return commands.check(lambda ctx: is_owner_check(ctx.message))

def in_group(group):
  return commands.check(lambda ctx: in_group_check(ctx.message, group))

def has_perms(**perms):
  return commands.check(lambda ctx: check_permissions(ctx.message, **perms))

def has_role_check(check, **perms):
  return commands.check(lambda ctx: role_or_permissions(ctx, check, **perms))

# The permission system of the bot is based on a "just works" basis
# You have permissions and the bot has permissions. If you meet the permissions
# required to execute the command (and the bot does as well) then it goes
# through and you can execute the command.
# If these checks fail, then there are two fallbacks.
# A role with the name of Bot Mod and a role with the name of Bot Admin.
# Having these roles provides you access to certain commands without actually
# having the permissions required for them.
# Of course, the owner will always be able to execute commands.

def is_owner_check(message):
  return message.author.id == config['owner']

def in_group_check(msg, group):
  if is_owner_check(msg):
    return True

  for num in config[group]:
    if num == msg.author.id:
      return True
  return False

def check_permissions(msg, **perms):
  if is_owner_check(msg):
    return True

  chan     = msg.channel
  author   = msg.author
  resolved = chan.permissions_for(author)
  return all(getattr(resolved, name, None) == value for name,
                                                        value in perms.items())

def role_or_permissions(ctx, check, **perms):
  #http://discordpy.readthedocs.io/en/latest/api.html#discord.Permissions
  if check_permissions(ctx.message, **perms):
    return True

  chan   = ctx.message.channel
  author = ctx.message.author
  if chan.is_private:
    return False # can't have roles in PMs

  role = discord.utils.find(check, author.roles)
  return role is not None

def is_in_servers(*server_ids):
  def predicate(ctx):
    server = ctx.message.server
    if not server:
      return False
    return server.id in server_ids
  return commands.check(predicate)
