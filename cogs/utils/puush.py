import puush
import os
from cogs.utils import find as azfind
from cogs.utils.config import Config
import requests
import tempfile
import hashlib

# open config and set up puush
conf = Config('configs/az.json')
if 'path' not in conf:
  conf['path'] = input('Enter dir to search for: ')
if 'images' not in conf or type(conf['images']) != dict:
  conf['images'] = {}
if 'key' not in conf:
  conf['key'] = input('Enter puush api key: ')
account = puush.Account(conf['key'])

def upload(paths, h=None):
  '''
  given a list of file paths, upload all files to push and return urls

  paths: list of paths to files to upload
  h:     hash to use when remembering upload urls

  If h is not given,
    the file located at the first path will be hashed and used as h
  '''
  if not paths: # no file -> done
    return ''

  if not h: #no hash - calulate from first file
    h = get_hash(paths[0])

  urls = ''
  for path in paths:                  # for each file
    for i in range(3):                #   try at most 3 times
      try:
        image = account.upload(path)  #   to upload it
        if image and image.url:
          urls += image.url + '\n'
          break
      except:
        pass
    else:                             # if failed to upload after 3 attempts
      return 'could not upload image' #   return error string
  conf['images'][h] = {'url':urls}    # if success,
  conf.save()                         #   save urls under hash
  return urls                         #   and return

def get_url(path):
  tempfiles = []
  if path.startswith('http'):
    t   = tempfile.NamedTemporaryFile(suffix=".jpg")
    response = requests.get(path, stream=True, verify=False)
    t.write(response.raw.read())
    path = t.name
    tempfiles.append(t)

  str_hash = get_hash(path)

  if str_hash in conf['images']:
    urls = conf['images'][str_hash]['url']
    try:
      if confirm_img(urls):
        for t in tempfiles:
          t.close()
        return urls
    except:
      pass

  out = ''
  if path.rpartition('.')[2].lower() in ['zip', 'cbz']:
    files = azfind.extract(path)
    if files:
      out = upload(files, str_hash)
      for f in files:
        os.remove(f)
      os.rmdir(os.path.dirname(files[0]))
    else:
      out = 'archive found... but empty'
  else:
    out = upload([path], str_hash)

  for t in tempfiles:
    t.close()
  return out

def confirm_img(urls):
  for url in urls.split('\n'):
    if url and requests.get(url, timeout=2).status_code != 200:
      return False
  return True

def get_hash(path):
  hasher = hashlib.md5()
  with open(path, 'rb') as f:
    buf = f.read()
    hasher.update(buf)
  return hasher.hexdigest()
