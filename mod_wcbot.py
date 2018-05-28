import os
import datetime # datetime.datetime.utcnow()
import time
import pymongo
import inspect
import re
import sys, traceback

import mod_misc
import mod_global
import mod_messenger
import mod_woocommerce
import mod_shopcart
import mod_database

from inspect import currentframe, getframeinfo

# Constant variables
# Display message
MSG_NO_MORE_PRODUCTS = "No more products"
MSG_NO_MORE_CATEGORIES = "No more categories"
MSG_EMPTY_CART = "The shopping cart is empty!"
MSG_NO_HOT_PRODUCTS = "Sorry, no hot products today!"
MSG_EMPTY_CART_DONE = "The shopping cart is empty now"
MSG_BROWSE_CART = "There is {0} {1} in your shopping cart. You can browse it now"
MSG_CONNECT_ERROR = "Oops! There is connection problem with WooCommerce server :( Please report to admin!"
MSG_NO_ORDERS_FOUND = "You have no orders in our record"
# Messenger platform payload
PAYLOAD_GETSTARTED = "GETSTARTED" # Messenger predefined
# PAYLOAD_SHOWCATEGORY = "PLSHOWCATEGORY" # page_no, category_id
PAYLOAD_LISTPRODUCTS = "PLLISTPRODUCTS" # page_no, categroy_id, tag_id
PAYLOAD_HOTPRODUCTS = "PLHOTPRODUCTS"
PAYLOAD_LISTCATEGORIES = "PLLISTCATEGORIES" # page no
PAYLOAD_SHOWPRODUCT = "PLSHOWPRODUCT" # product id
PAYLOAD_ADDTOCART = "PLADDTOCART" # product_id
PAYLOAD_SHOWHINTS = "PLSHOWHINTS"
PAYLOAD_VIEWCART = "PLVIEWCART"
PAYLOAD_FINDPRODUCTS = "PLFINDPRODUCTS" # keyword, page no
PAYLOAD_PRODUCTS_PRICE_BETWEEN = "PLPRODUCTSPRICEBETWEEN"
PAYLOAD_PRODUCTS_PRICE_MIN = "PLPRODUCTSPRICEMIN"
PAYLOAD_PRODUCTS_PRICE_MAX = "PLPRODUCTSPRICEMAX"
PAYLOAD_ORDERDETAILS = "PLORDERDETAILS" # order_id
PAYLOAD_QUICKHELP = "PLQUICKHELP"
PAYLOAD_PRODUCT_VARIATION = "PLPRODUCTVAR"
PAYLOAD_LISTORDERS = "PLLISTORDERS"
# Rivescript variable name
RSVAR_CUR_PRODUCT = "wcCurrentProduct"
RSVAR_FBUSER_PROFILE = "fbUserProfile"
RSVAR_CUR_VAR_SELECTED = "wcCurVarSelected"
CR = "\n"
ITEMS_PER_PAGE = 10

logger = mod_misc.initLogger(__name__)

