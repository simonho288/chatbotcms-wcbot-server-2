/**
 * This module used in orderInfoInput.pug
 */
'use strict'

$(document).ready(function () {
  // RenderItemsIntoTable()
  RenderScreen()

  // Dismiss the loading screen
  $('.loading_wrapper').hide()
  $('.loaded_wrapper').show()
  SetupUI()
  SetupBraintreeCheckout()
  SetupStripeCheckout()
})

function SetupUI() {
  console.log('SetupUI()')

  // setup semantic-ui
  // $('.tabular.menu .item').tab()
  // $('.ui.accordion').accordion('open', 0)
  $('.ui.accordion').accordion()

  $('.btn_pay').click(function(evt) {
    window._curPaymentMethod = $(this).data('paymentmethod')
    window._curPaymentMethodTitle = $(this).data('paymentmethodtitle')
  })

  // $('#btn_proceed').click(onBtnProceed)
  $('#btn_back').click(onBtnBack)

  $('#btn_paypal_pay').click(OnPayWithPaypal)
  // $('#btn_braintree_pay').click(...)
  // $('#btn_stripe_pay').click(...)
  $('#btn_bacs_pay').click(OnPayWithBacs)
  $('#btn_cheque_pay').click(OnPayWithCheque)
  $('#btn_cod_pay').click(OnPayWithCod)
}

// function PayPalFormSubmit(paypalAccount, isSandbox, paymentId) {
//   console.log('PayPalFormSubmit()')
//   console.assert(window._orderId)
//   console.assert(window._totalAmount != null)
//   console.assert(_shoppingCart.server_settings.currency.value)

//   var currency = _shoppingCart.server_settings.currency.value
//   var items = [{
//     name: 'Chatbot CMS - WooCommerce Order no. ' + window._orderId,
//     qty: 1,
//     price: window._totalAmount,
//     itemId: 'chatbotcms_woocommerce'
//   }]
//   var urls = {
//     notify: document.location.origin + '/paypal-notify',
//     cancel: document.location.origin + '/mwp?page=paymentFailure&pid=' + paymentId,
//     success: document.location.origin + '/mwp?page=orderReceived&pid=' + paymentId,
//   }
//   var form = genPayPalMarkup(items, true, currency, paymentId, paypalAccount, urls)
//   $('#hot_form_div').empty()
//   var $form = $(form)
//   $('#hot_form_div').append($form)
//   $form.submit()
// }

function OnPayWithPaypal(evt) {
  console.log('OnPayWithPaypal()')
  console.assert(window._userId)
  console.assert(window._recipientId)
  console.assert(window._orderId)

  window._curPaymentMethod = $(this).data('paymentmethod')
  window._curPaymentMethodTitle = $(this).data('paymentmethodtitle')
  console.assert(window._curPaymentMethod)
  console.assert(window._curPaymentMethodTitle)

  var paypalAccount = $(this).data('email')
  var isSandbox = $(this).data('sandbox') === 'yes'
  console.assert(paypalAccount)

  var gateway = findPaymentGateways(window._curPaymentMethod)
  console.assert(gateway != null)

  $(this).addClass('disabled loading')
  $('#btn_back').addClass('disabled loading')
  $.ajax({
    url: 'ws/checkout_submit',
    type: 'POST',
    data: JSON.stringify({
      user_id: window._userId,
      recipient_id: window._recipientId,
      order_id: window._orderId,
      currency: _shoppingCart.server_settings.currency.value,
      total: window._totalAmount.toString(),
      payment_method: window._curPaymentMethod,
      payment_method_title: window._curPaymentMethodTitle,
      gateway_settings: gateway.settings
    }),
    contentType: 'application/json'
  }).done(function(result) {
    // Prepare make paypal submit form
    console.assert(result != null)
    window.location.href = result
    // PayPalFormSubmit(paypalAccount, isSandbox, result.paymentId)
  }).fail(function(xhr, status, err) {
    $.alert({
      type: 'red',
      useBootstrap: false,
      title: err,
      content: xhr.responseText,
    })
  })
}

