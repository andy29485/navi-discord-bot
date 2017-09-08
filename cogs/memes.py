#!/usr/bin/env python3

import re
import asyncio
import tempfile
from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw
from cogs.utils.format import error
from cogs.utils.config import Config

def wrap_text(text, width, font):
  '''
  input:
    text:  string of text
    width: max width per line, in px
    font:  PIL font object to user_id
  output:
    returns a list of line tuples,
    tuple consists of width of line, and line itself
  '''
  text_lines = [] #list of lines to output
  text_line  = [] #buffer of words for current line
  words = text.replace('\n', ' [br] ').split() #split text into words, honor \n

  for word in words:
    if word == '[br]': # if \n was encountered, break line there
      line = ' '.join(text_line)
      w, h = font.getsize(line)
      text_lines.append( (w, line) )
      text_line = []
      continue

    # iterator part - add word to buffer and calculate width
    text_line.append(word)
    w, h = font.getsize(' '.join(text_line))

    if w > width:                    # if this word makes the line too long
      text_line.pop()                #   remove word from buffer
      line = ' '.join(text_line)     #   join words into line
      w, h = font.getsize(line)      #   calculate width
      text_lines.append( (w, line) ) #   add width and line to output list
      text_line = [word]             #   add word to next buffer

  # if the buffer is not empty at the end,
  #   add remining words to output list
  if len(text_line) > 0:
    w, h = font.getsize(' '.join(text_line))
    text_lines.append((w,' '.join(text_line)))

  return text_lines


def write_image(text, out, **kargs):
  # get variables
  sx        = kargs.get('sx',         0)
  sy        = kargs.get('sy',         0)
  mx        = kargs.get('mx',       100)
  my        = kargs.get('my',       100)
  size      = kargs.get('size',      25)
  spacing   = kargs.get('spacing',    0)
  font_name = kargs.get('font_name', '')
  image     = kargs.get('image',     '')
  match     = kargs.get('match',     '')

  if match:
    match = re.search(match, text)

  # bad idea, I know
  text  = eval("f'''" + kargs.get('format', '{text}') + "'''")

  # load stuff
  img   = Image.open(image)
  font  = ImageFont.truetype(font_name, size)
  draw  = ImageDraw.Draw(img)

  while True:
    lines = wrap_text(text, mx, font) # split into lines to fit in image
    size += spacing

    # if the lines do not fit in the box, resize the text(font)
    if len(lines)*size > my:
      size -= spacing + 1
      font  = ImageFont.truetype(font_name, size)
    else:
      break

  # calculate offset to center vertically
  sy += (my-len(lines)*size)/2

  # draw the lines
  for i,(w,msg) in enumerate(lines):
    draw.text((sx+((mx-w)/2), sy+size*i), msg, (0,0,0), font=font)

  #save the image
  img.save(out)

class MemeGenerator:
  pattern = re.compile(r'(\w+)\s+(.*)$')
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/memes.json')
    self.newline = '\n      '

  @commands.command(pass_context=True, aliases=['memes'])
  async def meme(self, ctx, *, text : str):
    """
    Add text to images
    Usage: .meme <name> <text to add>

    Valid names so far:
      f'{self.newline.join(self.["memes"].keys())}'
    """
    match = MemeGenerator.pattern.match(text)
    name  = match.group(1).lower()
    text  = match.group(2)

    cfg = self.conf.get('memes', {}).get(name, None)

    if not cfg:
      await self.bot.say(error('Could not find image'))
      return
    if not text:
      await self.bot.say(error('Are you trying to get an empty image?'))
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
