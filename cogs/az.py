#!/usr/bin/env python3


from discord.ext import commands
from includes.utils import perms
from includes.az import AZ


class AzCog:
  def __init__(self, bot):
    self.bot = bot
    self.az  = AZ()

  @commands.command()
  async def lenny(self, first=''):
    await self.bot.say(self.az.lenny(first))

  @commands.command()
  async def shrug(self):
    await self.bot.say('\n¯\_(ツ)_/¯')

  @commands.command(pass_context=True)
  async def me(self, ctx, *, message : str):
    await self.bot.say(f'*{ctx.message.author.name} {message}*')
    await self.bot.delete_message(ctx.message)

  @commands.command(pass_context=True,name='set_colour',aliases=['sc'])
  @perms.is_in_servers('168702989324779520')
  @perms.has_role_check(lambda r: r.id == '258405421813989387')
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
    server = ctx.message.server
    colour = self.az.get_colour(colour)
    role   = dh.get_role(server, '258405421813989387')

    if not role:
      await self.bot.say('could not find role to change')
    elif not colour:
      await self.bot.say('Could not figure out colour - see help')
    else:
      await self.bot.edit_role(server, role, colour=colour)
      await self.bot.say(ok())

  @commands.command(pass_context=True)
  @perms.in_group('img')
  async def img(self, ctx, *search):
    url = await self.bot.loop.run_in_executor(None, self.az.img, *search)
    if not url:
      await self.bot.say(error(f'Could not find image matching: {search}'))
    elif type(url) == str and url.rpartition('.')[2] in ('zip', 'cbz'):
      zf = zipfile(path, 'r')
      for fl in zf.filelist:
        f = zf.open(fl.filename)
        await self.bot.send_file(ctx.message.channel, f, filename=fl.filename)
        f.close()
      zf.close()
    elif type(url) == str:
      await self.bot.say(url)
    else:
      await self.bot.say(embed=url)

  @commands.command(pass_context=True)
  async def math(self, ctx, *, formula):
    f = lambda: self.az.renderLatex(formula, fmt='png')
    f = await self.bot.loop.run_in_executor(None, f)
    await self.bot.send_file(ctx.message.channel, f, filename='math.png')

  async def repeat(self, message):
    chan = message.channel
    data = self.az.last.get(chan, ['', 0])

    if not message.content:
      return

    if data[0] == message.content.lower():
      data[1] += 1
    else:
      data = [message.content.lower(), 1]

    if data[1] == self.az.conf.get('repeat_after', 3):
      await self.bot.send_message(chan, message.content)
      data[1] = 0

    self.az.last[chan] = data

def setup(bot):
  az = AzCog(bot)
  bot.add_listener(az.repeat, "on_message")
  bot.add_cog(az)
