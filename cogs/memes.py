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
      if not line:                   #   if empty (single word was too long)
        return None                  #     return none to get a different font
      w, h = font.getsize(line)      #   calculate width
      text_lines.append( (w, line) ) #   add width and line to output list
      text_line = [word]             #   add word to next buffer

  # if the buffer is not empty at the end,
  #   add remining words to output list
  if len(text_line) > 0:
    w, h = font.getsize(' '.join(text_line))
    text_lines.append((w,' '.join(text_line)))

  return text_lines


def write_image(lines, out, **kargs):
  # get variables
  print(1)
  locations  = kargs.get('locations', [])
  size_const = kargs.get('size',      25)
  spacing    = kargs.get('spacing',    0)
  font_name  = kargs.get('font',      '')
  image_file = kargs.get('image',     '')
  regexes    = kargs.get('matches',   [])

  # load image
  img  = Image.open(image_file)
  draw = ImageDraw.Draw(img)

  # for each fillable box
  for text,location in zip(re.split('(\n|\\|)', lines), locations):
    # get location variables
    xpos,ypos,maxwidth,maxheight = location

    # reset size for each box
    size = size_const

    # calculate regex
    matches = []
    for pat in regexes:
      matches.append(re.search(pat, text) if pat else None)

    # bad idea, I know
    text  = eval("f'''" + kargs.get('format', '{text}') + "'''")

    # load font
    font = ImageFont.truetype(font_name, size)

    while True:
      # split into lines to fit in image
      lines = wrap_text(text, maxwidth, font)

      # if the lines do not fit in the box, resize the text(font)
      if not lines or len(lines)*(size+spacing) > maxheight:
        size -= 1
        font  = ImageFont.truetype(font_name, size)
      else:
        break

    # set spacing between lines
    size += spacing

    # calculate offset to center vertically
    ypos += (maxheight-len(lines)*size)/2

    # draw the lines
    for i,(line_width,msg) in enumerate(lines):
      line_pos = (posx+((maxwidth-line_width)/2), posy+size*i)
      try:
        draw.text(line_pos, msg, (0,0,0), font=font)
      except: #grey scale images I guess
        draw.text(line_pos, msg, 0, font=font)

  #save the image
  img.save(out)

class MemeGenerator:
  pattern = re.compile(r'(\w+)\s+(.*)$')
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/memes.json')

  @commands.command(pass_context=True, aliases=['memes'])
  async def meme(self, ctx, *, text : str):
    """
    Add text to images
    Usage: .meme <name> <text to add>

    Valid names so far:
      histy
      what
      not
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

    if 'font' not in cfg:
      cfg['font'] = self.conf['font']

    write_image(text, temp.name, **cfg)

    await self.bot.send_file(ctx.message.channel, temp.name)

    temp.close()


def setup(bot):
  m = MemeGenerator(bot)
  bot.add_cog(m)
