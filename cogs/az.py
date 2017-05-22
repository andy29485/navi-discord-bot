#!/usr/bin/env python3

import re
import asyncio
import discord
import os
from discord.ext import commands
from cogs.utils.format import *
from cogs.utils import perms
from cogs.utils import puush
from cogs.utils import find as azfind
from cogs.utils.config import Config


that = """
╚═( ͡° ͜ʖ ͡° )═╝
..╚═(███)═╝
.╚═(███)═╝
..╚═(███)═╝
...╚═(███)═╝
....╚═(███)═╝
...╚═(███)═╝
..╚═(███)═╝
.╚═(███)═╝
╚═(███)═╝
.╚═(███)═╝
..╚═(███)═╝
...╚═(███)═╝
...╚═(███)═╝
.....╚(███)╝
.......╚(██)╝
.........(█)
..........*"""

that2 = """
      ( ͡° ͜ʖ ͡°)
　＿    ノ ＼
`/　`/ ⌒Ｙ⌒ Ｙ　ヽ
( 　(三ヽ人　 /　　|
|　ﾉ⌒＼ ￣￣ヽ　 ノ
ヽ＿＿＿＞､＿＿_／   
　　 ｜( 王 ﾉ〈
　　 /ﾐ`ー―彡ヽ
　　/　ヽ_／　 |
　 ｜　　/    ｜
"""

that3 = '''
                         ______
                      .-"""".._'.       _,##
               _..__ |.-"""-.|  |   _,##'`-._
              (_____)||_____||  |_,##'`-._,##'`
              _|   |.;-""-.  |  |#'`-._,##'`
           _.;_ `--' `\    \ |.'`\._,##'`
          /( ͡° ͜ʖ ͡°)`\     |.-";.`_, |##'`
          |\_____/| _..;__  |'-' /
          '.____.'_.-`)\--' /'-'`
           //||\\(_.-'_,'-'`
         (`-...-')_,##'`
  jgs _,##`-..,-;##`
   _,##'`-._,##'`
_,##'`-._,##'`
  `-._,##'`
'''

class AZ:
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def lenny(self, first=None):
    try:
      first = int(first)
      if first < 1:
        first = 1
      if first > 10:
        first = 10
    except:
      first = 1
    await self.bot.say('\n( ͡° ͜ʖ ͡° )'*first)

  @commands.command()
  async def shrug(self):
    await self.bot.say('\n¯\_(ツ)_/¯')

  @commands.command()
  async def lennytipede(self):
    await self.bot.say(code(that))

  @commands.command()
  async def macholenny(self):
    await self.bot.say(code(that2))

  @commands.command()
  async def lennytrain(self):
    await self.bot.say(code(that3))

  @commands.command(pass_context=True)
  @perms.in_group('img')
  async def img(self, ctx, *search):
    if 'path' not in puush.conf or not os.path.exists(puush.conf['path']):
      await self.bot.say('{path} does not exist')
      return

    search = [re.sub(r'[^\w\./#\*-]+', '', i).lower() for i in search]
    for i in range(len(search)):
      if re.search('^(//|#)', search[i]):
        search = search[:i]
        break

    for i in range(len(search)):
      if re.search('^(/\\*)', search[i]):
        for j in range(i, len(search)):
          if re.search('^(\\*/)', search[j]):
            break
        search = search[:i] + search[j+1:]
        break

    loop = asyncio.get_event_loop()
    try:
      f = loop.run_in_executor(None, azfind.search, puush.conf['path'], search)
      path = await f
    except:
      path = ''

    if not path or not path.strip():
      await self.bot.send_message(ctx.message.channel,
                          "couldn't find anything matching: `{}`".format(search)
      )
      return

    try:
      future_url = loop.run_in_executor(None, puush.get_url, path)
      url = await future_url
    except:
      url = 'There was an error uploading the image, ' + \
            'but at least I didn\'t crash :p'
    await self.bot.say(url)

def setup(bot):
  bot.add_cog(AZ(bot))
