/**
 * This module used in orderReview.pug
 */
'use strict'

$(document).ready(function () {
  // $.when(LoadShoppingCart(), LoadWcOrder()).done(function(rstCart, rstOrder) {
  //   window._shoppingCart = rstCart[0]
  //   window._wcOrder = rstOrder[0]

    RenderItemsIntoTable()

    $('.loading_wrapper').hide()
    $('.loaded_wrapper').show()
    SetupUI()
  // }).fail(function(err) {
  //   console.error(err)
  // })
})

function SetupUI() {
  console.log('SetupUI()')

  $('#btn_proceed').click(onBtnProceed)
  $('#btn_back').click(onBtnBack)
}

function RenderItemsIntoTable() {
  console.log('RenderItemsIntoTable()')
  console.assert(window._wcOrder)

  var markup = ''
  var orderTotal = 0
  var orderTax = 0
  var crySts = window._shoppingCart.server_settings.currency

  for (var i = 0; i < window._wcOrder.line_items.length; i++) {
    var orderItem = window._wcOrder.line_items[i]
    orderItem.subtotal = parseFloat(orderItem.subtotal)
    orderItem.subtotal_tax = parseFloat(orderItem.subtotal_tax)
    orderItem.total = parseFloat(orderItem.total)
    orderItem.total_tax = parseFloat(orderItem.total_tax)

    var item = null
    for (var j = 0; j < window._shoppingCart.cart_items.length; j++) {
      var ci = window._shoppingCart.cart_items[j]
      if (ci.product_id == orderItem.product_id) {
        item = ci
        break
      }
    }
    console.assert(item != null)
    item.qty = parseFloat(item.qty)
    item.unit_price = parseFloat(item.unit_price)

    item.unit_tax = orderItem.subtotal_tax / orderItem.quantity
    item.subtotal = orderItem.subtotal + orderItem.subtotal_tax
    orderTotal += orderItem.subtotal
    orderTax += orderItem.subtotal_tax

    markup += '<tr>'
    markup += '<td>'
    markup += '<img src="' + item.image + '" />'
    markup += '</td>'
    markup += '<td>'
    markup += item.name
    markup += '</td>'
    markup += '<td style="text-align: right">'
    markup += item.qty
    markup += '</td>'
    markup += '<td style="text-align: right">'
    markup += util.ParseCurrencyToDisp(crySts, item.unit_price, false)
    markup += '</td>'
    markup += '<td style="text-align: right">'
    markup += util.ParseCurrencyToDisp(crySts, item.unit_tax, false)
    markup += '</td>'
    markup += '<td style="text-align: right">'
    markup += util.ParseCurrencyToDisp(crySts, item.subtotal)
    markup += '</td>'
    markup += '</tr>'
  }

  var shipTotal = parseFloat(window._wcOrder.shipping_total)
  var shipTax = parseFloat(window._wcOrder.shipping_tax)
  var totalAmount = orderTotal + orderTax + shipTotal + shipTax
  $('#order_total').html(util.ParseCurrencyToDisp(crySts, orderTotal))
  $('#order_tax').html(util.ParseCurrencyToDisp(crySts, orderTax))
  $('#ship_total').html(util.ParseCurrencyToDisp(crySts, shipTotal))
  $('#ship_tax').html(util.ParseCurrencyToDisp(crySts, shipTax))
  $('#total_amount').html(util.ParseCurrencyToDisp(crySts, totalAmount))

  $('#table_items tbody').html(markup)
}

function LoadShoppingCart() {
  console.log('LoadShoppingCart()')
  console.assert(window._userId) // this assigned in shoppingCart.pug
  console.assert(window._recipientId) // this assigned in shoppingCart.pug

  return $.ajax({
    method: 'GET',
    url: 'ws/db_loadcart',
    data: {
      uid: window._userId,
      rid: window._recipientId
    }
  })
}

function LoadWcOrder() {
  console.log('LoadWcOrder()')
  console.assert(window._userId)
  console.assert(window._recipientId)
  console.assert(window._orderId)

  return $.ajax({
    method: 'GET',
    url: 'get_wc_order',
    data: {
      uid: window._userId,
      rid: window._recipientId,
      oid: window._orderId
    }
  })
}

function RemoveWcOrder() {
  console.log('RemoveWcOrder()')
  console.assert(window._orderId)
  console.assert(window._userId)
  console.assert(window._recipientId)

  return $.ajax({
    type: 'DELETE',
    url: 'ws/delete_order',
    data: {
      oid: window._orderId,
      uid: window._userId,
      rid: window._recipientId
    }
  })
}

function EnableAllButtons(isEnable) {
  if (isEnable) {
    $('#btn_proceed').removeClass('disabled loading')
    $('#btn_back').removeClass('disabled loading')
  } else {
    $('#btn_proceed').addClass('disabled loading')
    $('#btn_back').addClass('disabled loading')
  }
}

function onBtnBack(evt) {
  console.log('onBtnBack()')
  
  var dlg = $('#dlg_discardwarn')
  dlg.modal('show')
  dlg.find('#btn_ok').click(function(evt) {
    EnableAllButtons(false)

    RemoveWcOrder().done(function() {
      var url = 'mwp?page=shopCart&uid=' + window._userId + '&rid=' + window._recipientId
      window.location.href = url
    }).fail(function(xhr, status, err) {
      $.alert({
        type: 'red',
        useBootstrap: false,
        title: err,
        content: xhr.responseText,
      })
    })
  })
  dlg.find('#btn_cancel').click(function (evt) {
    $('#dlg_discardwarn').modal('hide')
  })
}

function onBtnProceed(evt) {
  console.log('onBtnProceed()')
  console.assert(window._orderId)
  console.assert(window._userId)
  console.assert(window._recipientId)

  EnableAllButtons(false)
  
  window.location.href = 'mwp?page=orderPayment&oid=' + window._orderId + '&uid=' + window._userId + '&rid=' + window._recipientId
}
