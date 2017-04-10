import puush
import os
from cogs.utils import find as azfind
from cogs.utils.config import Config
import requests
import tempfile

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
  tempfiles = []
  if not p:
    p = paths[0]
  urls = ''
  for path in paths:
    if path.startswith('http'):
      ext = path.rpartition('.')[2].lower()
      t   = tempfile.NamedTemporaryFile(suffix=ext)
      response = requests.get(path, stream=True, verify=False)
      t.write(response.raw.read())
      path = t.name
      tempfiles.append(t)
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
  for t in tempfiles:
    t.close()
  return urls

def get_url(path):
  if path in conf['images']:
    urls = conf['images'][path]['url']
    try:
      if confirm_img(urls):
        return urls
    except:
      pass

  out = ''
  if path.rpartition('.')[2].lower() in ['zip', 'cbz']:
    files = azfind.extract(path)
    if files:
      out = upload(files, path)
      for f in files:
        os.remove(f)
      os.rmdir(os.path.dirname(files[0]))
    else:
      out = 'archive found... but empty'
    return out
  else:
    return upload([path])

def confirm_img(urls):
  for url in urls.split('\n'):
    if url and requests.get(url, timeout=2).status_code != 200:
      return False
  return True