function OnPayWithBacs(evt) {
  console.log('OnPayWithBacs()')
  console.assert(window._userId)
  console.assert(window._recipientId)
  console.assert(window._orderId)

  window._curPaymentMethod = $(this).data('paymentmethod')
  window._curPaymentMethodTitle = $(this).data('paymentmethodtitle')
  console.assert(window._curPaymentMethod)
  console.assert(window._curPaymentMethodTitle)

  var gateway = findPaymentGateways(window._curPaymentMethod)
  console.assert(gateway != null)

  $(this).addClass('disabled loading')
  $('#btn_back').addClass('disabled loading')

  $.ajax({
    url: 'ws/checkout_submit',
    type: 'POST',
    data: JSON.stringify({
      user_id: window._userId,
      recipient_id: window._recipientId,
      order_id: window._orderId,
      currency: _shoppingCart.server_settings.currency.value,
      total: window._totalAmount.toString(),
      payment_method: window._curPaymentMethod,
      payment_method_title: window._curPaymentMethodTitle,
      gateway_settings: gateway.settings
    }),
    contentType: 'application/json'
  }).done(function (result) {
    console.assert(result.payment_id != null)
    window.location.href = 'payment_return?pid=' + result.payment_id
  }).fail(function(xhr, status, err) {
    $('#btn_bacs_pay').removeClass('disabled loading')
    $('#btn_back').removeClass('disabled loading')
    $.alert({
      type: 'red',
      useBootstrap: false,
      title: err,
      content: xhr.responseText,
    })
  })
}

function OnPayWithCheque() {
  console.log('OnPayWithCheque()')
  console.assert(window._userId)
  console.assert(window._recipientId)
  console.assert(window._orderId)

  window._curPaymentMethod = $(this).data('paymentmethod')
  window._curPaymentMethodTitle = $(this).data('paymentmethodtitle')
  console.assert(window._curPaymentMethod)
  console.assert(window._curPaymentMethodTitle)

  var gateway = findPaymentGateways(window._curPaymentMethod)
  console.assert(gateway != null)

  $(this).addClass('disabled loading')
  $('#btn_back').addClass('disabled loading')

  $.ajax({
    url: 'ws/checkout_submit',
    type: 'POST',
    data: JSON.stringify({
      user_id: window._userId,
      recipient_id: window._recipientId,
      order_id: window._orderId,
      currency: _shoppingCart.server_settings.currency.value,
      total: window._totalAmount.toString(),
      payment_method: window._curPaymentMethod,
      payment_method_title: window._curPaymentMethodTitle,
      gateway_settings: gateway.settings
    }),
    contentType: 'application/json'
  }).done(function (result) {
    console.assert(result.payment_id != null)
    window.location.href = 'payment_return?pid=' + result.payment_id
  }).fail(function(xhr, status, err) {
    $('#btn_cheque_pay').removeClass('disabled loading')
    $('#btn_back').removeClass('disabled loading')
    $.alert({
      type: 'red',
      useBootstrap: false,
      title: err,
      content: xhr.responseText,
    })
  })
}

function OnPayWithCod() {
  console.log('OnPayWithCod()')
  console.assert(window._userId)
  console.assert(window._recipientId)
  console.assert(window._orderId)

  window._curPaymentMethod = $(this).data('paymentmethod')
  window._curPaymentMethodTitle = $(this).data('paymentmethodtitle')
  console.assert(window._curPaymentMethod)
  console.assert(window._curPaymentMethodTitle)

  var gateway = findPaymentGateways(window._curPaymentMethod)
  console.assert(gateway != null)

  $(this).addClass('disabled loading')
  $('#btn_back').addClass('disabled loading')

  $.ajax({
    url: 'ws/checkout_submit',
    type: 'POST',
    data: JSON.stringify({
      user_id: window._userId,
      recipient_id: window._recipientId,
      order_id: window._orderId,
      currency: _shoppingCart.server_settings.currency.value,
      total: window._totalAmount.toString(),
      payment_method: window._curPaymentMethod,
      payment_method_title: window._curPaymentMethodTitle,
      gateway_settings: gateway.settings
    }),
    contentType: 'application/json'
  }).done(function (result) {
    console.assert(result.payment_id != null)
    window.location.href = 'payment_return?pid=' + result.payment_id
  }).fail(function(xhr, status, err) {
    $('#btn_cod_pay').removeClass('disabled loading')
    $('#btn_back').removeClass('disabled loading')
    $.alert({
      type: 'red',
      useBootstrap: false,
      title: err,
      content: xhr.responseText,
    })
  })
}

