#!/usr/bin/env python3

import re
import asyncio
import logging
import os.path
import tempfile
import itertools
from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw
from includes.utils.format import error
from includes.utils.config import Config
from includes.utils import discord_helper as dh

logger = logging.getLogger('navi.memes')
zp = itertools.zip_longest

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
      if not line:                   #   if too long - no words
        return None                  #     return None to get a different font
      w, h = font.getsize(line)      #   calculate width
      if w > width:                  #   if single word was too long
        return None                  #     return none to get a different font
      text_lines.append( (w, line) ) #   add width and line to output list
      text_line = [word]             #   add word to next buffer

  # if the buffer is not empty at the end,
  #   add remining words to output list
  if len(text_line) > 0:
    w, h = font.getsize(' '.join(text_line))
    text_lines.append((w,' '.join(text_line)))

  return text_lines


def write_image(text_in, out, **kargs):
  # get variables
  logger.debug('kargs: '+ str(kargs))
  locs       = kargs.get('locations',         [])
  size_const = kargs.get('size',              25)
  spacing    = kargs.get('spacing',            0)
  font_name  = kargs.get('font',              '')
  image_file = kargs.get('image',             '')
  path       = kargs.get('path',              '')
  flags      = kargs.get('flags',             [])
  regexes    = kargs.get('matches',           [])
  formats    = kargs.get('formats',   ['{text}'])
  colour     = kargs.get('colour',     (0, 0, 0))
  border     = kargs.get('border',             0)

  if type(colour) == int:
    colour = (colour, colour, colour)

  tmp_loc = os.path.join(path, image_file)
  if os.path.exists(tmp_loc):
    image_file = tmp_loc

  tmp_loc = os.path.join(path, font_name)
  if os.path.exists(tmp_loc):
    font_name = tmp_loc

  logger.debug('opening: '+ image_file)
  # load image
  img  = Image.open(image_file)
  draw = ImageDraw.Draw(img, "RGB")

  # for each fillable box
  text_in = re.split('\\s*(\n|\\|)\\s*', text_in)
  for text,loc,style,flag in zp(text_in, locs, formats, flags):
    #just in case
    flag   = flag or ''
    style = style or '{text}'

    # get location variables
    xpos, ypos, maxwidth, maxheight = loc

    # reset size for each box
    size = size_const

    # calculate regex
    matches = []
    for pat in regexes:
      matches.append(re.search(pat, text) if pat else None)

    # bad idea, I know
    text  = eval("f'''" + style + "'''")

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
    logger.debug(f'drawing {lines}')
    for i,(line_width,msg) in enumerate(lines):
      if 'l' in flag:
        line_pos = (xpos, ypos+size*i)
      elif 'r' in flag:
        line_pos = (xpos+maxwidth-line_width, ypos+size*i)
      else:
        line_pos = (xpos+((maxwidth-line_width)/2), ypos+size*i)

      logger.debug(f'drawing at {line_pos}')
      #try:
      draw.text(line_pos, msg, colour, font=font)
      if border:
        line_pos[0] -= border
        line_pos[1] -= border
        tmpfont = ImageFont.truetype(font_name, size+border*2)
        colour  = tuple(255-x for x in colour)
        draw.text(line_pos, msg, colour, font=tmpfont)
      #except: # not grey scale images I guess
        #colour = sum(colour)//3
        #draw.text(line_pos, msg, colour, font=font)

  #save the image
  img.save(out)

class MemeGenerator:
  pattern = re.compile(r'(\w+)\s+(.*)$')
  def __init__(self, bot):
    self.bot    = bot
    self.conf   = Config('configs/memes.json')
    doc  = self.meme.__dict__['help']
    doc += '\n  '
    doc += '\n  '.join(self.conf.get('memes', {}).keys())

    self.meme.__dict__['help'] = doc

  @commands.command(pass_context=True, aliases=['memes'])
  async def meme(self, ctx, *, text : str):
    """
    Adds text to images

    Valid names so far:
    """

    match = MemeGenerator.pattern.match(text)
    name  = match.group(1).lower() if match else text
    text  = match.group(2) if match else ''
    text  = ' '.join(dh.remove_comments(text.split()))

    cfg = self.conf.get('memes', {}).get(name, None)

    if not cfg:
      await self.bot.say(error('Could not find image'))
      return
    if not text:
      await self.bot.say(error('Are you trying to get an empty image?'))
      return

    temp = tempfile.NamedTemporaryFile(suffix=".png")

    if 'font' not in cfg:
      cfg['font'] = self.conf.get('font', '')
    if 'path' not in cfg:
      cfg['path'] = self.conf.get('path', '')

    write_image(text, temp.name, **cfg)

    await self.bot.send_file(ctx.message.channel, temp.name)

    temp.close()


def setup(bot):
  m = MemeGenerator(bot)
  bot.add_cog(m)
