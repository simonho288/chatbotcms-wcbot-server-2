/**
 * This module used in shoppingCart.pug
 */
'use strict'

$(document).ready(function () {
  // Render the shopping cart
  // LoadShoppingCart().done(function(result) {
    // Dismiss the loading screen
    $('.loading_wrapper').hide()
    $('.loaded_wrapper').show()
    // window._shoppingCart = result

    RenderCartAndSetupEvent()
  // }).fail(function(err) {
  //   alert(err.statusText)
  // })

  // fix main menu to page on passing
  $('.main.menu').visibility({
    type: 'fixed'
  })
  $('.overlay').visibility({
    type: 'fixed',
    offset: 80
  })

  // lazy load images
  $('.image').visibility({
    type: 'image',
    transition: 'vertical flip in',
    duration: 500
  })

  // show dropdown on hover
  $('.main.menu .ui.dropdown').dropdown({
    on: 'hover'
  })

  $('#btn_checkout').on('click', function(evt) {
    EnableAllButtons(false)
    SaveCart(function(result) {
      if (result) {
        DoCheckout()
      }
    })
  })
})

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

function DoCheckout() {
  console.log('DoCheckout()')
  console.assert(window._userId != null)
  console.assert(window._recipientId != null)

  var url = 'mwp?page=orderInfoInput&uid=' + window._userId + '&rid=' + window._recipientId
  if (window._orderId != null && window._orderId != '') {
    url += '&oid=' + window._orderId
  }
  window.location.href = url
}

// Save the current (modified shopping cart items) to server.
function SaveCart(callback) {
  console.log('SaveCart()')
  console.assert(window._userId)
  console.assert(window._recipientId)
  console.assert(window._shoppingCart)

  // No need to save server settings
  var cart = util.CloneObject(window._shoppingCart)
  delete cart.server_settings

  $.ajax({
    type: 'POST',
    url: 'ws/db_savecart',
    data: JSON.stringify({
      userId: window._userId,
      recipientId: window._recipientId,
      cart: cart
    }),
    contentType: 'application/json'
  }).done(function (result) {
    console.log(result)
    if (result === 'ok' && callback) {
      callback(true)
    }
  }).fail(function(err, result, xhr) {
    $.alert({
      type: 'red',
      useBootstrap: false,
      title: err,
      content: xhr.responseText,
    })
    if (callback) {
      callback(false)
    }
  })
}

function getItemStock(itemId) {
  console.log('checkItemStock()')
  console.assert(_recipientId != null)
  
  return $.ajax({
    type: 'GET',
    url: 'ws/get_item_stock',
    data: {
      fb_page_id: _recipientId,
      item_id: itemId
    },
    contentType: 'application/json',
    dataType: 'json'
  })
}

function findItemInCart(itemId) {
  console.log('findItemInCart()')

  for (var i = 0; i < window._shoppingCart.cart_items.length; ++i) {
    var item = window._shoppingCart.cart_items[i]
    if (item.product_id == itemId) {
      return item
    }
  }
  console.assert(false)
}

function CalculateTotal() {
  console.log('CalculateTotal()')
  console.assert(window._shoppingCart.server_settings.currency)
  
  var total = 0
  $('.card').each(function (index, ctrl) {
    var itemId = $(this).data('itemid')
    var item = findItemInCart(itemId)
    total += parseInt(item.qty) * parseFloat(item.unit_price)
  })

  var disp = util.ParseCurrencyToDisp(window._shoppingCart.server_settings.currency, total)
  $('#amount').html(disp)
}

function RemoveItemFromCart(itemId) {
  console.assert(window._shoppingCart)
  console.assert(window._shoppingCart.cart_items)

  var newCartItems = []
  for (var i = 0; i < window._shoppingCart.cart_items.length; ++i) {
    var item = window._shoppingCart.cart_items[i]
    if (item.product_id != itemId) {
      newCartItems.push(item)
    }
  }
  window._shoppingCart.cart_items = newCartItems

  RenderCartAndSetupEvent()
}

function EnableAllButtons(isEnable) {
  if (isEnable) {
    $('#btn_checkout').removeClass('disabled loading')
  } else {
    $('#btn_checkout').addClass('disabled loading')
  }
}

function RenderCartToElem() {
  console.log('RenderCartToElem()')
  console.assert(_shoppingCart.server_settings.currency)

  var cartItems = window._shoppingCart.cart_items
  var ciTempl = $('#cartItem').html()
  var markup = ''
  if (cartItems.length === 0) {
    markup = 'No items in shopping cart. Please close this window and add item to cart in Messenger'
  } else {
    for (var i = 0; i < cartItems.length; ++i) {
      var item = cartItems[i]
      // Construct the qty dropdown
      var dd = ''
      for (var q = 1; q < 100; q++) {
        if (q != item.qty) {
          dd += '<option value="' + q + '">' + q + '</option>'
        } else {
          dd += '<option value="' + q + '" selected="selected">' + q + '</option>'
        }
      }

      var total = item.qty * parseFloat(item.unit_price)
      var disp = util.ParseCurrencyToDisp(window._shoppingCart.server_settings.currency, total, false)

      // Construct the cart item
      var tmpl = ciTempl.replace(/item_image/g, item.image)
                        .replace(/item_itemName/g, item.name)
                        .replace(/item_itemId/g, item.product_id)
                        .replace(/item_unitPrice/g, numeral(item.unit_price).format('0,0[.]00'))
                        .replace(/item_subTotal/g, disp)
                        .replace(/item_qtyDropDown/g, dd)

      markup += tmpl
    }
  }
  $('#cartitems_div').html(markup)

  if (cartItems.length === 0) {
    $('#btn_checkout').attr('disabled', 'disabled')
  }

  CalculateTotal()
}

function RenderCartAndSetupEvent() {
  console.log('RenderCartAndSetupEvent()')
  console.assert(window._shoppingCart)
  console.assert(window._shoppingCart.cart_items)
  console.assert(window._shoppingCart.server_settings.currency)

  RenderCartToElem()

  var cartItems = window._shoppingCart.cart_items

  $('.item_qty').off().on('change', function(evt) {
    var qty = evt.target.value
    var itemId = evt.target.id
    var item = findItemInCart(itemId)
    var $this = $(this)

    getItemStock(itemId).done(function(result) {
      var in_stock = !result.manage_stock
      if (result.manage_stock) {
        if (result.in_stock && result.stock_quantity >= qty) {
          in_stock = true
        }
      }
      if (in_stock) {
        // Re-calculate the sub-total
        item.qty = qty
        var total = qty * item.unit_price
        var disp = util.ParseCurrencyToDisp(window._shoppingCart.server_settings.currency, total, false)
        var markup = 'Sub-total: ' + disp
        $(evt.target).closest('.card').find('.sub_total').html(markup)
        SaveCart()
        CalculateTotal()
        return true
      } else {
        // revert the quantity
        $.alert({
          type: 'red',
          useBootstrap: false,
          title: 'Sorry! Insufficient Stock',
          content: 'We\'ve stock on hand: ' + result.stock_quantity,
          onClose: function() {
            $this.val(item.qty)
          }
        })
        return false
      }
    }).fail(function(err, result, xhr) {
      $.alert({
        type: 'red',
        useBootstrap: false,
        title: err,
        content: xhr.responseText
      })
    })
  })
  
  $('.btn_remove').off().on('click', function(evt) {
    var itemId = $(this).data('itemid')
    RemoveItemFromCart(itemId)
    SaveCart()
  })
}
