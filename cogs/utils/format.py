def error(text):
  return "\N{NO ENTRY SIGN} {}".format(text)

def warning(text):
  return "\N{WARNING SIGN} {}".format(text)


def info(text):
  return "\N{INFORMATION SOURCE} {}".format(text)

def ok(text=''):
  return "\N{OK HAND SIGN} {}".format(text)

def question(text):
  return "\N{BLACK QUESTION MARK ORNAMENT} {}".format(text)

def bold(text):
  return "**{}**".format(text)

def code(text, lang=""):
  return "```{}\n{}\n```".format(lang, text)

def inline(text):
  return "`{}`".format(text)

def italics(text):
  return "*{}*".format(text)

def strikethrough(text):
  return "~~{}~~".format(text)

def underline(text):
  return "__{}__".format(text)

def escape_mentions(text):
  return text.replace('@', '@\u200b')

def escape(text, mentions=False):
  if mentions:
    text = escape_mentions(text)
  text = text.replace("`", "\\`") \
             .replace("*", "\\*") \
             .replace("_", "\\_") \
             .replace("~", "\\~")
  return text

