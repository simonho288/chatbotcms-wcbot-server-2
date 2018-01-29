"use strict";function SetupUI(){var e=$("#shipping_fee_form");e.form({on:"blur",inline:!0,fields:{ship_method:["empty"]}}),e.submit(function(e){return e.preventDefault(),!1}),$("#btn_proceed").click(onBtnProceed),$("#btn_back").click(onBtnBack)}function LoadShoppingCart(){return $.ajax({method:"GET",url:"ws/db_loadcart",data:{uid:window._userId,rid:window._recipientId}})}function LoadWcShipSetting(){return $.ajax({method:"GET",url:"ws/get_wc_ship_setting",timeout:15e3,data:{uid:window._userId,rid:window._recipientId}})}function renderShipInfo(){function e(e){return e&&e.length>0?e:"--"}$("#first_name").html(e(window._wcOrder.shipping.first_name)),$("#last_name").html(e(window._wcOrder.shipping.last_name)),$("#address1").html(e(window._wcOrder.shipping.address_1)),$("#address2").html(window._wcOrder.shipping.address_2),$("#city").html(e(window._wcOrder.shipping.city)),$("#state").html(e(window._wcOrder.shipping.state)),$("#postcode").html(e(window._wcOrder.shipping.postcode)),$("#country").html(e(window._wcOrder.shipping.country))}function CalculateTotal(){var e=0,t=0;window._wcOrder.line_items.forEach(function(n){e+=parseFloat(n.subtotal),t+=parseFloat(n.total_tax)}),window._totalAmount=e;var n=util.ParseCurrencyToDisp(window._shoppingCart.server_settings.currency,e);$("#order_totalamt").html(n);for(var i=[],o=null,r=0,d=_shipSettings.length;r<d;r++){var a=_shipSettings[r];if(0===a.locations.length)o=a;else{for(var s=!1,l=!1,p=!1,c=0,w=a.locations.length;c<w;c++){var u=a.locations[c];"country"===u.type?u.code===_wcOrder.shipping.country&&(s=!0):"postcode"===u.type&&(l=!0,IsPostcodeMatch(u.code,_wcOrder.shipping.postcode)&&(p=!0))}s&&(l?p&&i.push(a):i.push(a))}}var _='<option value="">Please select</option>';if(0===i.length)_+=MethodsToSelectOptionsMarkup("Locations not covered",o.methods);else for(r=0,d=i.length;r<d;++r){var h=i[r];_+=MethodsToSelectOptionsMarkup(h.zone.name,h.methods)}$('[name="ship_method"]').html(_);n=util.ParseCurrencyToDisp(window._shoppingCart.server_settings.currency,t);$("#order_totaltax").html(n)}function MethodsToSelectOptionsMarkup(e,t){for(var n=window._shoppingCart.server_settings.currency,i="",o=0;o<t.length;++o){var r,d,a=t[o];switch(d=e+": ",a.method_id){case"free_shipping":if(r=0,"min_amount"===a.settings.requires.value){var s=parseFloat(a.settings.min_amount.value);if(window._totalAmount<s)continue}d+=a.method_title,d+=": Fee "+util.ParseCurrencyToDisp(n,0);break;case"flat_rate":case"local_pickup":r=ParseAndCalcShipCost(a.settings.cost.value),d+=a.method_title+": Fee "+util.ParseCurrencyToDisp(n,r)}i+="<option ",i+='value="'+a.method_id+'"',i+='data-title="'+a.method_title+'"',i+='data-cost="'+r+'">',i+=d,i+="</option>"}return i}function IsPostcodeMatch(e,t){var n=t.toLowerCase().trim(),i=e.toLowerCase().split("-");if(1===i.length)return i[0].trim()===n;if(2===i.length){var o=parseInt(i[0].trim()),r=parseInt(i[1].trim());if(o>r){var d=r;r=o,o=d}return(n=parseInt(n))>=o&&n<=r}return!1}function ParseAndCalcShipCost(e){if(null==e||""==e)return 0;var t=e.toLowerCase();return ParseWithLexer(t)}function EnableAllButtons(e){e?($("#btn_proceed").removeClass("disabled loading"),$("#btn_back").removeClass("disabled loading")):($("#btn_proceed").addClass("disabled loading"),$("#btn_back").addClass("disabled loading"))}function onBtnBack(e){e.preventDefault(),EnableAllButtons(!1),$.ajax({type:"DELETE",url:"ws/delete_order",data:{oid:window._orderId,uid:window._userId,rid:window._recipientId}}).done(function(e){"ok"===e&&(window.location.href="mwp?page=orderInfoInput&oid="+window._orderId+"&uid="+window._userId+"&rid="+window._recipientId)}).fail(function(e,t,n){EnableAllButtons(!0)})}function onBtnProceed(e){$("#shipping_fee_form").form("validate form")&&(EnableAllButtons(!1),$.when(SaveCart(),UpdateWcOrder()).done(function(e,t){"success"===e[1]&&"success"===t[1]&&(window.location.href="mwp?page=orderReview&oid="+window._orderId+"&uid="+window._userId+"&rid="+window._recipientId)}).fail(function(e,t,n){EnableAllButtons(!0)}))}function SaveCart(){delete window._shoppingCart.input_info,delete window._shoppingCart.cart_items,delete window._shoppingCart.server_settings,delete window._shoppingCart.order_pool;var e=$('[name="ship_method"]');return window._shoppingCart.ship_info={wc_order_id:window._wcOrder.id.toString(),method:e.val(),cost:e.find(":selected").data("cost")},$.ajax({type:"POST",url:"ws/db_savecart",data:JSON.stringify({userId:window._userId,recipientId:window._recipientId,cart:window._shoppingCart}),contentType:"application/json"})}function UpdateWcOrder(){var e=$('[name="ship_method"]').find(":selected"),t={shipping_lines:[{method_id:e.val(),method_title:e.data("title"),total:numeral(e.data("cost")).format("0.00")}]};return $.ajax({type:"PUT",url:"ws/update_order",data:{userId:window._userId,recipientId:window._recipientId,orderId:window._orderId,updateProps:JSON.stringify(t)}})}$(document).ready(function(){renderShipInfo(),CalculateTotal(),$(".loading_wrapper").hide(),$(".loaded_wrapper").show(),SetupUI()});