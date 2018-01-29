import logging
import inspect
import mod_misc

from inspect import currentframe, getframeinfo

logger = mod_misc.initLogger(__name__)
APP_NAME = "WCBOT"

# remove_path is optional paramater which is to remove additional path such '/ws'. See @app.route("/ws/<name>" in server.py
def server_entry(request, remove_path=None):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  # print(request.host_url)
  global SERVER_URL, SERVER_URL_ROOT
  # will produce https://..../dev
  url = request.url
  if url[:len(url)] == "/": # eliminate last "/"" if exists
    url = url[:len(url) - 1]
  url = url[:url.rfind('/')] # remove /***
  if remove_path is not None and url.endswith(remove_path):
    url = url[:len(url) - len(remove_path)]
  SERVER_URL = url + "/"
  SERVER_URL_ROOT = request.url_root
  # For personal PC debugging only :)
  if "localhost" in SERVER_URL or "127.0.0" in SERVER_URL:
    SERVER_URL = "https://dev-5000.simonho.net/" # Messenger API friendly
  logger.info("SERVER_URL=" + SERVER_URL)