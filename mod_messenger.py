import os
import requests
import time
import logging
import json
import inspect
import mod_database
import mod_rivescript
import mod_wcbot
import mod_misc

from inspect import currentframe, getframeinfo

FBSRV_URL = "https://graph.facebook.com/v2.6/" # Messenger server URL

logger = mod_misc.initLogger(__name__)

class Messenger:
  def __init__(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    self.m_db = mod_database.Mdb()
    self.m_wcbot = mod_wcbot.WcBot()
    self.client_rec = None

  def getClientRecByFbPageId(self, fb_page_id):
    if self.client_rec is not None:
      return self.client_rec
    rec = self.m_db.findClientByFbPageId(fb_page_id)
    if rec is None:
      raise Exception("Client record not found by fb page id: {0}. Please check the page existance, or you may need to re-register it in the WcBot plugin.", fb_page_id)
    self.client_rec = rec
    return rec

  def webhookGet(self, query):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert query is not None
    # print(os.path.basename(getframeinfo(cf).filename) + ":" + str(cf.f_lineno) + ":" + inspect.stack()[0][3] + "()")
    if query.get("hub.mode") == "subscribe":
      verify_token = query.get("hub.verify_token")
      challenge = query.get("hub.challenge")
      # m_db = mod_database.Mdb()
      doc = self.m_db.findClientByVerifyToken(verify_token)
      if doc is None:
        return None
      else:
        curtime = int(time.time() * 1000) # equivalent to js Date.now()
        self.m_db.updateClientSubscribeDate(doc["client_id"], curtime)
        return challenge

  def webhookPost(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert request.json is not None
    entries = request.json["entry"]
    for entry in entries:
      for message in entry["messaging"]:
        if "message" in message:
          self.handleMessage(message)
        elif "postback" in message:
          self.handlePostback(message)
        else:
          raise Exception("Unhandled message type (either message nor postback)!")
    return "ok"

  def handleMessage(self, msg):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    # logger.debug(json.dumps(msg))
    assert msg is not None
    assert isinstance(msg["sender"]["id"], str)
    assert isinstance(msg["recipient"]["id"], str)
    assert self.m_wcbot is not None
    user_id = msg["sender"]["id"] # end user's messenger id
    fb_page_id = msg["recipient"]["id"] # target facebook page id
    message = None; sticker_id = None
    if "sticker_id" in msg["message"] is not None:
      sticker_id = msg["message"]["sticker_id"]
      logger.debug("user_id=%s, fb_page_id=%s, sticker_id=%d", user_id, fb_page_id, sticker_id)
    elif "text" in msg["message"] is not None:
      message = msg["message"]["text"]
      logger.debug("user_id=%s, fb_page_id=%s, message=%s", user_id, fb_page_id, message)
    client_rec = self.getClientRecByFbPageId(fb_page_id)
    access_token = client_rec["facebook_page"]["access_token"]
    sendMessengerTyping(access_token, user_id, True)
    time.sleep(3)
    usrvar_rec = self.m_db.findRsUserVarsByUserAndPage(user_id, fb_page_id)
    c_nls = mod_rivescript.Nls(user_id, fb_page_id)
    c_nls.setSubroutines(self.m_wcbot)
    if (usrvar_rec is not None):
      c_nls.setUserVars(user_id, json.loads(usrvar_rec["doc"]))
    if sticker_id is not None:
      reply = c_nls.getReply(user_id, sticker_id=sticker_id)
    elif message is not None:
      reply = c_nls.getReply(user_id, message=message)
    logger.debug("reply: %s", reply)
    if len(reply) > 0:
      if not self.m_wcbot.filterReplyCommand(reply, client_rec, c_nls, user_id):
        sendMessengerTextMessage(access_token, user_id, reply)
    usrvar_rs = c_nls.getUserVars(user_id)
    self.m_db.updateRsUserVars(user_id, fb_page_id, usrvar_rs)

  def handlePostback(self, msg):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert msg is not None
    assert isinstance(msg["sender"]["id"], str)
    assert isinstance(msg["recipient"]["id"], str)
    assert isinstance(msg["postback"]["payload"], str)
    user_id = msg["sender"]["id"] # end user's messenger id
    fb_page_id = msg["recipient"]["id"] # target facebook page id
    payload = msg["postback"]["payload"]
    logger.debug("user_id=%s, fb_page_id=%s, message=%s", user_id, fb_page_id, payload)
    client_rec = self.getClientRecByFbPageId(fb_page_id)
    access_token = client_rec["facebook_page"]["access_token"]
    sendMessengerTyping(access_token, user_id, True)
    time.sleep(3)
    usrvar_rec = self.m_db.findRsUserVarsByUserAndPage(user_id, fb_page_id)
    c_nls = mod_rivescript.Nls(user_id, fb_page_id)
    c_nls.setSubroutines(self.m_wcbot)
    if (usrvar_rec is not None):
      c_nls.setUserVars(user_id, json.loads(usrvar_rec["doc"]))
    if not self.m_wcbot.filterPostbackPayload(payload, client_rec, c_nls, user_id):
      logger.warn("%s-%s: Unhandled postback payload: %s", str(currentframe().f_lineno), inspect.stack()[0][3], payload)
      # any payload needs to handle in messenger webhook level?
    usrvar_rs = c_nls.getUserVars(user_id)
    self.m_db.updateRsUserVars(user_id, fb_page_id, usrvar_rs)

###############################################################################
# Messenger Send API functions
###############################################################################

def _checkApiError(resp):
  if resp.status_code != 200:
    err_obj = json.loads(resp.text)["error"]
    raise Exception("Messenger API error: " + err_obj["message"])
    return False
    # logger.error(.error)
  else:
    return True

def sendMessengerTyping(access_token, user_id, ison):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  assert isinstance(access_token, str)
  assert isinstance(user_id, str)
  cmd = "typing_on"
  if not ison:
    cmd = "typing_off"
  data = {
    "recipient": { "id": user_id },
    "sender_action": cmd
  }
  qs = "access_token=" + access_token
  url = FBSRV_URL + "me/messages?" + qs
  # logger.debug("url = %s", url)
  return _checkApiError(requests.post(url, json=data))

def sendMessengerTextMessage(access_token, user_id, text):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  assert isinstance(access_token, str)
  assert isinstance(user_id, str)
  assert isinstance(text, str)
  data = {
    "recipient": { "id": user_id },
    "message": { "text": text }
  }
  qs = "access_token=" + access_token
  url = FBSRV_URL + "me/messages?" + qs
  # logger.debug("url = %s", url)
  return _checkApiError(requests.post(url, json=data))

def getMessengerUserProfile(access_token, user_id):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  assert isinstance(access_token, str)
  assert isinstance(user_id, str)
  param = {
    "access_token": access_token,
    "fields": "first_name,last_name,locale,timezone,gender"
  }
  result = requests.get(FBSRV_URL + user_id, params=param)
  return result.json()

def sendMessengerImagesMessage(access_token, user_id, images):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  assert isinstance(access_token, str)
  assert isinstance(user_id, str)
  assert images is not None
  data = {
    "recipient": { "id": user_id },
    "message": {
      "attachment": {
        "type": 'template',
        "payload": {
          "template_type": "generic",
          "elements": images
        }
      }
    }
  }
  qs = "access_token=" + access_token
  url = FBSRV_URL + "me/messages?" + qs
  # logger.debug("url = %s", url)
  return _checkApiError(requests.post(url, json=data))

"""
"title": 'Order Details',
"type": "postback" | "web_url"
"url": "???" or "payload": "???"
"""
def sendMessengerButtonMessage(access_token, user_id, prompt, buttons):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  assert isinstance(access_token, str)
  assert isinstance(user_id, str)
  assert isinstance(prompt, str)
  assert buttons is not None
  data = {
    "recipient": { "id": user_id },
    "message": {
      "attachment": {
        "type": 'template',
        "payload": {
          "template_type": "button",
          "text": prompt,
          "buttons": buttons
        }
      }
    }
  }
  qs = "access_token=" + access_token
  url = FBSRV_URL + "me/messages?" + qs
  # logger.debug("url = %s", url)
  return _checkApiError(requests.post(url, json=data))

def getMessengerWhitelistedDomain(access_token):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  assert isinstance(access_token, str)
  param = {
    "access_token": access_token,
    "fields": "whitelisted_domains"
  }
  result = requests.get(FBSRV_URL + "me/messenger_profile", params=param)
  result = result.json()["data"]
  if len(result) == 0:
    return []
  elif "whitelisted_domains" in result[0]:
    return result[0]["whitelisted_domains"]
  else:
    return []

def setMessengerProfile(access_token, profile):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  assert isinstance(access_token, str)
  assert profile is not None
  qs = "access_token=" + access_token
  url = FBSRV_URL + "me/messenger_profile?" + qs
  return _checkApiError(requests.post(url, json=profile))

def setupWhiteListDomains(access_token, domains):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  assert isinstance(access_token, str)
  assert isinstance(domains, list)
  new_domains = []
  for domain in domains:
    if "localhost" not in domain and "127.0." not in domain:
      if not domain.endswith('/'):
        domain += '/'
      new_domains.append(domain)
  if len(new_domains) > 0:
    # Append existing domains
    exist_domains = getMessengerWhitelistedDomain(access_token)
    for domain in exist_domains:
      if domain not in new_domains:
        new_domains.append(domain)
    # print("final new_domains:")
    # print(new_domains)
    profile = {
      "whitelisted_domains": new_domains
    }
    setMessengerProfile(access_token, profile)
  return True