class WcBot:
  def __init__(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    self.m_woocom = None # mod_woocommerce
    self.raw_gensts = None # Raw general settings
    self.currcy_sts = None # Extracted general settings

  def filterReplyCommand(self, reply, client_rec, m_nls, user_id):
    """
    Handles WcBot specified command from rivescript reply (such as _jsShowQuickHelp_)
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(reply, str)
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    acc_tok = client_rec["facebook_page"]["access_token"]
    try:
      if reply == "_jsShowVersion_":
        return self.doShowVersion(client_rec, m_nls, user_id)
      elif reply == "_jsShowQuickHelp_":
        return self.PLQuickHelp(client_rec, m_nls, user_id)
      elif reply == "_jsListProducts_":
        return self.PLListProducts(client_rec, m_nls, user_id)
      elif reply == "_jsListHotProducts_":
        return self.PLHotProducts(client_rec, m_nls, user_id, page_no=1)
      elif reply == "_jsListCategories_":
        return self.doListCategories(client_rec, m_nls, user_id, page_no=1)
      elif reply == "_jsViewCart_":
        return self.PLViewCart(client_rec, m_nls, user_id)
      elif reply == "_jsListAllOrders_":
        return self.doListAllOrders(client_rec, m_nls, user_id)
      elif reply == "_jsShowStoreName_":
        return self.doShowStoreName(client_rec, m_nls, user_id)
      elif reply == "_jsShowStoreUrl_":
        return self.doShowStoreUrl(client_rec, m_nls, user_id)
      elif reply == "_jsShowWcbotProductInfo_":
        return self.doShowWcbotProductInfo(client_rec, m_nls, user_id)
      else:
        if self.doAnswerQuickQuestion(client_rec, m_nls, user_id, reply):
          return True
    except Exception as ex:
      # the problem maybe: woocommerce connection problem, php not started
      traceback.print_exc(file=sys.stdout)
      out_msg = "Exp: {0}...".format(str(ex)[:60])
      mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
      return True
    return False

  def filterPostbackPayload(self, payload, client_rec, m_nls, user_id):
    """
    Handles postback payload from messenger
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payload, str)
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    payloads = payload.split("_")
    payload_cmd = payloads[0]
    if self.m_woocom is None:
      rec_wc = client_rec["woocommerce"]
      self.m_woocom = mod_woocommerce.Wc(rec_wc["url"], rec_wc["consumer_key"], rec_wc["consumer_secret"])
    if payload_cmd == PAYLOAD_SHOWPRODUCT:
      return self.PLViewProductDetail(payloads[1], client_rec, m_nls, user_id)
    elif payload_cmd == PAYLOAD_ADDTOCART:
      return self.PLAddProductToCart(payloads[1], client_rec, m_nls, user_id)
    elif payload_cmd == PAYLOAD_LISTPRODUCTS:
      page_no = 1
      if len(payloads) > 1: page_no = int(payloads[1])
      catg_id = None
      if len(payloads) > 2: catg_id = payloads[2]
      return self.PLListProducts(client_rec, m_nls, user_id, page_no=page_no, catg_id=catg_id)
    elif payload_cmd == PAYLOAD_HOTPRODUCTS:
      page_no = 1
      if len(payloads) > 1: page_no = int(payloads[1])
      return self.PLHotProducts(client_rec, m_nls, user_id, page_no=page_no)
    elif payload_cmd == PAYLOAD_VIEWCART:
      return self.PLViewCart(client_rec, m_nls, user_id)
    elif payload_cmd == PAYLOAD_QUICKHELP:
      return self.PLQuickHelp(client_rec, m_nls, user_id)
    elif payload_cmd == PAYLOAD_FINDPRODUCTS:
      return self.PLGetProductsByName(client_rec, user_id, int(payloads[2]), payloads[1])
    elif payload_cmd == PAYLOAD_ORDERDETAILS:
      return self.PLOrderDetails(client_rec, user_id, payloads[1])
    elif payload_cmd == PAYLOAD_GETSTARTED:
      return self.PLGetStarted(client_rec, m_nls, user_id)
    elif payload_cmd == PAYLOAD_PRODUCTS_PRICE_MAX:
      price = payloads[1]
      return self.PLGetProductsByPrice(client_rec, user_id, int(payloads[2]), "The products which the price under " + price, max_price=price)
    elif payload_cmd == PAYLOAD_PRODUCTS_PRICE_MIN:
      price = payloads[1]
      return self.PLGetProductsByPrice(client_rec, user_id, int(payloads[2]), "The products which the price above " + price, min_price=price)
    elif payload_cmd == PAYLOAD_PRODUCTS_PRICE_BETWEEN:
      prices = payloads[1].split("&")
      min_price = prices[0]
      max_price = prices[1]
      return self.PLGetProductsByPrice(client_rec, user_id, int(payloads[2]), "The products which the price between " + min_price + " and " + max_price, min_price=min_price, max_price=max_price)
    elif payload_cmd == PAYLOAD_PRODUCT_VARIATION:
      product_id = payloads[1]
      page = payloads[2]
      return self.PLShowProductVariation(client_rec, m_nls, user_id, product_id, page)
    elif payload_cmd == PAYLOAD_LISTCATEGORIES:
      page_no = 1
      if len(payloads) > 1: page_no = int(payloads[1])
      return self.doListCategories(client_rec, m_nls, user_id, page_no)
    elif payload_cmd == PAYLOAD_LISTORDERS:
      return self.doListAllOrders(client_rec, m_nls, user_id)
    return False

  # called from rivescript subsubroutine by trigger 'rs_find_products"
  def rsSubFindProducts(self, rs, args):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    user_id = rs.current_user()
    fb_page_id = rs.get_uservar(user_id, "fb_page_id")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert len(args) > 0
    mdb = mod_database.Mdb()
    client_rec = mdb.findClientByFbPageId(fb_page_id)
    name = " ".join([str(s) for s in args])
    try:
      self.PLGetProductsByName(client_rec, user_id, 1, name)
    except Exception as exp:
      traceback.print_exc(file=sys.stdout)

  def rsSubProductsPriceBelow(self, rs, args):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    user_id = rs.current_user()
    fb_page_id = rs.get_uservar(user_id, "fb_page_id")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert len(args) > 0
    mdb = mod_database.Mdb()
    client_rec = mdb.findClientByFbPageId(fb_page_id)
    price = args[0]
    if not mod_misc.isNumeric(price):
      msg = "Your price is incorrect! Please try again."
      mod_messenger.sendMessengerTextMessage(client_rec["facebook_page"]["access_token"], user_id, msg)
      return
    try:
      self.PLGetProductsByPrice(client_rec, user_id, 1, "The products which the price under " + price, max_price=price)
    except Exception as exp:
      traceback.print_exc(file=sys.stdout)

  def rsSubProductsPriceAbove(self, rs, args):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    user_id = rs.current_user()
    fb_page_id = rs.get_uservar(user_id, "fb_page_id")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert len(args) > 0
    mdb = mod_database.Mdb()
    client_rec = mdb.findClientByFbPageId(fb_page_id)
    price = args[0]
    if not mod_misc.isNumeric(price):
      msg = "Your price is incorrect! Please try again."
      mod_messenger.sendMessengerTextMessage(client_rec["facebook_page"]["access_token"], user_id, msg)
      return
    try:
      self.PLGetProductsByPrice(client_rec, user_id, 1, "The products which the price above " + price, min_price=price)
    except Exception as exp:
      traceback.print_exc(file=sys.stdout)

  def rsSubProductsPriceRange(self, rs, args):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    user_id = rs.current_user()
    fb_page_id = rs.get_uservar(user_id, "fb_page_id")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert len(args) > 1
    mdb = mod_database.Mdb()
    client_rec = mdb.findClientByFbPageId(fb_page_id)
    min_price = args[0]
    max_price = args[1]
    if not mod_misc.isNumeric(min_price) or not mod_misc.isNumeric(max_price):
      msg = "Your price is incorrect! Please try again."
      mod_messenger.sendMessengerTextMessage(client_rec["facebook_page"]["access_token"], user_id, msg)
      return
    if float(min_price) > float(max_price): # swap the prices
      t = min_price
      min_price = max_price
      max_price = t
    try:
      self.PLGetProductsByPrice(client_rec, user_id, 1, "The products which the price between " + min_price + " and " + max_price, min_price=min_price, max_price=max_price)
    except Exception as exp:
      traceback.print_exc(file=sys.stdout)

  def parseGeneralSetting(self, gen_sts):
    """
    Extract the setting return from WooCommerce settings/general api
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert gen_sts is not None

    cur = mod_misc.wcGeneralSettingLookup(gen_sts, "woocommerce_currency")
    if cur is None:
      raise Exception("Can't retrieve WooCommerce settings. Is the REST API access authorized?")
    cur_pos = mod_misc.wcGeneralSettingLookup(gen_sts, "woocommerce_currency_pos")
    thou_sep = mod_misc.wcGeneralSettingLookup(gen_sts, "woocommerce_price_thousand_sep")
    dec_sep = mod_misc.wcGeneralSettingLookup(gen_sts, "woocommerce_price_decimal_sep")
    num_dec = mod_misc.wcGeneralSettingLookup(gen_sts, "woocommerce_price_num_decimals")

    self.currcy_sts = {
      "value": cur["value"],
      "position": cur_pos["value"],
      "thousand_sep": thou_sep["value"],
      "decimal_sep": dec_sep["value"],
      "num_decimal": num_dec["value"]
    }

  def doShowVersion(self, client_rec, m_nls, user_id):
    """
    Show internal version number
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    msg = mod_global.APP_NAME + " ver: " + mod_global.SERVER_VERSION
    mod_messenger.sendMessengerTextMessage(client_rec["facebook_page"]["access_token"], user_id, msg)
    return True

  # def PLQuickHelp(self, client_rec, m_nls, user_id):
  #   """
  #   Handle Payload: Handles rivescript _jsShowQuickHelp_ reply (see cms_wc.rive)
  #   """
  #   logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  #   assert client_rec is not None
  #   assert m_nls is not None
  #   assert isinstance(user_id, str)
  #   msg = "* QUICK HELP *" + CR + "You can send me the command like:" + CR + "  show products" + CR + "  show hot products" + CR + "  show category" + CR + "  show all order" + CR + "  view shopping cart" + CR + "  find product tshirt" + CR + "  product price under 30" + CR + "  product price between 10 and 20"
  #   mod_messenger.sendMessengerTextMessage(client_rec["facebook_page"]["access_token"], user_id, msg)
  #   return True
  def PLQuickHelp(self, client_rec, m_nls, user_id):
    """
    Handle Payload: Handles rivescript _jsShowQuickHelp_ reply (see cms_wc.rive)
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    acc_tok = client_rec["facebook_page"]["access_token"]
    fb_page_id = client_rec["fb_page_id"]
    if self.m_woocom is None:
      rec_wc = client_rec["woocommerce"]
      self.m_woocom = mod_woocommerce.Wc(rec_wc["url"], rec_wc["consumer_key"], rec_wc["consumer_secret"])
    # actions = ['show products', 'hot products', 'show categories']
    # actions.append('show all orders')
    # actions.append('view shopping cart')
    replies = [{
      "content_type": "text",
      "title": "Show products",
      "payload": "{0}_1".format(PAYLOAD_LISTPRODUCTS),
    }, {
      "content_type": "text",
      "title": "Hot products",
      "payload": "{0}_1".format(PAYLOAD_HOTPRODUCTS),
    }, {
      "content_type": "text",
      "title": "Show categories",
      "payload": "{0}_{1}".format(PAYLOAD_LISTCATEGORIES, 1)
    }]
    # Determine to show "View cart"
    m_shopcart = mod_shopcart.ShoppingCart(user_id, client_rec["fb_page_id"])
    m_shopcart.loadFromDatabase()
    items = m_shopcart.getCartItem()
    if len(items) > 0:
      replies.append({
        "content_type": "text",
        "title": "View cart",
        "payload": PAYLOAD_VIEWCART,
      })
    # Determine to show "View orders"
    m_db = mod_database.Mdb()
    orders = m_db.getOrderByUserAndFbpage(user_id, fb_page_id)
    if orders is not None and len(orders) > 0:
      replies.append({
        "content_type": "text",
        "title": "My orders",
        "payload": PAYLOAD_LISTORDERS,
      })

    # Show all in messenger    
    msg = "* QUICK HELP *" + CR + "Please select below action, or send me the commands like:" + CR + "  find product tshirt" + CR + "  product price under 30" + CR + "  product price between 10 and 20"
    mod_messenger.sendMessengerQuickReplies(acc_tok, user_id, msg, replies)
    return True

  def PLListProducts(self, client_rec, m_nls, user_id, page_no=1, catg_id=None, tag_id=None):
    """
    Handle Payload: Handles rivescript _jsListProducts_ (see cms_wc.rive)
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    assert isinstance(page_no, int)
    acc_tok = client_rec["facebook_page"]["access_token"]
    if self.m_woocom is None:
      rec_wc = client_rec["woocommerce"]
      self.m_woocom = mod_woocommerce.Wc(rec_wc["url"], rec_wc["consumer_key"], rec_wc["consumer_secret"])
    if self.raw_gensts is None: # needs for formatting currency
      self.raw_gensts = self.m_woocom.getGeneralSetting()
      self.parseGeneralSetting(self.raw_gensts)
    if catg_id is not None:
      products = self.m_woocom.getProductsList(ITEMS_PER_PAGE, page_no, category_id=catg_id)
    else:
      products = self.m_woocom.getProductsList(ITEMS_PER_PAGE, page_no)
    mgr_prods = self.productsToMessengerImages(products, PAYLOAD_LISTPRODUCTS, page_no)
    mod_messenger.sendMessengerImagesMessage(acc_tok, user_id, mgr_prods)
    return True

  def PLHotProducts(self, client_rec, m_nls, user_id, page_no):
    """
    Handle Payload: Handles rivescript _jsListHotProducts_ reply (see cms_wc.rive)
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    assert isinstance(page_no, int)
    acc_tok = client_rec["facebook_page"]["access_token"]
    if self.m_woocom is None:
      rec_wc = client_rec["woocommerce"]
      self.m_woocom = mod_woocommerce.Wc(rec_wc["url"], rec_wc["consumer_key"], rec_wc["consumer_secret"])
    if self.raw_gensts is None: # needs for formatting currency
      self.raw_gensts = self.m_woocom.getGeneralSetting()
      self.parseGeneralSetting(self.raw_gensts)
    tagrs = self.m_woocom.getTagBySlug("hot")
    if len(tagrs) > 0 and tagrs[0]["count"] > 0:
      tagr = tagrs[0]
      products = self.m_woocom.getProductsList(ITEMS_PER_PAGE, page_no, tag_id=tagr["id"])
      mgr_prods = self.productsToMessengerImages(products, PAYLOAD_HOTPRODUCTS, page_no)
      mod_messenger.sendMessengerImagesMessage(acc_tok, user_id, mgr_prods)
    else:
      mod_messenger.sendMessengerTextMessage(acc_tok, user_id, MSG_NO_HOT_PRODUCTS)
    return True

  def doListCategories(self, client_rec, m_nls, user_id, page_no):
    """
    Handles rivescript _jsListCategories_ (see cms_wc.rive)
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    assert isinstance(page_no, int)
    acc_tok = client_rec["facebook_page"]["access_token"]
    if self.m_woocom is None:
      rec_wc = client_rec["woocommerce"]
      self.m_woocom = mod_woocommerce.Wc(rec_wc["url"], rec_wc["consumer_key"], rec_wc["consumer_secret"])
    if self.raw_gensts is None: # needs for formatting currency
      self.raw_gensts = self.m_woocom.getGeneralSetting()
      self.parseGeneralSetting(self.raw_gensts)
    records = self.m_woocom.getProductCategoriesList(ITEMS_PER_PAGE, page_no)
    mgr_prods = [] # messenger items template
    for rec in records:
      productsCount = rec["count"]
      if productsCount > 0:
        image = ""
        if rec["image"] is not None:
          image = rec["image"]["src"]
        # logger.debug(rec)
        mgr_prods.append({
          "title": rec["name"],
          "subtitle": rec["description"],
          "image_url": image,
          "buttons": [{
            "type": "postback",
            "title": "See {0} products".format(productsCount),
            "payload": "{0}_1_{1}".format(PAYLOAD_LISTPRODUCTS, rec["id"])
          }]
        })
    if len(records) >= ITEMS_PER_PAGE:
      mgr_prods[ITEMS_PER_PAGE - 1]["buttons"].append({
        "type": 'postback',
        "title": 'More categories',
        "payload": "{0}_{1}".format(PAYLOAD_LISTCATEGORIES, page_no + 1)
      })
    mod_messenger.sendMessengerImagesMessage(acc_tok, user_id, mgr_prods)
    return True

  def PLViewProductDetail(self, product_id, client_rec, m_nls, user_id):
    """
    Handle Payload: Show product detail
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(product_id, str)
    if self.m_woocom is None:
      rec_wc = client_rec["woocommerce"]
      self.m_woocom = mod_woocommerce.Wc(rec_wc["url"], rec_wc["consumer_key"],rec_wc["consumer_secret"])
    if self.raw_gensts is None: # needs for formatting currency
      self.raw_gensts = self.m_woocom.getGeneralSetting()
      self.parseGeneralSetting(self.raw_gensts)
    product = self.m_woocom.getProductDetail(product_id)
    product_name = mod_misc.strRemoveMarkup(product["name"])
    m_nls.setUserVar(user_id, RSVAR_CUR_PRODUCT, product_id)
    m_nls.setUserVar(user_id, RSVAR_CUR_VAR_SELECTED, "")
    acc_tok = client_rec["facebook_page"]["access_token"]
    out_msg = "Thank you interesting on {0}...".format(product_name)
    time.sleep(1)
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    out_msg = mod_misc.strRemoveMarkup(product["description"])
    time.sleep(1)
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    if product["price"] != product["regular_price"] and product["regular_price"] != "":
      special = mod_misc.wcMakeCurrencyStr(self.currcy_sts, float(product["price"]))
      price = mod_misc.wcMakeCurrencyStr(self.currcy_sts, float(product["regular_price"]))
      out_msg = "Regular price {0}. Now special {1}".format(price, special)
    else:
      price = mod_misc.wcMakeCurrencyStr(self.currcy_sts, float(product["price"]))
      out_msg = "Price {0}".format(price)
    time.sleep(1)
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    out_msg = "Category: " + mod_misc.strMakeComma(product["categories"])
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    if product["dimensions"]["length"] or product["dimensions"]["width"] or product["dimensions"]["height"]:
      time.sleep(1)
      out_msg = "Dimension: "
      if product["dimensions"]["length"]:
        out_msg += " length=" + product["dimensions"]["length"] + ", "
      if product["dimensions"]["length"]:
        out_msg += " width=" + product["dimensions"]["width"] + ", "
      if product["dimensions"]["height"]:
        out_msg += " height=" + product["dimensions"]["height"] + ", "
      if len(out_msg) > 0:
        out_msg = out_msg[:len(out_msg) - 2]
      mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    time.sleep(1)
    if product["manage_stock"] == True:
      stock = product["stock_quantity"]
      in_stock = product["in_stock"]
      out_msg = "Stock: "
      if in_stock:
        out_msg += str(stock) + " in stock"
      else:
        out_msg += "Out of stock"
      mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
      time.sleep(1)
    if len(product["variations"]) > 0:
      # Variations product handling...
      self.doViewProductVariations(acc_tok, user_id, product)
    else:
      # conventional handling... Display buttons template
      buttons = [{
        "title": 'View on web',
        "type": "web_url",
        "url": product["permalink"]
      }, {
        "title": 'Add to Cart',
        "type": "postback",
        "payload": "{0}_{1}".format(PAYLOAD_ADDTOCART, product_id)
      }]
      out_msg = "Further act on this product:"
      mod_messenger.sendMessengerButtonMessage(acc_tok, user_id, out_msg, buttons)
    return True

  def PLAddProductToCart(self, product_id, client_rec, m_nls, user_id):
    """
    Handle Payload: Add product to shopping cart (db)
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(product_id, str)
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    if self.m_woocom is None:
      rec_wc = client_rec["woocommerce"]
      self.m_woocom = mod_woocommerce.Wc(rec_wc["url"], rec_wc["consumer_key"],rec_wc["consumer_secret"])
    if self.raw_gensts is None: # needs for formatting currency
      self.raw_gensts = self.m_woocom.getGeneralSetting()
      self.parseGeneralSetting(self.raw_gensts)
    acc_tok = client_rec["facebook_page"]["access_token"]
    product = self.m_woocom.getProductDetail(product_id)
    if product["in_stock"] == False:
      out_msg = "Sorry! " + product["name"] + " is out of stock currently :(. Please choose another product."
      mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    else:
      m_shopcart = mod_shopcart.ShoppingCart(user_id, client_rec["fb_page_id"])
      m_shopcart.loadFromDatabase()
      m_shopcart.appendProduct(product)
      m_shopcart.saveToDatabase()
      shopcart_url = mod_global.SERVER_URL
      if not shopcart_url.endswith("/"): shopcart_url += "/"
      btns = [{
        "title": "View Cart",
        "type": "postback",
        "payload": PAYLOAD_VIEWCART
      }, {
        "title": "Check Out",
        "type": "web_url",
        "url": shopcart_url + "mwp?page=shopCart&uid={0}&rid={1}".format(user_id, client_rec["fb_page_id"])
      }]
      out_msg = product["name"] + " added to shopping cart."
      mod_messenger.sendMessengerButtonMessage(acc_tok, user_id, out_msg, btns)
    return True

  def PLViewCart(self, client_rec, m_nls, user_id):
    """
    Handle Payload: PAYLOAD_VIEWCART
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    acc_tok = client_rec["facebook_page"]["access_token"]
    fb_page_id = client_rec["fb_page_id"]
    m_shopcart = mod_shopcart.ShoppingCart(user_id, fb_page_id)
    m_shopcart.loadFromDatabase()
    item_count = 0
    if m_shopcart.getCartItem() is not None:
      item_count = len(m_shopcart.getCartItem())
    if item_count == 0:
      out_msg = "There is no item in shopping cart."
      mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    else:
      btns = [{
        "title": "Check Out",
        "type": "web_url",
        "url": mod_global.SERVER_URL + "mwp?page=shopCart&uid={0}&rid={1}".format(user_id, fb_page_id)
      }]
      item_str = "item"
      if item_count > 1: item_str = "items"
      out_msg = MSG_BROWSE_CART.format(item_count, item_str)
      mod_messenger.sendMessengerButtonMessage(acc_tok, user_id, out_msg, btns)
    return True

  def PLGetProductsByName(self, client_rec, user_id, page_no, name):
    """
    Handle Payload: PAYLOAD_FINDPRODUCTS
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(name, str)
    assert client_rec is not None
    assert isinstance(user_id, str)
    assert isinstance(page_no, int)
    acc_tok = client_rec["facebook_page"]["access_token"]
    out_msg = "Finding products {0}...".format(name)
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    time.sleep(1)
    if self.m_woocom is None:
      rec_wc = client_rec["woocommerce"]
      self.m_woocom = mod_woocommerce.Wc(rec_wc["url"], rec_wc["consumer_key"], rec_wc["consumer_secret"])
    if self.raw_gensts is None: # needs for formatting currency
      self.raw_gensts = self.m_woocom.getGeneralSetting()
      self.parseGeneralSetting(self.raw_gensts)
    records = self.m_woocom.searchProductsByName(ITEMS_PER_PAGE, page_no, name)
    if len(records) == 0:
      mod_messenger.sendMessengerTextMessage(acc_tok, user_id, "Sorry, product no matched with " + name + "!")
      return True
    out_msg = "I found {0} products which the name like {1}:".format(len(records), name)
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    mgr_prods = self.productsToMessengerImages(records, PAYLOAD_FINDPRODUCTS + "_" + name, page_no)
    mod_messenger.sendMessengerImagesMessage(acc_tok, user_id, mgr_prods)
    return True

  def PLGetProductsByPrice(self, client_rec, user_id, page_no, image_msg, min_price=None, max_price=None):
    """
    Handle Payload: PAYLOAD_PRODUCTS_PRICE_BETWEEN, _MAX or _MIN
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert isinstance(user_id, str)
    assert isinstance(page_no, int)
    assert min_price is not None or max_price is not None
    acc_tok = client_rec["facebook_page"]["access_token"]
    out_msg = "Products looking up..."
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    time.sleep(1)
    if self.m_woocom is None:
      rec_wc = client_rec["woocommerce"]
      self.m_woocom = mod_woocommerce.Wc(rec_wc["url"], rec_wc["consumer_key"], rec_wc["consumer_secret"])
    if self.raw_gensts is None: # needs for formatting currency
      self.raw_gensts = self.m_woocom.getGeneralSetting()
      self.parseGeneralSetting(self.raw_gensts)
    records = self.m_woocom.searchProductsByPriceRange(ITEMS_PER_PAGE, page_no, min_price, max_price)
    if len(records) == 0:
      mod_messenger.sendMessengerTextMessage(acc_tok, user_id, "Sorry, product no matched with " + name + "!")
      return True
    # sort the result by price
    records2 = sorted(records, key=lambda k: float(k["price"]))
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, image_msg)
    if min_price is not None and max_price is not None:
      payload = PAYLOAD_PRODUCTS_PRICE_BETWEEN + "_" + min_price + "&" + max_price
    elif min_price is not None:
      payload = PAYLOAD_PRODUCTS_PRICE_MIN + "_" + min_price
    elif max_price is not None:
      payload = PAYLOAD_PRODUCTS_PRICE_MAX + "_" + max_price
    mgr_prods = self.productsToMessengerImages(records2, payload, page_no)
    mod_messenger.sendMessengerImagesMessage(acc_tok, user_id, mgr_prods)
    return True

  def doListAllOrders(self, client_rec, m_nls, user_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    acc_tok = client_rec["facebook_page"]["access_token"]
    fb_page_id = client_rec["fb_page_id"]
    if self.m_woocom is None:
      rec_wc = client_rec["woocommerce"]
      self.m_woocom = mod_woocommerce.Wc(rec_wc["url"], rec_wc["consumer_key"], rec_wc["consumer_secret"])
    if self.raw_gensts is None: # needs for formatting currency
      self.raw_gensts = self.m_woocom.getGeneralSetting()
      self.parseGeneralSetting(self.raw_gensts)
    m_db = mod_database.Mdb()
    orders = m_db.getOrderByUserAndFbpage(user_id, fb_page_id)
    # orders = None
    # print("orders:")
    # print(orders)
    if orders is None:
      out_msg = "You have no order in our record..."
      mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    else:
      order_str = "order"
      if len(orders) > 1:
        order_str = "orders"
        orders = sorted(orders, key=lambda k: k["doc"]["order_id"])
      out_msg = "I found you have {0} {1} in our record...".format(len(orders), order_str)
      mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
      for order in orders:
        order_doc = order["doc"]
        wcorder = order_doc["wcorder"]
        out_msg = "Order no.: " + str(order_doc["order_id"]) + CR + "Date: " + mod_misc.timestampToString(order_doc["created_at"]) + CR + "Total: " + wcorder["currency"] + wcorder["total"]
        buttons = [{
          "title": 'Order #' + str(order_doc["order_id"]) + " details",
          "type": "postback",
          "payload": "{0}_{1}".format(PAYLOAD_ORDERDETAILS, order["id"])
        }]
        mod_messenger.sendMessengerButtonMessage(acc_tok, user_id, out_msg, buttons)
    return True

  def PLOrderDetails(self, client_rec, user_id, order_id):
    """
    Handle Payload: PAYLOAD_ORDERDETAILS
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert isinstance(user_id, str)
    assert isinstance(order_id, str)
    acc_tok = client_rec["facebook_page"]["access_token"]
    fb_page_id = client_rec["fb_page_id"]
    m_db = mod_database.Mdb()
    ord = m_db.findOrderPoolById(order_id)["doc"]
    if self.m_woocom is None:
      rec_wc = client_rec["woocommerce"]
      self.m_woocom = mod_woocommerce.Wc(rec_wc["url"], rec_wc["consumer_key"], rec_wc["consumer_secret"])
    wcorder_id = ord["order_id"]
    wcorder = self.m_woocom.getOrder(wcorder_id)
    out_msg = "Order# {0} details".format(wcorder_id) + ":" + CR
    out_msg += "Date: {0}".format(mod_misc.timestampToString(ord["created_at"])) + CR
    out_msg += "Total: {0}{1}".format(ord["wcorder"]["currency"], ord["wcorder"]["total"]) + CR
    out_msg += "Payment method: " + wcorder["payment_method_title"] + CR
    out_msg += "Bill to: " + wcorder["billing"]["first_name"] + " " + wcorder["billing"]["last_name"] + CR
    out_msg += "Items:" + CR
    for item in wcorder["line_items"]:
      out_msg += "  " + item["name"] + ", Qty: " + str(item["quantity"]) + ", Subtotal: " + item["subtotal"] + CR
    out_msg += "Ship to: " + wcorder["shipping"]["first_name"] + " " + wcorder["shipping"]["last_name"] + CR
    out_msg += "Address: " + wcorder["shipping"]["address_1"] + " " + wcorder["shipping"]["address_2"] + wcorder["shipping"]["city"] + " " + wcorder["shipping"]["state"] + wcorder["shipping"]["country"] + CR
    out_msg += "Shipping method:" + CR
    for shipline in wcorder["shipping_lines"]:
      out_msg += "  " + shipline["method_title"] + ": " + shipline["total"] + CR
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    return True

  def PLGetStarted(self, client_rec, m_nls, user_id):
    """
    Handle Payload: PAYLOAD_GETSTARTED
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    m_nls.setUserVar(user_id, RSVAR_CUR_PRODUCT, None) # Reset rivescript state
    acc_tok = client_rec["facebook_page"]["access_token"]
    # get user name and save it to rs uservar
    user_profile = mod_messenger.getMessengerUserProfile(acc_tok, user_id)
    m_nls.setUserVar(user_id, RSVAR_FBUSER_PROFILE, mod_misc.dictToJsonStr(user_profile))
    user_name = user_profile["first_name"]
    logger.debug("user_name: " + user_name)
    m_nls.setUserVar(user_id, 'name', user_name)
    buttons = [{
      "title": "Quick help",
      "type": "postback",
      "payload": PAYLOAD_QUICKHELP
    }]
    m_db = mod_database.Mdb()
    # get shopping cart
    shop_cart = m_db.findShopcartByUserAndFbpageid(user_id, client_rec["fb_page_id"])
    if shop_cart is not None and shop_cart["doc"]["cart_items"] is not None:
      if len(shop_cart["doc"]["cart_items"]) > 0:
        buttons.append({
          "title": "View your cart",
          "type": "postback",
          "payload": PAYLOAD_VIEWCART
        })
    # get hot products
    wc_rec = client_rec["woocommerce"]
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    tagrs = m_wc.getTagBySlug("hot")
    if len(tagrs) > 0 and tagrs[0]["count"] > 0:
      tagr = tagrs[0]
      products = m_wc.getProductsList(ITEMS_PER_PAGE, 1, tag_id=tagr["id"])
      logger.debug("num of products: " + str(len(products)))
      if len(products) > 0:
        buttons.append({
          "title": "Show hot products",
          "type": "postback",
          "payload": "{0}_1".format(PAYLOAD_HOTPRODUCTS)
        })
    # get woocommerce sitename
    site_name = wc_rec["site_name"]
    if site_name is None: site_name = "My online shop"
    out_msg = "Hello {0}, Welcome to {1}. Please select your act".format(user_name, site_name)
    mod_messenger.sendMessengerButtonMessage(acc_tok, user_id, out_msg, buttons)
    return True

  def doShowStoreName(self, client_rec, m_nls, user_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    site_name = "Chatbot CMS - WcBot"
    if "site_name" in client_rec["woocommerce"]:
      site_name = client_rec["woocommerce"]["site_name"]
    out_msg = "Our store name is {0}".format(site_name)
    acc_tok = client_rec["facebook_page"]["access_token"]
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
    return True

  def doShowStoreUrl(self, client_rec, m_nls, user_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    site_url = client_rec["woocommerce"]["url"]
    acc_tok = client_rec["facebook_page"]["access_token"]
    out_msg = "Our store website address is " + site_url
    buttons = [{
      "title": 'Browse it now',
      "type": "web_url",
      "url": site_url
    }]
    mod_messenger.sendMessengerButtonMessage(acc_tok, user_id, out_msg, buttons)
    return True

  def doShowWcbotProductInfo(self, client_rec, m_nls, user_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    acc_tok = client_rec["facebook_page"]["access_token"]
    site_url = "https://chatbotcms.com/wcbot.html"
    out_msg = "Info of this chatbot: " + site_url
    buttons = [{
      "title": 'Browse it now',
      "type": "web_url",
      "url": site_url
    }]
    mod_messenger.sendMessengerButtonMessage(acc_tok, user_id, out_msg, buttons)
    return True
  
  def doAnswerQuickQuestion(self, client_rec, m_nls, user_id, question):
    """
    This is to handle general answer to quick questions. It will check the question inside the questions list. If found, it will send the anwser as a text message to the user.
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    assert isinstance(question, str)
    questions = {
      "_jsShowWcbotHowToPayInfo_": "You can say 'view shopping cart'. Then I will tell you more :)",
    }
    if question in questions:
      acc_tok = client_rec["facebook_page"]["access_token"]
      out_msg = questions[question]
      mod_messenger.sendMessengerTextMessage(acc_tok, user_id, out_msg)
      return True
    else:
      return False

  def productsToMessengerImages(self, products, payload_prefix, page_no):
    """
    Create Messenger images template list from woocommerce products
    Notes: 2018-03-09: Add support for product variation
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(products, list)
    assert isinstance(payload_prefix, str)
    results = []
    i = 0
    for product in products:
      category = mod_misc.strMakeComma(product["categories"])
      image = ""
      if len(product["images"]) > 0 and product["images"][0]["src"] is not None:
        image = product["images"][0]["src"]
      # logger.debug(product)
      price = mod_misc.wcMakeCurrencyStr(self.currcy_sts, float(product["price"]))
      result = {
        "title": product["name"],
        "subtitle": "Category: {0}\nPrice {1}".format(category, price),
        "image_url": image,
        "buttons": [{
          "type": "postback",
          "title": "Detail",
          "payload": "{0}_{1}".format(PAYLOAD_SHOWPRODUCT, product["id"])
        }]
      }
      # Check it has product variation
      if len(product["variations"]) == 0:
        result["buttons"].append({
          "title": 'Add to Cart',
          "type": 'postback',
          "payload": "{0}_{1}".format(PAYLOAD_ADDTOCART, product["id"])
        })
      else:
        result["buttons"].append({
          "title": "See variations",
          "type": "postback",
          "payload": "{0}_{1}_1".format(PAYLOAD_PRODUCT_VARIATION, product["id"])
        })
      results.append(result)
      i += 1
      if i == ITEMS_PER_PAGE:
        break

    if len(products) >= ITEMS_PER_PAGE:
      results[ITEMS_PER_PAGE - 1]["buttons"].append({
        "type": 'postback',
        "title": 'Show More',
        "payload": "{0}_{1}".format(payload_prefix, page_no + 1)
      })
    return results

  def doOrderReceived(self, user_id, fb_page_id, order_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    m_db = mod_database.Mdb()
    client_rec = m_db.findClientByFbPageId(fb_page_id)
    acc_tok = client_rec["facebook_page"]["access_token"]
    msg = "Thank you! I noticed that you've placed an order. Below is the order details:"
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, msg)
    self.PLOrderDetails(client_rec, user_id, order_id)
    return True

  def doViewProductVariations(self, acc_tok, user_id, product):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(acc_tok, str)
    assert isinstance(user_id, str)
    assert product is not None
    assert self.m_woocom is not None
    attributes = []
    messages = []
    for attr in product["attributes"]:
      attributes.append(attr["name"])
      messages.append("Different " + attr["name"])
    msg = "This product has multiple variations: " + ", ".join(attributes)
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, msg)

    time.sleep(1)
    msg = "Do you want to see the variations of {0}?".format(product["name"])
    buttons = [{
      "title": "Show variations",
      "type": "postback",
      "payload": "{0}_{1}_1".format(PAYLOAD_PRODUCT_VARIATION, product["id"])
    }]
    mod_messenger.sendMessengerButtonMessage(acc_tok, user_id, msg, buttons)
    return True

  def PLShowProductVariation(self, client_rec, m_nls, user_id, product_id, page_no):
    """
    Handle Payload: PAYLOAD_PRODUCT_VARIATION
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert client_rec is not None
    assert m_nls is not None
    assert isinstance(user_id, str)
    assert isinstance(product_id, str)
    assert isinstance(page_no, str)
    assert self.m_woocom is not None
    acc_tok = client_rec["facebook_page"]["access_token"]
    product = self.m_woocom.getProductDetail(product_id)
    msg = product["name"] + " variations:"
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, msg)
    variations = self.m_woocom.getProductVariations(product_id, ITEMS_PER_PAGE, page_no)
    # cur_var_selected format: {"[name]": "[value]""}. e.g. {"Color", "36"} - 36 is product_id
    images = []
    cur_var_selected = m_nls.getUserVar(user_id, RSVAR_CUR_VAR_SELECTED)
    for variation in variations:
      titles = []
      for lattr in variation["attributes"]:
        titles.append(lattr["option"])
      subtitle = "In stock"
      if not variation["in_stock"]:
        subtitle = "Out of stock"
      images.append({
        "title": ", ".join(titles),
        "subtitle": subtitle,
        "image_url": variation["image"]["src"],
        "buttons": [{
          "title": 'View on web',
          "type": "web_url",
          "url": variation["permalink"]
        }, {
          "title": 'Add to Cart',
          "type": "postback",
          "payload": "{0}_{1}".format(PAYLOAD_ADDTOCART, variation["id"])
        }]
      })
    if len(variations) >= ITEMS_PER_PAGE:
      images[ITEMS_PER_PAGE - 1]["buttons"].append({
        "type": 'postback',
        "title": 'Show More Variations',
        "payload": "{0}_{1}_{2}".format(PAYLOAD_PRODUCT_VARIATION, product_id, int(page_no) + 1)
      })
    mod_messenger.sendMessengerImagesMessage(acc_tok, user_id, images)
    return True
