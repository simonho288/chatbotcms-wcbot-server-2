"""
Paypal Payment Flow Chart:
https://docs.google.com/drawings/d/1kRqfhFffbZxPmDSKPX7XcF6FXSCpGjv1IQt68L3P9O0/edit?usp=sharing

"""
import os
import requests
import time
import logging
import json
import inspect
import datetime
import paypalrestsdk
import braintree
import stripe

import mod_misc
import mod_woocommerce
import mod_database
import mod_global
import mod_shopcart

# from requests.auth import HTTPBasicAuth
from requests.utils import quote
from inspect import currentframe, getframeinfo
from urllib.parse import urlparse, parse_qsl
from flask import Flask, make_response, request, jsonify, render_template, redirect, abort

logger = mod_misc.initLogger(__name__)

class Paygate(object):
  def __init__(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    self.wc_raw_paygates = None
    self.gw_paypal = None
    self.gw_stripe = None
    self.gw_braintree = None

  def initBraintree(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    if self.gw_braintree is None:
      return False
    mode = braintree.Environment.Production
    if self.gw_braintree["isSandbox"]:
      mode = braintree.Environment.Sandbox
    braintree.Configuration.configure(mode,
      self.gw_braintree["merchantId"],
      self.gw_braintree["publicKey"],
      self.gw_braintree["secretKey"]
    )
    return True

  def getRawPaymentGateways(self):
    """
    Get processed of all gateways. (Processed in initPaymentGateways())
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert self.wc_raw_paygates is not None
    return self.wc_raw_paygates

  def initPaymentGateways(self, m_wc):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert m_wc is not None
    gwsts = m_wc.getPaymentGateways() # Call WooCommerce to get payment gateway
    self.wc_raw_paygates = gwsts
    for gw in gwsts:
      if gw["enabled"]:
        gw_id = gw["id"]
        if gw_id == "paypal":
          self.gw_paypal = {
            "title": gw["title"],
            "isSandbox": gw["settings"]["testmode"]["value"] == "yes",
            "email": gw["settings"]["email"]["value"],
            "clientId": gw["settings"]["api_username"]["value"],
            "clientSecret": gw["settings"]["api_password"]["value"],
            "receiverEmail": gw["settings"]["receiver_email"]["value"],
            "invoicePrefix": gw["settings"]["invoice_prefix"]["value"],
            "paymentAction": gw["settings"]["paymentaction"]["value"]
          }
        elif gw_id == "stripe":
          self.gw_stripe = {
            "title": gw["title"],
            "isSandbox": gw["settings"]["testmode"]["value"] == "yes",
          }
          if self.gw_stripe["isSandbox"]:
            self.gw_stripe["publishKey"] = gw["settings"]["test_publishable_key"]["value"]
            self.gw_stripe["secretKey"] = gw["settings"]["test_secret_key"]["value"]
          else:
            self.gw_stripe["publishKey"] = gw["settings"]["publishable_key"]["value"]
            self.gw_stripe["secretKey"] = gw["settings"]["secret_key"]["value"]
        elif gw_id == "braintree_credit_card":
          self.gw_braintree = {
            "title": gw["title"],
            "isSandbox": gw["settings"]["environment"]["value"] == "sandbox",
          }
          if self.gw_braintree["isSandbox"]:
            self.gw_braintree["merchantId"] = gw["settings"]["sandbox_merchant_id"]["value"]
            self.gw_braintree["publicKey"] = gw["settings"]["sandbox_public_key"]["value"]
            self.gw_braintree["secretKey"] = gw["settings"]["sandbox_private_key"]["value"]
          else:
            self.gw_braintree["merchantId"] = gw["settings"]["merchant_id"]["value"]
            self.gw_braintree["publicKey"] = gw["settings"]["public_key"]["value"]
            self.gw_braintree["secretKey"] = gw["settings"]["private_key"]["value"]

  def createBraintreeClientToken(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    if not self.initBraintree():
      return None
    mode = "Production"
    if self.gw_braintree["isSandbox"]: mode = "Sandbox"
    return {
      "clientToken": braintree.ClientToken.generate(),
      "mode": mode
    }

  def getStripePublishKey(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    if self.gw_stripe is None:
      return ""
    else:
      return self.gw_stripe["publishKey"]

  def getPaypalAccountInfo(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    if self.gw_paypal is None:
      return ""
    else:
      result = {
        "email": self.gw_paypal["email"],
        "mode": "Production"
      }
      if self.gw_paypal["isSandbox"]:
        result["mode"] = "Sandbox"
      return result

  # def paypalSubmit(self, params):
  #   logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  #   user_id = params["userId"]
  #   fb_page_id = params["recipientId"]
  #   order_id = params["orderId"]
  #   payment_id = params["payment_id"]
  #   currency = params["currency"]
  #   total = parseFloat(params["totalAmount"])
  #   rlink = self.createPaypalPayment(payment_id, order_id, user_id, fb_page_id, total, currency)
  #   return rlink

  # def createPaypalPayment(self, payment_id, order_id, user_id, fb_page_id, total, currency):
  #   """
  #   Ref: https://github.com/paypal/PayPal-Python-SDK
  #   """
  #   logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  #   assert isinstance(payment_id, str)
  #   assert isinstance(order_id, str)
  #   assert isinstance(user_id, str)
  #   assert isinstance(fb_page_id, str)
  #   assert isinstance(total, float)
  #   assert isinstance(currency, float)
  #   pp_items = [{
  #     "name": "Chatbot CMS - WooCommerce Order no. " + order_id,
  #     "sku": "chatbotcms_woocommerce",
  #     "price": amount,
  #     "currency": currency,
  #     "quantity": 1
  #   }]
  #   mode = "live"
  #   if self.gw_paypal["isSandbox"]:
  #     mode = "sandbox"
  #   paypalrestsdk.configure({
  #     "mode": mode,
  #     "client_id": "EBWKjlELKMYqRNQ6sYvFo64FtaRLRR5BdHEESmha49TM",
  #     "client_secret": "EO422dn3gQLgDbuwqTjzrFgFtaRLRR5BdHEESmha49TM"
  #   })
  #   payment = paypalrestsdk.Payment({
  #     "intent": "sale",
  #     "payer": {
  #       "payment_method": "paypal"
  #     },
  #     "redirect_urls": {
  #       "return_url": "{0}/mwp?page=orderReceived&pid={1}".format(host, payment_id),
  #       "cancel_url": "{0}/mwp?page=paymentFailure&pid={1}".format(host, payment_id)
  #     },
  #     "transactions": [{
  #       "item_list": {
  #         "items": pp_items
  #       },
  #       "amount": {
  #         "total": amount,
  #         "currency": currency
  #       },
  #       "description": "This is the payment transaction description."
  #     }]
  #   })
  #   if payment.create():
  #     print("Payment created successfully")
  #   else:
  #     print(payment.error)

  def doPaymentPaypal(self, payment_id, total, currency, gateway_sts):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    assert isinstance(total, str)
    assert isinstance(currency, str)
    assert gateway_sts is not None
    assert isinstance(gateway_sts["api_username"]["value"], str)
    assert isinstance(gateway_sts["api_password"]["value"], str)
    assert isinstance(gateway_sts["api_signature"]["value"], str)
    assert isinstance(gateway_sts["email"]["value"], str)
    assert isinstance(gateway_sts["testmode"]["value"], str)
    print("mod_global.SERVER_URL=" + mod_global.SERVER_URL)
    # Pre-save a payment to database
    test_mode = gateway_sts["testmode"]["value"]
    if test_mode == "yes":
      mode = "sandbox"
      api_username = gateway_sts["sandbox_api_username"]["value"]
      api_password = gateway_sts["sandbox_api_password"]["value"]
      api_signature = gateway_sts["sandbox_api_signature"]["value"]
    else:
      mode = "live"
      api_username = gateway_sts["api_username"]["value"]
      api_password = gateway_sts["api_password"]["value"]
      api_signature = gateway_sts["api_signature"]["value"]
    email = gateway_sts["email"]["value"]
    urls = mod_misc.getPaypalUrlsByMode(mode)
    nvp_data = {
      "USER": api_username,
      "PWD": api_password,
      "SIGNATURE": api_signature,
      # "SUBJECT": email,
      "METHOD": "SetExpressCheckout",
      "VERSION": 93,
      "PAYMENTREQUEST_0_PAYMENTACTION": "SALE",
      "PAYMENTREQUEST_0_AMT": str(total),
      "PAYMENTREQUEST_0_CURRENCYCODE": currency,
      "RETURNURL": mod_global.SERVER_URL + "payment_return?pid=" + payment_id,
      "CANCELURL": mod_global.SERVER_URL + "payment_cancel?pid=" + payment_id
    }
    response = requests.post(urls["nvp_url"], data=nvp_data) # post to Paypal NVP API
    pp_rst = dict(parse_qsl(response.text))
    if pp_rst["ACK"] == "Failure":
      return make_response(pp_rst["L_SHORTMESSAGE0"], 500)
    else:
      token = pp_rst["TOKEN"]
      redirect_url = urls["pp_url"] + "?cmd=_express-checkout&token=" + token
      return make_response(redirect_url) # for frontend redirect. See orderPayment.js

  def doPaymentBraintreeCC(self, payment_id, total, currency, gateway_sts, braintree_nonce):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    assert isinstance(total, str)
    assert isinstance(currency, str)
    assert gateway_sts is not None
    assert isinstance(braintree_nonce, str)
    # inital braintree individual in this function only use
    if (gateway_sts["environment"]["value"] == "sandbox"):
      mode = braintree.Environment.Sandbox
      merchant_id = gateway_sts["sandbox_merchant_id"]["value"]
      public_key = gateway_sts["sandbox_public_key"]["value"]
      private_key = gateway_sts["sandbox_private_key"]["value"]
    else:
      mode = braintree.Environment.Production
      merchant_id = gateway_sts["merchant_id"]["value"]
      public_key = gateway_sts["public_key"]["value"]
      private_key = gateway_sts["private_key"]["value"]
    assert isinstance(merchant_id, str)
    assert isinstance(public_key, str)
    assert isinstance(private_key, str)
    braintree.Configuration.configure(mode, merchant_id, public_key, private_key)
    result = braintree.Transaction.sale({
      "amount": total,
      "payment_method_nonce": braintree_nonce,
      "options": { "submit_for_settlement": True }
    })
    if result.is_success:
      m_db = mod_database.Mdb()
      m_db.setPaymentTxnGatewayResult(payment_id, {
        "id": result.transaction.id,
        "merchant_account_id": result.transaction.merchant_account_id,
        "payment_instrument_type": result.transaction.payment_instrument_type,
        "processor_authorization_code": result.transaction.processor_authorization_code,
        "processor_response_text": result.transaction.processor_response_text,
        "status": result.transaction.status,
        "type": result.transaction.type
      })
      return make_response(jsonify({ "payment_id": payment_id }))
    else:
      message = ""
      for error in result.errors.deep_errors:
        message += error.message + "<br />"
      abort(500, message)

  def doPaymentStripe(self, payment_id, total, currency, gateway_sts, stripe_token):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    assert isinstance(total, str)
    assert isinstance(currency, str)
    assert gateway_sts is not None
    assert isinstance(stripe_token, str)
    descriptor = gateway_sts["statement_descriptor"]["value"]
    if gateway_sts["testmode"]["value"] == "yes":
      secret_key = gateway_sts["test_secret_key"]["value"]
      publish_key = gateway_sts["test_publishable_key"]["value"]
    else:
      secret_key = gateway_sts["secret_key"]["value"]
      publish_key = gateway_sts["publishable_key"]["value"]
    stripe.api_key = secret_key
    stripe_txn = stripe.Charge.create(
      amount = int(float(total) * 100),
      currency = currency,
      source = stripe_token,
      description = descriptor
    )
    if stripe_txn["status"] == "succeeded":
      m_db = mod_database.Mdb()
      m_db.setPaymentTxnGatewayResult(payment_id, stripe_txn.to_dict())
      return make_response(jsonify({ "payment_id": payment_id }))
    else:
      message = ""
      for error in result.errors.deep_errors:
        message += error.message + "<br />"
      abort(500, message)

  def doPaymentBacs(self, payment_id, total, currency, gateway_sts):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    assert isinstance(total, str)
    assert isinstance(currency, str)
    assert gateway_sts is not None
    # Nothing to do
    return make_response(jsonify({ "payment_id": payment_id }))

  def doPaymentCheque(self, payment_id, total, currency, gateway_sts):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    assert isinstance(total, str)
    assert isinstance(currency, str)
    assert gateway_sts is not None
    # Nothing to do
    return make_response(jsonify({ "payment_id": payment_id }))

  def doPaymentCod(self, payment_id, total, currency, gateway_sts):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    assert isinstance(total, str)
    assert isinstance(currency, str)
    assert gateway_sts is not None
    # Nothing to do
    return make_response(jsonify({ "payment_id": payment_id }))

  def handleReturn(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert request is not None
    m_db = mod_database.Mdb()
    payment_id = request.values["pid"]
    payment_rec = m_db.findPaymentTxnById(payment_id)["doc"]
    if payment_rec["status"] != "pending": # prevent double entry
      return None
    payment_rec["status"] = "paid" # update the payment status to "paid"
    m_db.replacePaymentRecord(payment_id, payment_rec)
    payment_method = payment_rec["payment_method"]
    if payment_method == "paypal":
      return self.handlePaypalReturn(payment_id, request, m_db, payment_rec)
    elif payment_method == "braintree_credit_card":
      return self.handleBraintreeCCReturn(payment_id, request, m_db, payment_rec)
    elif payment_method == "stripe":
      return self.handleStripeReturn(payment_id, request, m_db, payment_rec)
    elif payment_method == "bacs":
      return self.handleBacsChequeCodReturn(payment_id, request, m_db, payment_rec)
    elif payment_method == "cheque":
      return self.handleBacsChequeCodReturn(payment_id, request, m_db, payment_rec)
    elif payment_method == "cod":
      return self.handleBacsChequeCodReturn(payment_id, request, m_db, payment_rec)
    else:
      raise Exception("Unknown payment gateway: " + payment_method)

  def handlePaypalReturn(self, payment_id, request, m_db, payment_rec):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    assert request is not None
    assert m_db is not None
    assert payment_rec is not None
    token = request.values["token"]
    payer_id = request.values["PayerID"]
    gateway_sts = payment_rec["gateway_settings"]
    test_mode = gateway_sts["testmode"]["value"]
    if test_mode == "yes":
      api_username = gateway_sts["sandbox_api_username"]["value"]
      api_password = gateway_sts["sandbox_api_password"]["value"]
      api_signature = gateway_sts["sandbox_api_signature"]["value"]
    else:
      api_username = gateway_sts["api_username"]["value"]
      api_password = gateway_sts["api_password"]["value"]
      api_signature = gateway_sts["api_signature"]["value"]
    email = gateway_sts["email"]["value"]
    if test_mode == "yes": mode = "sandbox"
    else: mode = "live"
    # checkout_details = self.callPaypalNVPGetCheckoutDetail(mode, api_username, api_password, api_signature, token)
    # TODO: Maybe add a "Confirm Pay" button here in future
    result_txn = self.callPaypalNVPGetCompleteTxn(mode, api_username, api_password, api_signature, token, payer_id, payment_rec["total"], payment_rec["currency"])
    m_db.setPaymentTxnGatewayResult(payment_id, result_txn)
    client_rec = m_db.findClientByFbPageId(payment_rec["fb_page_id"])
    m_cart = mod_shopcart.ShoppingCart(payment_rec["user_id"], payment_rec["fb_page_id"])
    m_cart.loadFromDatabase()
    orderpool_id = payment_rec["order_id"]
    orderpool_rec = m_db.findOrderPoolById(orderpool_id)["doc"]
    wcorder_id = str(orderpool_rec["order_id"])
    wc_rec = client_rec["woocommerce"]
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    wcorder = m_wc.getOrder(wcorder_id)
    self.updateOrderPool(True, m_db, orderpool_id, payment_id, payment_rec)
    self.updateWcOrder(True, wcorder_id, client_rec, payment_rec, result_txn)
    self.updateWcProductStocks(m_wc, wcorder)
    return {
      "paymenttxn": payment_rec,
      "shopcart": m_cart.getRecord(),
      "wcorder": wcorder
    }

  def handleBraintreeCCReturn(self, payment_id, request, m_db, payment_rec):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    assert request is not None
    assert m_db is not None
    assert payment_rec is not None
    gateway_sts = payment_rec["gateway_settings"]
    gateway_txn = payment_rec["gateway_txn"]
    client_rec = m_db.findClientByFbPageId(payment_rec["fb_page_id"])
    m_cart = mod_shopcart.ShoppingCart(payment_rec["user_id"], payment_rec["fb_page_id"])
    m_cart.loadFromDatabase()
    orderpool_id = payment_rec["order_id"]
    orderpool_rec = m_db.findOrderPoolById(orderpool_id)["doc"]
    wcorder_id = str(orderpool_rec["order_id"])
    wc_rec = client_rec["woocommerce"]
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    wcorder = m_wc.getOrder(wcorder_id)
    self.updateOrderPool(True, m_db, orderpool_id, payment_id, payment_rec)
    self.updateWcOrder(True, wcorder_id, client_rec, payment_rec, gateway_txn)
    self.updateWcProductStocks(m_wc, wcorder)
    return {
      "paymenttxn": payment_rec,
      "shopcart": m_cart.getRecord(),
      "wcorder": wcorder
    }

  def handleStripeReturn(self, payment_id, request, m_db, payment_rec):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    assert request is not None
    assert m_db is not None
    assert payment_rec is not None
    gateway_sts = payment_rec["gateway_settings"]
    gateway_txn = payment_rec["gateway_txn"]
    client_rec = m_db.findClientByFbPageId(payment_rec["fb_page_id"])
    m_cart = mod_shopcart.ShoppingCart(payment_rec["user_id"], payment_rec["fb_page_id"])
    m_cart.loadFromDatabase()
    orderpool_id = payment_rec["order_id"]
    orderpool_rec = m_db.findOrderPoolById(orderpool_id)["doc"]
    wcorder_id = str(orderpool_rec["order_id"])
    wc_rec = client_rec["woocommerce"]
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    wcorder = m_wc.getOrder(wcorder_id)
    self.updateOrderPool(True, m_db, orderpool_id, payment_id, payment_rec)
    self.updateWcOrder(True, wcorder_id, client_rec, payment_rec, gateway_txn)
    self.updateWcProductStocks(m_wc, wcorder)
    return {
      "paymenttxn": payment_rec,
      "shopcart": m_cart.getRecord(),
      "wcorder": wcorder
    }

  def handleBacsChequeCodReturn(self, payment_id, request, m_db, payment_rec):
    """
    BACS/Cheque/COD are all same handling for payment return
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    assert request is not None
    assert m_db is not None
    assert payment_rec is not None
    gateway_sts = payment_rec["gateway_settings"]
    # gateway_txn = payment_rec["gateway_txn"]
    client_rec = m_db.findClientByFbPageId(payment_rec["fb_page_id"])
    m_cart = mod_shopcart.ShoppingCart(payment_rec["user_id"], payment_rec["fb_page_id"])
    m_cart.loadFromDatabase()
    orderpool_id = payment_rec["order_id"]
    orderpool_rec = m_db.findOrderPoolById(orderpool_id)["doc"]
    wcorder_id = str(orderpool_rec["order_id"])
    wc_rec = client_rec["woocommerce"]
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    wcorder = m_wc.getOrder(wcorder_id)
    self.updateOrderPool(False, m_db, orderpool_id, payment_id, payment_rec)
    self.updateWcOrder(False, wcorder_id, client_rec, payment_rec)
    # NOTES: Don't update stock level for these kinds of payment
    # self.updateWcProductStocks(m_wc, wcorder)
    return {
      "paymenttxn": payment_rec,
      "shopcart": m_cart.getRecord(),
      "wcorder": wcorder
    }

  def callPaypalNVPGetCheckoutDetail(self, mode, api_username, api_password, api_signature, token):
    """
    Call Paypal NVP to get checkout detail
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(mode, str)
    urls = mod_misc.getPaypalUrlsByMode(mode)
    # Call Paypal NVP to get checkout details
    # Ref: https://blog.codezero.xyz/paypal-express-checkout-in-python/ and https://developer.paypal.com/docs/classic/express-checkout/ht_ec-singleItemPayment-curl-etc/
    nvp_data = {
      "USER": api_username,
      "PWD": api_password,
      "SIGNATURE": api_signature,
      # "SUBJECT": email,
      "METHOD": "GetExpressCheckoutDetails",
      "VERSION": 93,
      "TOKEN": token
    }
    response = requests.post(urls["nvp_url"], data=nvp_data) # post to Paypal NVP API
    return dict(parse_qsl(response.text))

  def callPaypalNVPGetCompleteTxn(self, mode, api_username, api_password, api_signature, token, payer_id, amount, currency):
    """
    Call Paypal NVP to complete the transaction
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(mode, str)
    assert isinstance(token, str)
    assert isinstance(payer_id, str)
    urls = mod_misc.getPaypalUrlsByMode(mode)
    # Call Paypal NVP to get checkout details
    # Ref: https://blog.codezero.xyz/paypal-express-checkout-in-python/ and https://developer.paypal.com/docs/classic/express-checkout/ht_ec-singleItemPayment-curl-etc/
    nvp_data = {
      "USER": api_username,
      "PWD": api_password,
      "SIGNATURE": api_signature,
      # "SUBJECT": email,
      "METHOD": "DoExpressCheckoutPayment",
      "VERSION": 93,
      "TOKEN": token,
      "PAYERID": payer_id,
      "PAYMENTREQUEST_0_PAYMENTACTION": "SALE",
      "PAYMENTREQUEST_0_AMT": str(amount),
      "PAYMENTREQUEST_0_CURRENCYCODE": currency
    }
    response = requests.post(urls["nvp_url"], data=nvp_data) # post to Paypal NVP API
    return dict(parse_qsl(response.text))

  def handleCancel(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert request is not None
    m_db = mod_database.Mdb()
    payment_id = request.values["pid"]
    payment_rec = m_db.findPaymentTxnById(payment_id)["doc"]
    payment_rec["status"] = "cancelled" # mark the status to cancelled
    m_db.replacePaymentRecord(payment_id, payment_rec)
    return payment_rec # return payment_rec but it is deleted

  def updateOrderPool(self, is_paid, m_db, orderpool_id, payment_id, payment_rec):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert m_db is not None
    assert isinstance(is_paid, bool)
    assert isinstance(orderpool_id, str)
    assert isinstance(payment_id, str)
    assert payment_rec is not None
    # update orderPools
    props = [
      {
        "key": "payment_transaction",
        "value": {
          "id": payment_id,
          "payment_method_title": payment_rec["payment_method_title"]
        }
      },
      {
        "key": "is_paid",
        "value": True
      }
    ]
    if is_paid:
      props.append({
        "key": "paid_at",
        "value": int(round(time.time() * 1000))
      })
    m_db.updateOrderPoolById(orderpool_id, props)

  def updateWcOrder(self, is_paid, wcorder_id, client_rec, payment_rec, txn_obj=None):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(is_paid, bool)
    assert isinstance(wcorder_id, str)
    assert client_rec is not None
    assert payment_rec is not None
    if is_paid:
      assert txn_obj is not None
    order_id = payment_rec["order_id"]
    method = payment_rec["payment_method"]
    if method == "stripe":
      order_status = "processing"
      txn_id = txn_obj["id"]
    elif method == "braintree_credit_card":
      order_status = "processing"
      txn_id = txn_obj["id"]
    elif method == "paypal":
      order_status = "processing"
      txn_id = txn_obj["PAYMENTINFO_0_TRANSACTIONID"]
    elif method == "bacs": pass
    elif method == "cheque": pass
    elif method == "cod": pass
    else:
      raise Exception("Unhandled payment method: " + method)
    wc_rec = client_rec["woocommerce"]
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    props = {
      "payment_method": payment_rec["payment_method"],
      "payment_method_title": payment_rec["payment_method_title"],
    }
    if is_paid:
      props["status"] = order_status # change the order status
      props["transaction_id"] = txn_id
      props["date_paid"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
      props["date_paid_gmt"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    m_wc.updateOrder(wcorder_id, props)

  def updateWcProductStocks(self, m_wc, wcorder):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert wcorder is not None
    update_cmd = [] # batch of product to be updated the stock
    for item in wcorder["line_items"]:
      product_id = item["product_id"]
      qty = item["quantity"]
      # Is it the stock managing?
      product = m_wc.getProductDetail(str(product_id))
      if product["manage_stock"]:
        new_qty = product["stock_quantity"] - qty
        update_cmd.append({
          "id": product_id,
          "stock_quantity": new_qty,
          "in_stock": new_qty > 0
        })
    cmd_obj = { "update": update_cmd }
    m_wc.updateProductBatch(cmd_obj)
