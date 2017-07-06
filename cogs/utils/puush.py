import puush
import os
from cogs.utils import find as azfind
from cogs.utils.config import Config
import requests
import tempfile
import hashlib

conf = Config('configs/az.json')
if 'path' not in conf:
  conf['path'] = input('Enter dir to search for: ')

if 'key' not in conf:
  conf['key'] = input('Enter puush api key: ')

account = puush.Account(conf['key'])

if 'images' not in conf or type(conf['images']) != dict:
  conf['images'] = {}

account = puush.Account(conf['key'])

def upload(paths, p=None):
  if not paths:
    return []
  if not p:
    p = get_hash(paths[0])
  urls = ''
  for path in paths:
    for i in range(3):
      try:
        image = account.upload(path)
        if image and image.url:
          urls += image.url + '\n'
          break
      except ValueError:
        pass
    else:
      return 'could not upload image'
  conf['images'][p] = {'url':urls}
  conf.save()
  return urls

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
