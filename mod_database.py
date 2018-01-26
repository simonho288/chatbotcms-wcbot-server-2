# Dynamodb Ref:
# https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GettingStarted.Python.html
# https://pypi.python.org/pypi/dynamodb-json/1.1.2

import os 
# import datetime # datetime.datetime.utcnow()
import time
import pymongo
import inspect
import uuid
import json
import boto3
import decimal
from datetime import datetime
# from decimal import Decimal

import mod_global
import mod_misc

from inspect import currentframe, getframeinfo
from pymongo import MongoClient
from dynamodb_json import json_util as djson
from boto3.dynamodb.conditions import Key, Attr
from botocore import session

# AWS Keys and services setup
assert os.environ["AMZACCESSKEY"] is not None, "env AMZACCESSKEY is not defined!"
assert os.environ["AMZACCESSSECRET"] is not None, "env AMZACCESSSECRET is not defined!"
assert os.environ["AMZREGION"] is not None, "env AMZREGION is not defined!"
assert os.environ["AMZBUCKET"] is not None, "env AMZBUCKET is not defined!"
boto3.setup_default_session(
  aws_access_key_id=os.environ["AMZACCESSKEY"],
  aws_secret_access_key=os.environ["AMZACCESSSECRET"],
  region_name=os.environ["AMZREGION"])

# MongoDB collection names (for conversion use)
MONGO_COLL_CLIENTS = "clients"
MONGO_COLL_USER_VARS = "rs_user_vars2"
MONGO_COLL_SHOP_CART = "shop_cart2"
MONGO_COLL_ORDERS_POOL = "orders_pool"
MONGO_COLL_PAYMENT_TXN = "payment_transaction"

# Dynamodb collection names
DYNAMO_COLL_CLIENTS = "Chatbotcms_Clients"
DYNAMO_COLL_USER_VARS = "Chatbotcms_RsUserVars"
DYNAMO_COLL_SHOP_CART = "Chatbotcms_WcBotShopCarts"
DYNAMO_COLL_ORDERS_POOL = "Chatbotcms_WcBotOrdersPool"
DYNAMO_COLL_PAYMENT_TXN = "Chatbotcms_WcBotPaymentTxn"

logger = mod_misc.initLogger(__name__)

dclient = boto3.client('dynamodb')
dynamodb = boto3.resource('dynamodb')

# Internal functions
def __dynamodbDeleteAllItems(table_name):
  """
  Delete all records in specified table
  """
  table = dynamodb.Table(table_name)
  response = dclient.describe_table(TableName = table_name)
  keys = [k["AttributeName"] for k in response["Table"]["KeySchema"]]
  response = table.scan()
  items = response["Items"]
  with table.batch_writer() as batch:
    for item in items:
      key_dict = {k: item[k] for k in keys}
      batch.delete_item(Key=key_dict)

