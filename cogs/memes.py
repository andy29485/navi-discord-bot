#!/usr/bin/env python3

import re
import asyncio
import tempfile
from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw
from cogs.utils.format import error
from cogs.utils.config import Config

def wrap_text(text, width, font):
  text_lines = []
  text_line = []
  words = text.replace('\n', ' [br] ').split()

  for word in words:
    if word == '[br]':
      w, h = font.getsize(' '.join(text_line))
      text_lines.append((w, ' '.join(text_line)))
      text_line = []
      continue

    text_line.append(word)
    w, h = font.getsize(' '.join(text_line))
    if w > width:
      text_line.pop()
      w, h = font.getsize(' '.join(text_line))
      text_lines.append((w,' '.join(text_line)))
      text_line = [word]

  if len(text_line) > 0:
    w, h = font.getsize(' '.join(text_line))
    text_lines.append((w,' '.join(text_line)))

  return text_lines


def write_image(text,out, sx,sy,mx,my, font_name,image,spacing,size,sufix=''):
  text += sufix
  img = Image.open(image)
  font = ImageFont.truetype(font_name, size)
  draw = ImageDraw.Draw(img)
  lines = wrap_text(text, mx, font)
  size += spacing
  sy += (my-len(lines)*size)/2
  for i,(w,msg) in enumerate(lines):
    draw.text((sx+((mx-w)/2), sy+size*i), msg, (0,0,0), font=font)
  img.save(out)

class MemeGenerator:
  pattern = re.compile(r'(\w+)\s+(.*)$')
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/memes.json')

  @commands.command(pass_context=True)
  async def meme(self, ctx, *, text : str):
    """
    Add text to images
    Usage: .meme <name> <text to add>

    Valid names so far:
      histy
    """
    match = MemeGenerator.pattern.match(text)
    name  = match.group(1).lower()
    text  = match.group(2)

    cfg = self.conf.get('memes', {}).get(name, None)

    if not cfg:
      await self.bot.say(error('Could not find image'))
      return

    temp = tempfile.NamedTemporaryFile(suffix=".png")

    if 'font_name' not in cfg:
      cfg['font_name'] = self.conf['font']

    write_image(text=text, out=temp.name, **cfg)

    await self.bot.send_file(ctx.message.channel, temp.name)

    temp.close()


def setup(bot):
  m = MemeGenerator(bot)
  bot.add_cog(m)
