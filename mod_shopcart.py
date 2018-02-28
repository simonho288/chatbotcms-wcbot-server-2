import inspect

import mod_misc
import mod_messenger
import mod_woocommerce
import mod_database

from inspect import currentframe, getframeinfo

logger = mod_misc.initLogger(__name__)

class ShoppingCart:
  def __init__(self, user_id, fb_page_id, cart_items=None, order_id=None):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    self.user_id = user_id
    self.fb_page_id = fb_page_id
    self.doc = None
    self.m_db = mod_database.Mdb()
    if cart_items is not None or order_id is not None:
      self.doc = {}
      if cart_items is not None:
        self.doc["cart_items"] = cart_items
      if order_id is not None:
        self.doc["order_id"] = order_id

  def getRecord(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    return self.doc

  def getServerSettings(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    return self.doc["server_settings"]

  # def saveServerSettings(self, ssts):
  #   logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  #   assert ssts is not None
  #   self.doc["server_settings"] = ssts

  def saveToDatabase(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(self.user_id, str)
    assert isinstance(self.fb_page_id, str)
    if "ship_info" in self.doc and self.doc["ship_info"] != None:
      self.doc["ship_info"]["cost"] = str(self.doc["ship_info"]["cost"])
    self.m_db.upsertShopcart(self.user_id, self.fb_page_id, self.doc)

  def loadFromDatabase(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(self.user_id, str)
    assert isinstance(self.fb_page_id, str)
    result = self.m_db.findShopcartByUserAndFbpageid(self.user_id, self.fb_page_id)
    if result is not None and "doc" in result:
      self.doc = result["doc"]
      # self.doc = djson.loads(result["doc"])
      # self.cart_items = rec["cart_items"]
      # self.order_id = order_id
      # self.server_settings = rec["cart_items"]
      # self.input_info = rec["input_info"]
      # self.ship_info = rec["ship_info"]
    
  def appendProduct(self, product):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert product is not None
    cart_items = []
    if self.doc is not None and "cart_items" in self.doc:
      cart_items = self.doc["cart_items"]
    for item in cart_items:
      if item["product_id"] == product["id"]:
        item["qty"] += 1
        return
    image = ""
    if len(product["images"]) > 0:
      image = product["images"][0]["src"]
    cart_items.append({
      "product_id": product["id"],
      "name": product["name"],
      "qty": 1,
      "unit_price": product["price"],
      "image": image
    })
    if self.doc is None:
      self.doc = {
        "cart_items": cart_items,
        "order_id": None,
        "server_settings": None,
        "input_info": None, # persist input info
        "ship_info": None, # persist ship info
      }

  def createWcOrder(self, url, consumer_key, consumer_secret):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(url, str)
    assert isinstance(consumer_key, str)
    assert isinstance(consumer_secret, str)
    assert self.doc is not None
    assert self.doc["cart_items"] is not None
    assert self.doc["input_info"] is not None
    assert self.doc["input_info"]["billing"] is not None
    assert self.doc["input_info"]["billing"]["first_name"] is not None
    assert self.doc["input_info"]["billing"]["last_name"] is not None
    assert self.doc["input_info"]["billing"]["email"] is not None
    assert self.doc["input_info"]["billing"]["phone"] is not None
    assert self.doc["input_info"]["billing"]["address1"] is not None
    # assert self.doc["input_info"]["billing"]["address2"] is not None
    assert self.doc["input_info"]["billing"]["city"] is not None
    assert self.doc["input_info"]["billing"]["state"] is not None
    assert self.doc["input_info"]["billing"]["postal"] is not None
    assert self.doc["input_info"]["billing"]["country"] is not None
    assert self.doc["input_info"]["shipping"] is not None
    assert self.doc["input_info"]["shipping"]["first_name"] is not None
    assert self.doc["input_info"]["shipping"]["last_name"] is not None
    assert self.doc["input_info"]["shipping"]["address1"] is not None
    # assert self.doc["input_info"]["shipping"]["address2"] is not None
    assert self.doc["input_info"]["shipping"]["city"] is not None
    assert self.doc["input_info"]["shipping"]["state"] is not None
    assert self.doc["input_info"]["shipping"]["postal"] is not None
    assert self.doc["input_info"]["shipping"]["country"] is not None
    m_wc = mod_woocommerce.Wc(url, consumer_key, consumer_secret)
    return m_wc.createOrder(self.doc["input_info"], self.doc["cart_items"])

  def saveServerSettings(self, sts):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert sts is not None
    if self.doc is not None:
      self.doc["server_settings"] = sts
    self.m_db.updateShopcartServerSettings(self.user_id, self.fb_page_id, sts)

  def getCartItem(self):
    if self.doc is None:
      return None
    return self.doc["cart_items"]

  def saveCartItems(self, items):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert items is not None
    if self.doc is not None:
      self.doc["cart_items"] = items
    self.m_db.updateShopcartCartitems(self.user_id, self.fb_page_id, items)

  def saveCartInputinfo(self, iinfo):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert iinfo is not None
    iinfo = mod_misc.remove_empty_string(iinfo)
    if self.doc is not None:
      self.doc["input_info"] = iinfo
    self.m_db.updateShopcartInputinfo(self.user_id, self.fb_page_id, iinfo)

  def saveCartShipinfo(self, sinfo):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert sinfo is not None
    if self.doc is not None:
      self.doc["ship_info"] = sinfo
    self.m_db.updateShopcartShipinfo(self.user_id, self.fb_page_id, sinfo)

  def saveOrderPool(self, orderpool):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert orderpool is not None
    if self.doc is not None:
      self.doc["order_pool"] = orderpool
    self.m_db.updateShopcartOrderpool(self.user_id, self.fb_page_id, orderpool)


