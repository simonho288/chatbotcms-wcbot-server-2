"use strict";function SetupUI(){$(".ui.accordion").accordion(),$(".btn_pay").click(function(t){window._curPaymentMethod=$(this).data("paymentmethod"),window._curPaymentMethodTitle=$(this).data("paymentmethodtitle")}),$("#btn_back").click(onBtnBack),$("#btn_paypal_pay").click(OnPayWithPaypal),$("#btn_bacs_pay").click(OnPayWithBacs),$("#btn_cheque_pay").click(OnPayWithCheque),$("#btn_cod_pay").click(OnPayWithCod)}function OnPayWithPaypal(t){window._curPaymentMethod=$(this).data("paymentmethod"),window._curPaymentMethodTitle=$(this).data("paymentmethodtitle");$(this).data("email"),$(this).data("sandbox");var e=findPaymentGateways(window._curPaymentMethod);$(this).addClass("disabled loading"),$("#btn_back").addClass("disabled loading"),$.ajax({url:"ws/checkout_submit",type:"POST",data:JSON.stringify({user_id:window._userId,recipient_id:window._recipientId,order_id:window._orderId,currency:_shoppingCart.server_settings.currency.value,total:window._totalAmount.toString(),payment_method:window._curPaymentMethod,payment_method_title:window._curPaymentMethodTitle,gateway_settings:e.settings}),contentType:"application/json"}).done(function(t){window.location.href=t}).fail(function(t,e,n){$.alert({type:"red",useBootstrap:!1,title:n,content:t.responseText})})}function OnPayWithBacs(t){window._curPaymentMethod=$(this).data("paymentmethod"),window._curPaymentMethodTitle=$(this).data("paymentmethodtitle");var e=findPaymentGateways(window._curPaymentMethod);$(this).addClass("disabled loading"),$("#btn_back").addClass("disabled loading"),$.ajax({url:"ws/checkout_submit",type:"POST",data:JSON.stringify({user_id:window._userId,recipient_id:window._recipientId,order_id:window._orderId,currency:_shoppingCart.server_settings.currency.value,total:window._totalAmount.toString(),payment_method:window._curPaymentMethod,payment_method_title:window._curPaymentMethodTitle,gateway_settings:e.settings}),contentType:"application/json"}).done(function(t){window.location.href="payment_return?pid="+t.payment_id}).fail(function(t,e,n){$("#btn_bacs_pay").removeClass("disabled loading"),$("#btn_back").removeClass("disabled loading"),$.alert({type:"red",useBootstrap:!1,title:n,content:t.responseText})})}function OnPayWithCheque(){window._curPaymentMethod=$(this).data("paymentmethod"),window._curPaymentMethodTitle=$(this).data("paymentmethodtitle");var t=findPaymentGateways(window._curPaymentMethod);$(this).addClass("disabled loading"),$("#btn_back").addClass("disabled loading"),$.ajax({url:"ws/checkout_submit",type:"POST",data:JSON.stringify({user_id:window._userId,recipient_id:window._recipientId,order_id:window._orderId,currency:_shoppingCart.server_settings.currency.value,total:window._totalAmount.toString(),payment_method:window._curPaymentMethod,payment_method_title:window._curPaymentMethodTitle,gateway_settings:t.settings}),contentType:"application/json"}).done(function(t){window.location.href="payment_return?pid="+t.payment_id}).fail(function(t,e,n){$("#btn_cheque_pay").removeClass("disabled loading"),$("#btn_back").removeClass("disabled loading"),$.alert({type:"red",useBootstrap:!1,title:n,content:t.responseText})})}function OnPayWithCod(){window._curPaymentMethod=$(this).data("paymentmethod"),window._curPaymentMethodTitle=$(this).data("paymentmethodtitle");var t=findPaymentGateways(window._curPaymentMethod);$(this).addClass("disabled loading"),$("#btn_back").addClass("disabled loading"),$.ajax({url:"ws/checkout_submit",type:"POST",data:JSON.stringify({user_id:window._userId,recipient_id:window._recipientId,order_id:window._orderId,currency:_shoppingCart.server_settings.currency.value,total:window._totalAmount.toString(),payment_method:window._curPaymentMethod,payment_method_title:window._curPaymentMethodTitle,gateway_settings:t.settings}),contentType:"application/json"}).done(function(t){window.location.href="payment_return?pid="+t.payment_id}).fail(function(t,e,n){$("#btn_cod_pay").removeClass("disabled loading"),$("#btn_back").removeClass("disabled loading"),$.alert({type:"red",useBootstrap:!1,title:n,content:t.responseText})})}function RenderScreen(){for(var t="",e=0;e<window._wcPaymentGateways.length;++e){var n=window._wcPaymentGateways[e];if(n.enabled)switch(n.id){case"bacs":t+='<div class="title">',t+='<div class="dropdown icon"></div>',t+=n.title,t+="</div>",t+='<div class="content">',t+='<p class="transition hidden">',t+=n.description,t+="</p>",t+='<p class="transition hidden">',t+='<button class="ui primary button btn_pay" id="btn_bacs_pay" data-paymentmethod="'+n.id+'" data-paymentmethodtitle="'+n.title+'">',t+="Place Order",t+="</button>",t+="</p>",t+="</div>";break;case"cheque":t+='<div class="title">',t+='<div class="dropdown icon"></div>',t+=n.title,t+="</div>",t+='<div class="content">',t+='<p class="transition hidden">',t+=n.description,t+="</p>",t+='<p class="transition hidden">',t+='<button class="ui primary button btn_pay" id="btn_cheque_pay" data-paymentmethod="'+n.id+'" data-paymentmethodtitle="'+n.title+'">',t+="Place Order",t+="</button>",t+="</p>",t+="</div>";break;case"cod":t+='<div class="title">',t+='<div class="dropdown icon"></div>',t+=n.title,t+="</div>",t+='<div class="content">',t+='<p class="transition hidden">',t+=n.description,t+="</p>",t+='<p class="transition hidden">',t+='<button class="ui primary button btn_pay" id="btn_cod_pay" data-paymentmethod="'+n.id+'" data-paymentmethodtitle="'+n.title+'">',t+="Place Order",t+="</button>",t+="</p>",t+="</div>";break;case"paypal":t+='<div class="title">',t+='<div class="dropdown icon"></div>',t+=n.title,t+="</div>",t+='<div class="content">',t+='<p class="transition hidden">',t+=n.description,t+="</p>",t+='<p class="transition hidden">',t+='<button class="ui primary button btn_pay" id="btn_paypal_pay" data-paymentmethod="'+n.id+'" data-paymentmethodtitle="'+n.title+'" data-email="'+n.settings.email.value+'" data-sandbox="'+n.settings.testmode.value+'">',t+='<i class="paypal icon"></i>',t+="Paid By PayPal",t+="</button>",t+="</p>",t+="</div>";break;case"braintree_credit_card":t+='<div class="title">',t+='<div class="dropdown icon"></div>',t+=n.title,t+="</div>",t+='<div class="content">',t+='<p class="transition hidden">',t+=n.description,t+='<div class="field">',t+='<div class="bt-drop-in-wrapper">',t+='<div id="bt-dropin">',t+="</div>",t+="</div>",t+="</div>",t+='<input id="nonce" type="hidden" name="payment_method_nonce" />',t+='<button class="ui primary button btn_pay" id="btn_braintree_pay" data-paymentmethod="'+n.id+'" data-paymentmethodtitle="'+n.title+'">',t+='<i class="credit card alternative icon"></i>',t+="Paid by Braintree",t+="</button>",t+="</p>",t+='<p id="bt-errmsg" class="errmsg"></p>',t+="</div>";break;case"stripe":t+='<div class="title">',t+='<div class="dropdown icon"></div>',t+=n.title,t+="</div>",t+='<div class="content">',t+='<p class="transition hidden">',t+=n.description,t+="</p>",t+='<p class="transition hidden">',t+='<div class="field">',t+='<button class="ui primary button btn_pay" id="btn_stripe_pay" data-paymentmethod="'+n.id+'" data-paymentmethodtitle="'+n.title+'">',t+='<i class="stripe icon"></i>',t+="Paid By Stripe",t+="</button>",t+="</div>",t+="</p>",t+='<p id="stripe_errmsg" class="errmsg"></p>',t+="</div>"}}$("#payment_methods").html(t);t="";for(var i=0,a=0,d=(e=0,window._wcOrder.line_items.length);e<d;++e){var o=window._wcOrder.line_items[e];o.subtotal=parseFloat(o.subtotal),o.subtotal_tax=parseFloat(o.subtotal_tax),o.total=parseFloat(o.total),o.total_tax=parseFloat(o.total_tax);for(var s=null,r=0,l=window._shoppingCart.cart_items.length;r<l;++r){var c=window._shoppingCart.cart_items[r];if(c.product_id==o.product_id){s=c;break}}s.qty=parseFloat(s.qty),s.unit_price=parseFloat(s.unit_price),s.unit_tax=o.subtotal_tax/o.quantity,s.subtotal=o.subtotal+o.subtotal_tax,i+=o.subtotal,a+=o.subtotal_tax}var p=i+a+parseFloat(window._wcOrder.shipping_total)+parseFloat(window._wcOrder.shipping_tax);window._totalAmount=parseFloat(p.toFixed(5));var u=util.ParseCurrencyToDisp(window._shoppingCart.server_settings.currency,p);$("#total_amount").html(u)}function LoadShoppingCart(){return $.ajax({method:"GET",url:"ws/db_loadcart",data:{uid:window._userId,rid:window._recipientId}})}function LoadWcOrder(){return $.ajax({method:"GET",url:"get_wc_order",data:{uid:window._userId,rid:window._recipientId,oid:window._orderId}})}function LoadWcPaymentGateways(){return $.ajax({method:"GET",url:"get_wc_paygates",data:{uid:window._userId,rid:window._recipientId}})}function RemoveWcOrder(){return $.ajax({type:"DELETE",url:"ws/delete_order",data:{oid:window._orderId,uid:window._userId,rid:window._recipientId}})}function EnableAllButtons(t){t?$("#btn_back").removeClass("disabled loading"):$("#btn_back").addClass("disabled loading")}function onBtnBack(t){var e=$("#dlg_discardwarn");e.modal("show"),e.find("#btn_ok").click(function(t){EnableAllButtons(!1),RemoveWcOrder().done(function(){var t="mwp?page=shopCart&uid="+window._userId+"&rid="+window._recipientId;window.location.href=t}).fail(function(t,e,n){$.alert({type:"red",useBootstrap:!1,title:n,content:t.responseText})})}),e.find("#btn_cancel").click(function(t){$("#dlg_discardwarn").modal("hide")})}function SetupBraintreeCheckout(){document.querySelector("#braintree-payment-form");var t=window._braintreeClientToken;function e(t){this.config=t,this.config.development=t.development||!1,this.paymentForm=$("#"+t.formID),this.inputs=$("input[type=text], input[type=email], input[type=tel]"),this.button=this.paymentForm.find(".button"),this.states={show:"active",wait:"loading"},this.focusClass="has-focus",this.valueClass="has-value",this.initialize()}braintree.dropin.create({authorization:t,container:"#bt-dropin",paypal:{flow:"vault"}},function(t,e){t?$.alert({type:"red",useBootstrap:!1,title:"Error",content:t}):$("#btn_braintree_pay").click(function(t){t.preventDefault(),e.requestPaymentMethod(function(t,e){if(!t){$("#btn_braintree_pay").addClass("disabled loading"),$("#btn_back").addClass("disabled loading");var n=findPaymentGateways(window._curPaymentMethod);$.ajax({url:"ws/checkout_submit",type:"POST",data:JSON.stringify({user_id:window._userId,recipient_id:window._recipientId,order_id:window._orderId,currency:_shoppingCart.server_settings.currency.value,total:window._totalAmount.toString(),payment_method:window._curPaymentMethod,payment_method_title:window._curPaymentMethodTitle,gateway_settings:n.settings,braintree_nonce:e.nonce}),contentType:"application/json"}).done(function(t){$("#bt-errmsg").html(""),window.location.href="payment_return?pid="+t.payment_id}).fail(function(t,e,n){$("#bt-errmsg").html(n.statusText),$("#btn_braintree_pay").removeClass("disabled loading"),$("#btn_back").removeClass("disabled loading"),$.alert({type:"red",useBootstrap:!1,title:n,content:t.responseText})})}})})}),e.prototype.initialize=function(){var t=this;this.events(),this.inputs.each(function(e,n){t.labelHander($(n))}),this.notify("error")},e.prototype.events=function(){var t=this;this.inputs.on("focus",function(){$(this).closest("label").addClass(t.focusClass),t.labelHander($(this))}).on("keydown",function(){t.labelHander($(this))}).on("blur",function(){$(this).closest("label").removeClass(t.focusClass),t.labelHander($(this))})},e.prototype.labelHander=function(t){var e=this,n=t,i=n.closest("label");window.setTimeout(function(){n.val().length>0?i.addClass(e.valueClass):i.removeClass(e.valueClass)},10)},e.prototype.notify=function(t){var e=this,n=$(".notice-"+t),i=!0===this.config.development?4e3:2e3;n.show(),window.setTimeout(function(){n.addClass("show"),e.button.removeClass(e.states.wait),window.setTimeout(function(){n.removeClass("show"),window.setTimeout(function(){n.hide()},310)},i)},10)};new e({formID:"braintree-payment-form"})}function SetupStripeCheckout(){var t=findPaymentGateways("stripe"),e=t.settings.stripe_checkout_image.value,n=t.settings.stripe_checkout_locale.value,i=StripeCheckout.configure({key:window._stripePublishKey,image:e,locale:n,token:function(t){$("#btn_stripe_pay").addClass("disabled loading"),$("#btn_back").addClass("disabled loading");var e=findPaymentGateways(window._curPaymentMethod);$.ajax({url:"ws/checkout_submit",type:"POST",data:JSON.stringify({user_id:window._userId,recipient_id:window._recipientId,order_id:window._orderId,currency:_shoppingCart.server_settings.currency.value,total:window._totalAmount.toString(),payment_method:window._curPaymentMethod,payment_method_title:window._curPaymentMethodTitle,gateway_settings:e.settings,stripe_token:t.id}),contentType:"application/json"}).done(function(t){$("#stripe_errmsg").html(""),window.location.href="payment_return?pid="+t.payment_id}).fail(function(t,e,n){$("#stripe_errmsg").html(n),$("#btn_stripe_pay").removeClass("disabled loading"),$("#btn_back").removeClass("disabled loading"),$.alert({type:"red",useBootstrap:!1,title:n,content:t.responseText})})}});$("#btn_stripe_pay").click(function(t){if(t.preventDefault(),!$("#shipping_form").form("is valid"))return!1;i.open({name:"Chatbot CMS",email:window._shoppingCart.input_info.billing.email,description:"Chatbot CMS - WooCommerce Order",amount:100*_totalAmount})}),window.addEventListener("popstate",function(){i.close()})}function genPayPalMarkup(t,e,n,i,a,d){var o=a;e&&(o="go-facilitator@simonho.net");document.baseURI.substring(0,document.baseURI.lastIndexOf("/"));var s="";s+='<form method="post" action="'+(e?"https://www.sandbox.paypal.com/cgi-bin/webscr":"https://www.paypal.com/cgi-bin/webscr")+'">',s+='<input type="hidden" name="charset" value="utf-8">',s+='<input type="hidden" name="cmd" value="_cart">',s+='<input type="hidden" name="upload" value="1">',s+='<input type="hidden" name="business" value="'+o+'">',s+='<input type="hidden" name="currency_code" value="'+n+'">',s+='<input type="hidden" name="custom" value="'+i+'">',s+='<input type="hidden" name="notify_url" value="'+d.notify+'">',s+='<input type="hidden" name="cancel_return" value="'+d.cancel+'">',s+='<input type="hidden" name="return" value="'+d.success+'">';for(var r=1,l=0;l<t.length;++l){var c=t[l];s+='<input type="hidden" name="item_name_'+(r=l+1)+'" value="'+c.name+'">',s+='<input type="hidden" name="quantity_'+r+'" value ="'+c.qty+'">',s+='<input type="hidden" name="amount_'+r+'" value="'+c.price+'">',s+='<input type="hidden" name="item_number_'+r+'" value="'+c.itemId+'">'}return s+="</form>"}function findPaymentGateways(t){for(var e=null,n=0;n<window._wcPaymentGateways.length;++n){var i=window._wcPaymentGateways[n];if(i.id===t){e=i;break}}return e}$(document).ready(function(){RenderScreen(),$(".loading_wrapper").hide(),$(".loaded_wrapper").show(),SetupUI(),SetupBraintreeCheckout(),SetupStripeCheckout()});