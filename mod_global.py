import os
import logging
import inspect
# import mod_misc

from inspect import currentframe, getframeinfo

# logger = mod_misc.initLogger(__name__)
global APP_NAME, IS_DEBUG, SERVER_VERSION
SERVER_VERSION = "1.2.1"
APP_NAME = "WCBOT"
if "DEBUG_MODE" in os.environ:
  IS_DEBUG = os.environ["DEBUG_MODE"] == "1"
else:
  IS_DEBUG = False
print("IS_DEBUG: " + str(IS_DEBUG))

# remove_path is optional paramater which is to remove additional path such '/ws'. See @app.route("/ws/<name>" in server.py
def server_entry(request, remove_path=None):
  # logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  # print(request.host_url)
  global APP_NAME, SERVER_URL, SERVER_URL_ROOT, IS_DEBUG
  # will produce https://..../dev
  url = request.url
  if url[:len(url)] == "/": # eliminate last "/"" if exists
    url = url[:len(url) - 1]
  url = url[:url.rfind('/')] # remove /***
  if remove_path is not None and url.endswith(remove_path):
    url = url[:len(url) - len(remove_path)]
  SERVER_URL = url + "/"
  SERVER_URL_ROOT = request.url_root
  if "DEBUG_MODE" in os.environ and "DEBUG_SERVER" in os.environ:
    if request.remote_addr == "127.0.0.1" or request.remote_addr == "localhost":
      SERVER_URL = os.environ["DEBUG_SERVER"]
  print("SERVER_URL=" + SERVER_URL)