def __createDynamoTables():
  """
  Create all tables for DynamoDB
  """
  table = dynamodb.create_table(
    TableName = DYNAMO_COLL_CLIENTS,
    KeySchema = [{
      "AttributeName": "client_id",
      "KeyType": "HASH"
    }],
    AttributeDefinitions = [{
      "AttributeName": "client_id",
      "AttributeType": "S"
    }],
    ProvisionedThroughput = {
      "ReadCapacityUnits": 5,
      "WriteCapacityUnits": 5
    }
  )
  table = dynamodb.create_table(
    TableName = DYNAMO_COLL_USER_VARS,
    KeySchema = [{
      "AttributeName": "user_id",
      "KeyType": "HASH"
    }, {
      "AttributeName": "fb_page_id",
      "KeyType": "RANGE"
    }],
    AttributeDefinitions = [{
      "AttributeName": "user_id",
      "AttributeType": "S"
    }, {
      "AttributeName": "fb_page_id",
      "AttributeType": "S"
    }],
    ProvisionedThroughput = {
      "ReadCapacityUnits": 5,
      "WriteCapacityUnits": 5
    }
  )
  table = dynamodb.create_table(
    TableName = DYNAMO_COLL_SHOP_CART,
    KeySchema = [{
      "AttributeName": "user_id",
      "KeyType": "HASH"
    }, {
      "AttributeName": "fb_page_id",
      "KeyType": "RANGE"
    }],
    AttributeDefinitions = [{
      "AttributeName": "user_id",
      "AttributeType": "S"
    }, {
      "AttributeName": "fb_page_id",
      "AttributeType": "S"
    }],
    ProvisionedThroughput = {
      "ReadCapacityUnits": 5,
      "WriteCapacityUnits": 5
    }
  )
  table = dynamodb.create_table(
    TableName = DYNAMO_COLL_ORDERS_POOL,
    KeySchema = [{
      "AttributeName": "id",
      "KeyType": "HASH"
    }],
    AttributeDefinitions = [{
      "AttributeName": "id",
      "AttributeType": "S"
    }],
    ProvisionedThroughput = {
      "ReadCapacityUnits": 5,
      "WriteCapacityUnits": 5
    }
  )
  table = dynamodb.create_table(
    TableName = DYNAMO_COLL_PAYMENT_TXN,
    KeySchema = [{
      "AttributeName": "id",
      "KeyType": "HASH"
    }],
    AttributeDefinitions = [{
      "AttributeName": "id",
      "AttributeType": "S"
    }],
    ProvisionedThroughput = {
      "ReadCapacityUnits": 5,
      "WriteCapacityUnits": 5
    }
  )
  print("Tables creation initiative. It should be finishen within several minutes. Please check the status in AWS dynamodb console.")

def __convertTable_Clients():
  # Source database (MongoDB)
  mclient = MongoClient(os.environ["MONGO_URL"])
  db_cbc = mclient.chatbotcms # main database
  src_coll = db_cbc[MONGO_COLL_CLIENTS]
  src_records = src_coll.find()
  # Destination database (DynamoDB)
  __dynamodbDeleteAllItems(DYNAMO_COLL_CLIENTS)
  for record in src_records:
    doc = {
      "client_id": { "S": record["_id"] },
      "version": { "S": record["version"] },
      "plugin_type": { "S": record["plugin_type"] },
      "shop_type": { "S": record["shop_type"] },
      "client_email": { "S": record["client_email"] },
      "woocommerce": { 
        "M": {
          "url": { "S": record["woocommerce"]["url"] },
          "consumer_key": { "S": record["woocommerce"]["consumer_key"] },
          "consumer_secret": { "S": record["woocommerce"]["consumer_secret"] },
          "site_name": { "S": record["woocommerce"]["site_name"] }
        }
      },
      "facebook_page": {
        "M": {
          "access_token": { "S": record["facebook_page"]["access_token"] }
        }
      },
      "fb_page_id": { "S": record["fb_page_id"] },
      "created_at": { "N": str(int(record["created_at"])) },
      "subscribe_date": { "N": str(int(record["subscribe_date"])) },
    }
    dclient.put_item(TableName=DYNAMO_COLL_CLIENTS, Item=doc)