function RenderScreen() {
  console.log('RenderScreen()')
  console.assert(window._wcOrder)
  console.assert(window._shoppingCart.server_settings.currency)

  // Render payment methods
  var markup = ''
  for (var i = 0; i < window._wcPaymentGateways.length; ++i) {
    var gateway = window._wcPaymentGateways[i]
    if (!gateway.enabled)
      continue
    switch (gateway.id) {
      case 'bacs':
        markup += '<div class="title">'
        markup +=  '<div class="dropdown icon"></div>'
        markup +=  gateway.title
        markup += '</div>'
        markup += '<div class="content">'
        markup +=  '<p class="transition hidden">'
        markup +=   gateway.description
        markup +=  '</p>'
        markup +=  '<p class="transition hidden">'
        markup += '<button class="ui primary button btn_pay" id="btn_bacs_pay" data-paymentmethod="' + gateway.id + '" data-paymentmethodtitle="' + gateway.title + '">'
        markup +=    'Place Order'
        markup +=   '</button>'
        markup +=  '</p>'
        markup += '</div>'
        break;

      case 'cheque':
        markup += '<div class="title">'
        markup +=  '<div class="dropdown icon"></div>'
        markup +=  gateway.title
        markup += '</div>'
        markup += '<div class="content">'
        markup +=  '<p class="transition hidden">'
        markup +=   gateway.description
        markup +=  '</p>'
        markup +=  '<p class="transition hidden">'
        markup += '<button class="ui primary button btn_pay" id="btn_cheque_pay" data-paymentmethod="' + gateway.id + '" data-paymentmethodtitle="' + gateway.title + '">'
        markup +=    'Place Order'
        markup +=   '</button>'
        markup +=  '</p>'
        markup += '</div>'
        break;

      case 'cod':
        markup += '<div class="title">'
        markup +=  '<div class="dropdown icon"></div>'
        markup +=  gateway.title
        markup += '</div>'
        markup += '<div class="content">'
        markup +=  '<p class="transition hidden">'
        markup +=   gateway.description
        markup +=  '</p>'
        markup +=  '<p class="transition hidden">'
        markup += '<button class="ui primary button btn_pay" id="btn_cod_pay" data-paymentmethod="' + gateway.id + '" data-paymentmethodtitle="' + gateway.title + '">'
        markup +=    'Place Order'
        markup +=   '</button>'
        markup +=  '</p>'
        markup += '</div>'
        break;

      case 'paypal':
        markup += '<div class="title">'
        markup +=  '<div class="dropdown icon"></div>'
        markup +=  gateway.title
        markup += '</div>'
        markup += '<div class="content">'
        markup +=  '<p class="transition hidden">'
        markup +=   gateway.description
        markup +=  '</p>'
        markup +=  '<p class="transition hidden">'
        markup += '<button class="ui primary button btn_pay" id="btn_paypal_pay" data-paymentmethod="' + gateway.id + '" data-paymentmethodtitle="' + gateway.title + '" data-email="' + gateway.settings.email.value + '" data-sandbox="' + gateway.settings.testmode.value + '">'
        markup +=    '<i class="paypal icon"></i>'
        markup +=    'Paid By PayPal'
        markup +=   '</button>'
        markup +=  '</p>'
        markup += '</div>'
        break;

      case 'braintree_credit_card':
        markup += '<div class="title">'
        markup +=  '<div class="dropdown icon"></div>'
        markup +=  gateway.title
        markup += '</div>'
        markup += '<div class="content">'
        markup +=  '<p class="transition hidden">'
        markup +=   gateway.description
        markup +=   '<div class="field">'
        markup +=    '<div class="bt-drop-in-wrapper">'
        markup +=     '<div id="bt-dropin">'
        markup +=     '</div>' // bt-dropin
        markup +=    '</div>' // bt-drop-in-wrapper
        markup +=   '</div>' // field
        markup +=   '<input id="nonce" type="hidden" name="payment_method_nonce" />'
        markup +=   '<button class="ui primary button btn_pay" id="btn_braintree_pay" data-paymentmethod="' + gateway.id + '" data-paymentmethodtitle="' + gateway.title + '">'
        markup +=    '<i class="credit card alternative icon"></i>'
        markup +=    'Paid by Braintree'
        markup +=   '</button>'
        markup +=  '</p>'
        markup +=  '<p id="bt-errmsg" class="errmsg"></p>'
        markup += '</div>'
        break;

      case 'stripe':
        markup += '<div class="title">'
        markup +=  '<div class="dropdown icon"></div>'
        markup +=  gateway.title
        markup += '</div>'
        markup += '<div class="content">'
        markup +=  '<p class="transition hidden">'
        markup +=   gateway.description
        markup +=  '</p>'
        markup +=  '<p class="transition hidden">'
        markup +=   '<div class="field">'
        markup += '<button class="ui primary button btn_pay" id="btn_stripe_pay" data-paymentmethod="' + gateway.id + '" data-paymentmethodtitle="' + gateway.title +  '">'
        markup +=     '<i class="stripe icon"></i>'
        markup +=     'Paid By Stripe'
        markup +=    '</button>'
        markup +=   '</div>' // field
        markup +=  '</p>'
        markup +=  '<p id="stripe_errmsg" class="errmsg"></p>'
        markup += '</div>'
        break;
    }
  }
  $('#payment_methods').html(markup)

  // Calculate order total
  var markup = ''
  var orderTotal = 0
  var orderTax = 0

  for (var i = 0, len = window._wcOrder.line_items.length; i < len; ++i) {
    var orderItem = window._wcOrder.line_items[i]
    orderItem.subtotal = parseFloat(orderItem.subtotal)
    orderItem.subtotal_tax = parseFloat(orderItem.subtotal_tax)
    orderItem.total = parseFloat(orderItem.total)
    orderItem.total_tax = parseFloat(orderItem.total_tax)

    var item = null
    for (var j = 0, len2 = window._shoppingCart.cart_items.length; j < len2; ++j) {
      var ci = window._shoppingCart.cart_items[j]
      if (ci.product_id == orderItem.product_id) {
        item = ci
        break
      }
    }
    item.qty = parseFloat(item.qty)
    item.unit_price = parseFloat(item.unit_price)

    item.unit_tax = orderItem.subtotal_tax / orderItem.quantity
    item.subtotal = orderItem.subtotal + orderItem.subtotal_tax
    orderTotal += orderItem.subtotal
    orderTax += orderItem.subtotal_tax
  }

  // Display the total
  var shipTotal = parseFloat(window._wcOrder.shipping_total)
  var shipTax = parseFloat(window._wcOrder.shipping_tax)
  var totalAmount = orderTotal + orderTax + shipTotal + shipTax
  window._totalAmount = parseFloat(totalAmount.toFixed(5))
  var disp = util.ParseCurrencyToDisp(window._shoppingCart.server_settings.currency, totalAmount)
  $('#total_amount').html(disp)
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

function LoadWcPaymentGateways() {
  console.log('LoadWcPaymentGateways()')
  console.assert(window._userId)
  console.assert(window._recipientId)

  return $.ajax({
    method: 'GET',
    url: 'get_wc_paygates',
    data: {
      uid: window._userId,
      rid: window._recipientId,
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
    // $('#btn_proceed').removeClass('disabled loading')
    $('#btn_back').removeClass('disabled loading')
  } else {
    // $('#btn_proceed').addClass('disabled loading')
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

// function onBtnProceed(evt) {
// 	console.log('onBtnProceed()')
// 	console.assert(window._orderId)
// 	console.assert(window._userId)
// 	console.assert(window._recipientId)

// 	EnableAllButtons(false)
  
// 	window.location.href = 'mwp?page=orderPayment&oid=' + window._orderId + '&uid=' + window._userId + '&rid=' + window._recipientId
// }

function SetupBraintreeCheckout() {
  console.log('SetupBraintreeCheckout()')
  console.assert(window._braintreeClientToken != null)

  var form = document.querySelector('#braintree-payment-form');
  var token = window._braintreeClientToken;

  if (token == '')
    return

  braintree.dropin.create({
    authorization: token,
    container: '#bt-dropin',
    paypal: {
      flow: 'vault'
    }
  }, function (err, instance) {
    if (err) {
      $.alert({
        type: 'red',
        useBootstrap: false,
        title: "Error",
        content: err,
      })
      return
    }

    $('#btn_braintree_pay').click(function (evt) {
      evt.preventDefault() // disable form post

      // window.payment_gateway = 'braintree'

      instance.requestPaymentMethod(function (err, payload) {
        if (err) {
          console.log('Error', err);
          return;
        }

        $('#btn_braintree_pay').addClass('disabled loading')
        $('#btn_back').addClass('disabled loading')
        // var shippingInfo = CollectShippingInfo()

        console.assert(window._curPaymentMethod)
        console.assert(window._curPaymentMethodTitle)

        var gateway = findPaymentGateways(window._curPaymentMethod)
        console.assert(gateway != null)

        $.ajax({
          url: 'ws/checkout_submit',
          type: 'POST',
          data: JSON.stringify({
            user_id: window._userId,
            recipient_id: window._recipientId,
            order_id: window._orderId,
            currency: _shoppingCart.server_settings.currency.value,
            total: window._totalAmount.toString(),
            payment_method: window._curPaymentMethod,
            payment_method_title: window._curPaymentMethodTitle,
            gateway_settings: gateway.settings,
            braintree_nonce: payload.nonce // special property for braintree
          }),
          contentType: 'application/json'
        }).done(function (result) {
          $('#bt-errmsg').html('')
          console.assert(result.payment_id != null)
          window.location.href = 'payment_return?pid=' + result.payment_id
        }).fail(function(xhr, status, err) {
          $('#bt-errmsg').html(err.statusText)
          $('#btn_braintree_pay').removeClass('disabled loading')
          $('#btn_back').removeClass('disabled loading')
          $.alert({
            type: 'red',
            useBootstrap: false,
            title: err,
            content: xhr.responseText,
          })
        })
      });
    });
  });

  function BraintreePayform(config) {
    this.config = config;
    this.config.development = config.development || false;

    this.paymentForm = $('#' + config.formID);
    this.inputs = $('input[type=text], input[type=email], input[type=tel]');
    this.button = this.paymentForm.find('.button');

    this.states = {
      show: 'active',
      wait: 'loading'
    };
    this.focusClass = 'has-focus';
    this.valueClass = 'has-value';

    this.initialize();
  }

  BraintreePayform.prototype.initialize = function () {
    var self = this;

    this.events();
    this.inputs.each(function (index, element) {
      self.labelHander($(element));
    });
    this.notify('error');
  };

  BraintreePayform.prototype.events = function () {
    var self = this;

    this.inputs.on('focus', function () {
      $(this).closest('label').addClass(self.focusClass);
      self.labelHander($(this));
    }).on('keydown', function () {
      self.labelHander($(this));
    }).on('blur', function () {
      $(this).closest('label').removeClass(self.focusClass);
      self.labelHander($(this));
    });
  };

  BraintreePayform.prototype.labelHander = function (element) {
    var self = this;
    var input = element;
    var label = input.closest('label');

    window.setTimeout(function () {
      var hasValue = input.val().length > 0;

      if (hasValue) {
        label.addClass(self.valueClass);
      } else {
        label.removeClass(self.valueClass);
      }
    }, 10);
  };

  BraintreePayform.prototype.notify = function (status) {
    var self = this;
    var notice = $('.notice-' + status);
    var delay = this.config.development === true ? 4000 : 2000;

    notice.show();

    window.setTimeout(function () {
      notice.addClass('show');
      self.button.removeClass(self.states.wait);

      window.setTimeout(function () {
        notice.removeClass('show');
        window.setTimeout(function () {
          notice.hide();
        }, 310);
      }, delay);
    }, 10);
  };

  var checkout = new BraintreePayform({
    formID: 'braintree-payment-form'
  });
} // SetupBraintreeCheckout()

function SetupStripeCheckout() {
  console.log('SetupStripeCheckout()')
  console.assert(window._userId != null)
  console.assert(window._recipientId != null)
  console.assert(window._stripePublishKey != null)
  console.assert(window._totalAmount != null)

  // Ref: https://stripe.com/docs/checkout#integration-custom
  var stripeSts = findPaymentGateways('stripe')
  console.assert(stripeSts != null)
  var checkoutImage = stripeSts.settings.stripe_checkout_image.value
  var locale = stripeSts.settings.stripe_checkout_locale.value

  var checkout = StripeCheckout.configure({
    key: window._stripePublishKey,
    image: checkoutImage,
    locale: locale,
    token: function (token) {
      // You can access the token ID with `token.id`.
      // Get the token ID to your server-side code for use.
      $('#btn_stripe_pay').addClass('disabled loading')
      $('#btn_back').addClass('disabled loading')

      console.assert(window._curPaymentMethod)
      console.assert(window._curPaymentMethodTitle)

      var gateway = findPaymentGateways(window._curPaymentMethod)
      console.assert(gateway != null)

      $.ajax({
        url: 'ws/checkout_submit',
        type: 'POST',
        data: JSON.stringify({
          user_id: window._userId,
          recipient_id: window._recipientId,
          order_id: window._orderId,
          currency: _shoppingCart.server_settings.currency.value,
          total: window._totalAmount.toString(),
          payment_method: window._curPaymentMethod,
          payment_method_title: window._curPaymentMethodTitle,
          gateway_settings: gateway.settings,
          stripe_token: token.id // special property for stripe
        }),
        contentType: 'application/json'
      }).done(function (result) {
        $('#stripe_errmsg').html('')
        console.assert(result.payment_id != null)
        window.location.href = 'payment_return?pid=' + result.payment_id
      }).fail(function(xhr, status, err) {
        $('#stripe_errmsg').html(err)
        $('#btn_stripe_pay').removeClass('disabled loading')
        $('#btn_back').removeClass('disabled loading')
        $.alert({
          type: 'red',
          useBootstrap: false,
          title: err,
          content: xhr.responseText,
        })
      })
    }
  });

  $('#btn_stripe_pay').click(function (e) {
    e.preventDefault() // disable form post

    if (!$('#shipping_form').form('is valid')) {
      return false
    }

    // Open Checkout with further options:
    checkout.open({
      name: 'Chatbot CMS',
      email: window._shoppingCart.input_info.billing.email,
      description: 'Chatbot CMS - WooCommerce Order',
      // zipCode: _shoppingCart.input_info.billing.postal,
      amount: _totalAmount * 100
    });
  });

  // Close Checkout on page navigation:
  window.addEventListener('popstate', function () {
    checkout.close();
  });
} // SetupStripeCheckout()

// Info source: https://developer.paypal.com/docs/classic/paypal-payments-standard/integration-guide/formbasics/
function genPayPalMarkup(items, isDebug, currency, customId, paypalAccount, urls) {
  console.assert(items && (items instanceof Array));
  console.assert(currency);
  console.assert(customId);
  console.assert(paypalAccount);
  console.assert(urls && urls.cancel && urls.success && urls.notify);

  var account = paypalAccount;
  if (isDebug)
    account = 'go-facilitator@simonho.net';
  var urlBase = document.baseURI.substring(0, document.baseURI.lastIndexOf('/')) + '/';

  var paypalUrl = isDebug
    ? 'https://www.sandbox.paypal.com/cgi-bin/webscr'
    : 'https://www.paypal.com/cgi-bin/webscr';
  var notifyUrl = urls.notify;
  var str = '';
  str += '<form method="post" action="' + paypalUrl + '">';
  str += '<input type="hidden" name="charset" value="utf-8">';
  str += '<input type="hidden" name="cmd" value="_cart">';
  str += '<input type="hidden" name="upload" value="1">';
  str += '<input type="hidden" name="business" value="' + account + '">';
  str += '<input type="hidden" name="currency_code" value="' + currency + '">';
  str += '<input type="hidden" name="custom" value="' + customId + '">'; // custom is Order ID
  str += '<input type="hidden" name="notify_url" value="' + notifyUrl + '">';
  str += '<input type="hidden" name="cancel_return" value="' + urls.cancel + '">';
  str += '<input type="hidden" name="return" value="' + urls.success + '">';

  var count = 1;
  var itemsString = "";

  for (var i = 0; i < items.length; ++i) {
    var item = items[i]
    console.assert(item.name);
    console.assert(item.qty);
    console.assert(item.price);
    console.assert(item.itemId);
    var count = i + 1;
    str += '<input type="hidden" name="item_name_' + count + '" value="' + item.name + '">';
    str += '<input type="hidden" name="quantity_' + count + '" value ="' + item.qty + '">';
    str += '<input type="hidden" name="amount_' + count + '" value="' + item.price + '">';
    str += '<input type="hidden" name="item_number_' + count + '" value="' + item.itemId + '">';
  }

  str += '</form>';

  return str;
} // genPayPalMarkup()

function findPaymentGateways(paymentId) {
  console.assert(paymentId != null)
  var result = null;
  for (var i = 0; i < window._wcPaymentGateways.length; ++i) {
    var gw = window._wcPaymentGateways[i]
    if (gw.id === paymentId) {
      result = gw
      break
    }
  }
  return result
}
