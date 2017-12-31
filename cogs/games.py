#!/usr/bin/env python3

import asyncio
import random
import os
from cogs.utils import perms
from discord.ext import commands
from cogs.utils.config import Config
from cogs.utils import format as formatter

class Games:
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/games.json')

  @perms.is_owner()
  @commands.command(pass_context=True, aliases=['faa'])
  async def fake_artist_add(self, ctx, *, themes):
    self.conf['fake_artist']['themes'].extend(themes.strip().split('\n'))
    self.conf.save()
    await self.bot.say(formatter.ok())

  @commands.command(pass_context=True, aliases=['fa'])
  async def fake_artist(self, ctx, number : int):
    conf   = self.conf.get('fake_artist', {})
    themes = conf.get('themes', [])
    themes = random.sample(themes, len(themes)-len(themes)%number)
    output = [[]]*number
    fakes  = list(range(number))*(len(themes)//number)
    random.shuffle(fakes)
    say = 'here are the links:'

    # generate
    for theme,fake in zip(themes, fakes):
      for i in range(len(output)):
        output[i].append(theme if i != fake else 'YOU ARE THE FAKE')

    # generate master file
    with open(os.path.join(conf.get('path',''), 'master.html'), 'w') as f:
      f.write(conf.get('rules'))
      for i,theme in enumerate(themes):
        f.write(f'''<li><input type="button" value="show"'''+ \
                f'''onclick="this.value=this.value=='show'''+ \
                f'''\'?'{theme}':'show';"></li>''')
      f.write(conf.get('out'))

    # generate player files
    for i in range(len(output)):
      filename = os.path.join(conf.get('path',''), f'{i}.html')
      with open(filename, 'w') as f:
        f.write(conf.get('rules'))
        for theme in output[i]:
          f.write(f'<li>{theme}</li>')
        f.write(conf.get('out'))
      say += f'\nhttps://andy29485.tk/files/{i}.html'

    await self.bot.say(formatter.ok(say))


def setup(bot):
  bot.add_cog(Games(bot))