class Mdb: # MongoDB
  def __init__(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")

  def getClientsCount(self):
    """
    For testing connection
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    table = dynamodb.Table(DYNAMO_COLL_CLIENTS)
    response = table.scan()
    items = response["Items"]
    return len(items)

  def findClientByVerifyToken(self, ver_tok):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(ver_tok, str)
    table = dynamodb.Table(DYNAMO_COLL_CLIENTS)
    resp = table.get_item(
      Key = {
        "client_id": ver_tok
      }
    )
    if not "Item" in resp:
      return None
    return resp["Item"]

  def updateClientSubscribeDate(self, client_id, dtime):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(client_id, str)
    assert isinstance(dtime, int)
    table = dynamodb.Table(DYNAMO_COLL_CLIENTS)
    resp = table.update_item(
      Key = {
        "client_id": client_id
      },
      UpdateExpression = "set subscribe_date = :r",
      ExpressionAttributeValues = {
        ":r": dtime
      }
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

  def findClientByFbPageId(self, fb_page_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(fb_page_id, str)
    table = dynamodb.Table(DYNAMO_COLL_CLIENTS)
    resp = table.scan(
      FilterExpression = "fb_page_id = :r",
      ExpressionAttributeValues = {
        ":r": fb_page_id
      }
    )
    if resp["Count"] > 0:
      obj = resp["Items"][0]
      return djson.loads(obj)
    return None

  def findRsUserVarsByUserAndPage(self, user_id, fb_page_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    table = dynamodb.Table(DYNAMO_COLL_USER_VARS)
    resp = table.get_item(
      Key = {
        "user_id": user_id,
        "fb_page_id": fb_page_id
      }
    )
    if not "Item" in resp:
      return None
    return resp["Item"]

  def updateRsUserVars(self, user_id, fb_page_id, user_vars):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert user_vars is not None
    table = dynamodb.Table(DYNAMO_COLL_USER_VARS)
    resp = table.update_item(
      Key = {
        "user_id": user_id,
        "fb_page_id": fb_page_id
      },
      UpdateExpression = "set doc = :r",
      ExpressionAttributeValues = {
        ":r": json.dumps(user_vars)
      }
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

  def findShopcartByUserAndFbpageid(self, user_id, fb_page_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    table = dynamodb.Table(DYNAMO_COLL_SHOP_CART)
    resp = table.get_item(
      Key = {
        "user_id": user_id,
        "fb_page_id": fb_page_id
      }
    )
    if not "Item" in resp:
      return None
    # return resp["Item"]
    return json.loads(json.dumps(resp["Item"], cls=mod_misc.DecimalEncoder))

  def upsertShopcart(self, user_id, fb_page_id, rec):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert rec is not None
    table = dynamodb.Table(DYNAMO_COLL_SHOP_CART)
    resp = table.get_item(
      Key = {
        "user_id": user_id,
        "fb_page_id": fb_page_id
      }
    )
    if not "Item" in resp:
      # Perform insert
      doc = {
        "user_id": user_id,
        "fb_page_id": fb_page_id,
        "doc": rec
      }
      table.put_item(
        Item = doc
      )
    else:
      # Perform update
      resp = table.update_item(
        Key = {
          "user_id": user_id,
          "fb_page_id": fb_page_id
        },
        UpdateExpression = "set doc = :r",
        ExpressionAttributeValues = {
          ":r": rec
        }
      )
      assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

  def updateShopcartServerSettings(self, user_id, fb_page_id, doc):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert doc is not None
    table = dynamodb.Table(DYNAMO_COLL_SHOP_CART)
    resp = table.update_item(
      Key = {
        "user_id": user_id,
        "fb_page_id": fb_page_id
      },
      UpdateExpression = "set doc.server_settings = :doc",
      ExpressionAttributeValues = {
        ":doc": doc
      }
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

  def updateShopcartCartitems(self, user_id, fb_page_id, doc):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert doc is not None
    table = dynamodb.Table(DYNAMO_COLL_SHOP_CART)
    resp = table.update_item(
      Key = {
        "user_id": user_id,
        "fb_page_id": fb_page_id
      },
      UpdateExpression = "set doc.cart_items = :doc",
      ExpressionAttributeValues = {
        ":doc": doc
      }
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

  def updateShopcartInputinfo(self, user_id, fb_page_id, doc):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert doc is not None
    table = dynamodb.Table(DYNAMO_COLL_SHOP_CART)
    resp = table.update_item(
      Key = {
        "user_id": user_id,
        "fb_page_id": fb_page_id
      },
      UpdateExpression = "set doc.input_info = :r",
      ExpressionAttributeValues = {
        ":r": doc
      }
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

  def updateShopcartShipinfo(self, user_id, fb_page_id, doc):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert doc is not None
    table = dynamodb.Table(DYNAMO_COLL_SHOP_CART)
    resp = table.update_item(
      Key = {
        "user_id": user_id,
        "fb_page_id": fb_page_id
      },
      UpdateExpression = "set doc.ship_info = :doc",
      ExpressionAttributeValues = {
        ":doc": doc
      }
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200
  
  def updateShopcartOrderpool(self, user_id, fb_page_id, doc):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert doc is not None
    table = dynamodb.Table(DYNAMO_COLL_SHOP_CART)
    resp = table.update_item(
      Key = {
        "user_id": user_id,
        "fb_page_id": fb_page_id
      },
      UpdateExpression = "set doc.order_pool = :doc",
      ExpressionAttributeValues = {
        ":doc": doc
      }
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

  def getOrderByUserAndFbpage(self, user_id, fb_page_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(fb_page_id, str)
    assert isinstance(user_id, str)
    table = dynamodb.Table(DYNAMO_COLL_ORDERS_POOL)
    resp = table.scan(
      Select = "ALL_ATTRIBUTES",
      FilterExpression = Attr("doc.user_id").eq(user_id) & Attr("doc.fb_page_id").eq(fb_page_id) & Attr("doc.app_name").eq("WCBOT") & Attr("doc.is_paid").eq(True)
    )
    if resp["Count"] > 0:
      obj = resp["Items"]
      return djson.loads(obj)
    return None

  def findOrderPoolById(self, id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(id, str)
    table = dynamodb.Table(DYNAMO_COLL_ORDERS_POOL)
    resp = table.get_item(
      Key = {
        "id": id
      }
    )
    if not "Item" in resp:
      return None
    return resp["Item"]

  def updateOrderPoolById(self, id, props):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(id, str)
    assert isinstance(props, list)
    assert len(props) > 0
    table = dynamodb.Table(DYNAMO_COLL_ORDERS_POOL)
    update_exp = "set "
    values = {}
    i = 1
    for prop in props:
      arg_name = ":r" + str(i)
      update_exp += "doc." + prop["key"] + "=" + arg_name + ", "
      values[arg_name] = prop["value"]
      i = i + 1
    update_exp = update_exp[:len(update_exp) - 2]
    resp = table.update_item(
      Key = {
        "id": id
      },
      UpdateExpression = update_exp,
      ExpressionAttributeValues = values
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

  def deleteOrderPoolById(self, id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(id, str)
    table = dynamodb.Table(DYNAMO_COLL_ORDERS_POOL)
    resp = table.delete_item(
      Key = {
        "id": id
      }
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

  def saveOrderToPool(self, user_id, fb_page_id, wc_order):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert wc_order is not None
    doc = {
      "id": str(uuid.uuid4()),
      "doc": {
        "app_name": mod_global.APP_NAME,
        "user_id": user_id,
        "fb_page_id": fb_page_id,
        "order_id": wc_order["id"],
        "created_at": int(round(time.time() * 1000)),
        "is_paid": False,
        "wcorder": { # similar to woocommerce order. It can be faster load time
          "date_created": wc_order["date_created"],
          "total": wc_order["total"],
          "currency": wc_order["currency"],
        }
      }
    }
    table = dynamodb.Table(DYNAMO_COLL_ORDERS_POOL)
    resp = table.put_item(
      Item = doc
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200
    return doc

  def savePaymentTransaction(self, txn):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert txn is not None
    table = dynamodb.Table(DYNAMO_COLL_PAYMENT_TXN)
    txn = mod_misc.remove_empty_string(txn)
    # rec_id = str(uuid.uuid4())
    rec_id = mod_misc.genRandomId()
    doc = {
      "id": rec_id,
      "doc": txn
    }
    resp = table.put_item(
      Item = doc
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200
    return rec_id

  def findPaymentTxnById(self, payment_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    table = dynamodb.Table(DYNAMO_COLL_PAYMENT_TXN)
    resp = table.get_item(
      Key = {
        "id": payment_id
      }
    )
    if not "Item" in resp:
      return None
    return resp["Item"]

  def setPaymentCancelled(self, payment_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    table = dynamodb.Table(DYNAMO_COLL_PAYMENT_TXN)
    resp = table.update_item(
      Key = {
        "id": payment_id
      },
      UpdateExpression = "set doc.status = :f",
      ExpressionAttributeValues = {
        ":f": "cancelled"
      }
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

  def setPaymentTxnGatewayResult(self, payment_id, txn_obj):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(payment_id, str)
    assert txn_obj is not None
    txn_obj = mod_misc.remove_empty_string(txn_obj)
    table = dynamodb.Table(DYNAMO_COLL_PAYMENT_TXN)
    resp = table.update_item(
      Key = { "id": payment_id },
      UpdateExpression = "set doc.gateway_txn = :r1",
      ExpressionAttributeValues = {
        ":r1": txn_obj
      }
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

