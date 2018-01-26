import os
import logging
import inspect
import rivescript

import mod_misc

from inspect import currentframe, getframeinfo

logger = mod_misc.initLogger(__name__)

logger.debug("rivescript module loaded")

class Nls:
  def __init__(self, user_id, fb_page_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    rsbot = rivescript.RiveScript(utf8=True)
    # rsbot = RiveScript()
    rsbot.load_directory("./rsBrainFiles")
    rsbot.sort_replies()
    rsbot.set_uservar(user_id, "fb_page_id", fb_page_id)
    self.rsbot = rsbot

  def getReply(self, userId, msg):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(userId, str)
    assert isinstance(msg, str)
    return self.rsbot.reply(userId, msg)

  def getUserVars(self, userId):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(userId, str)
    return self.rsbot.get_uservars(userId)

  def setUserVar(self, userId, name, value):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(userId, str)
    assert isinstance(name, str)
    self.rsbot.set_uservar(userId, name, value)

  def setUserVars(self, userId, usr_vars):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(userId, str)
    assert usr_vars is not None
    self.rsbot.set_uservars(userId, usr_vars)

  def setSubroutines(self, wc_bot):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert wc_bot is not None
    self.rsbot.set_subroutine('find_products', wc_bot.cbFindProducts)


