#!/usr/bin/env python3

import os
import discord
import logging
from discord.ext import commands
from zipfile import ZipFile as zipfile
import includes.utils.format as formatter
from includes.utils import perms
from includes.az import AZ

logger = logging.getLogger('navi.az')
upload_limit = 7.9999

class AzCog:
  def __init__(self, bot):
    self.bot = bot
    self.az  = AZ()

  @commands.command()
  async def lenny(self, ctx, first=''):
    await ctx.send(self.az.lenny(first))

  @commands.command()
  async def shrug(self, ctx):
    await ctx.send('\n¯\_(ツ)_/¯')

  @commands.command()
  async def me(self, ctx, *, message : str):
    '''
    a substitue for /me, because discord did not implement IRC's /me well
    '''
    await ctx.send(f'*{ctx.message.author.name} {message}*')
    await ctx.message.delete()

  @commands.command(name='set_colour',aliases=['sc'])
  @perms.is_in_servers('168702989324779520')
  @perms.has_role_check(lambda r: str(r.id) == '258405421813989387')
  async def _set_colour(self, ctx, colour):
    """
    set role colour

    colour can be a hex value or a name:
    teal         0x1abc9c.
    dark_teal    0x11806a.
    green        0x2ecc71.
    dark_green   0x1f8b4c.
    blue         0x3498db.
    dark_blue    0x206694.
    purple       0x9b59b6.
    dark_purple  0x71368a.
    magenta      0xe91e63.
    dark_magenta 0xad1457.
    gold         0xf1c40f.
    dark_gold    0xc27c0e.
    orange       0xe67e22.
    dark_orange  0xa84300.
    red          0xe74c3c.
    dark_red     0x992d22.
    lighter_grey 0x95a5a6.
    dark_grey    0x607d8b.
    light_grey   0x979c9f.
    darker_grey  0x546e7a.
    """
    server = ctx.message.guild
    colour = self.az.get_colour(colour)
    role   = dh.get_role(server, '258405421813989387')

    if not role:
      await ctx.send('could not find role to change')
    elif not colour:
      await ctx.send('Could not figure out colour - see help')
    else:
      await role.edit(colour=colour)
      await ctx.send(ok())

  @commands.command()
  @perms.in_group('img')
  async def img(self, ctx, *search):
    '''
    Searches bot's image repository for a matching image

    Note: Needs permissions (ask bot owner to give them to you)

    Search format:
    - search terms are seperated by spaces
    - search terms evaluated on an AND basis
    - search terms starting with `-` (minus/hyphen) are negativly matched
      (cannot be in the results)
    - `_` is treated as a word boundry (matches start, end, `_`, `.`, and `/`)
      - e.g.
        "do" can match "do", "undo" and "don't"
        "_do" will match "do" and "don't" (not "undo")
        "do_" will match "do" and "undo" (not "don't")
        "_do_" will only match "do"
    - `-` (minus/hyphen) is treated as `_`, except at start of a search term
    - comments are ignored when searching
      - `//` everything after `//` is a comment
      - everything between `/*` and `*/` is a comment
    - `*` matches 0 or more chars (useful when order matters)
      `do not` can match "do not", "do a jump not a hop", and "not do"
      `do*not` would NOT match "not do" (but matches the other examples)

    Examples:
    - .img test
    - .img k -ok
    - .img -_run_
    - .img _run- // a comment
    - .img _run_ /* treated the same as above */
    - .img this /* will only search the outer */ tags

    '''
    async with ctx.typing():
      path,url = await self.bot.loop.run_in_executor(None, self.az.img, *search)

      if path:
        size_ok = os.stat(path).st_size/1024/1024 <= upload_limit
      else:
        size_ok = False

      logger.debug('img (%s) - %s', type(path), str(path))

      if not path:
        error = formatter.error(f'Could not find image matching: {search}')
        await ctx.send(error)
      elif type(path) != str:
        await ctx.send(embed=path)
      elif path.rpartition('.')[2] in ('zip', 'cbz'):
        zf = zipfile(path, 'r')
        for fl in zf.filelist:
          f = zf.open(fl.filename)
          await ctx.send(file=discord.File(f, fl.filename))
          f.close()
        zf.close()
      elif path.rpartition('.')[2] in ('gif','png','jpg','jpeg') and size_ok:
        await ctx.send(file=discord.File(path))
      else:
        await ctx.send(url)

  async def repeat(self, message):
    logger.debug('repeat message listener start')
    await self.az.repeat(self.bot, message)
    logger.debug('repeat message listener end')

  async def censor(self, message):
    logger.debug('censor message listener start')
    await self.az.censor(self.bot, message)
    logger.debug('censor message listener end')

def setup(bot):
  az = AzCog(bot)
  bot.add_listener(az.repeat, "on_message")
  bot.add_listener(az.censor, "on_message")
  bot.add_cog(az)
