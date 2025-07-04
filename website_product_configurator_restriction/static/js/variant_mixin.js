odoo.define('website_product_configurator_restriction.variant_mixin', function (require) {
"use strict";

var ajax = require('web.ajax');
var VariantMixin = require('sale.VariantMixin');
console.log('\nVariantMixin---------', VariantMixin)

VariantMixin._onChangeColorAttribute(ev){
    this._super.apply(this, arguments);
    console.log('\nOnchange ev---------', ev)
}

// VariantMixin.selectOrCreateProduct = async function ($container, productId, productTemplateId, useAjax) {
//     var self = this;
//     productId = parseInt(productId);
//     var productReady = Promise.resolve();
//     // // Bypass custom value products
//     // if (productId) {
//     //     var route = '/check/exist_product';
//     //     await ajax.jsonRpc(route, 'call', {product_id: productId, kwargs:params})
//     //         .then(function (result) {
//     //             productReady = Promise.resolve(result);
//     //             productId = result
//     //         });
//     // }
//     productTemplateId = parseInt(productTemplateId);
//     // Get sol_type value from configurator and create Type in sale order line
//     var sol_type_val = null
//     var sol_type = document.getElementById('sol_type');
//     // // Edit
//     // if (self.state && self.state.data && self.state.data.sol_type && productId) {
//     //     sol_type_val = self.state.data.sol_type
//     //     // Update SOL type on product
//     //     ajax.jsonRpc('/update/soltype', 'call', {product_id: productId, sol_type: sol_type_val})
//     //     .then(function (result) {
//     //         // console.log('\n\n result-----',result)
//     //     });
//     // }
//     // Create
//     if (sol_type !== null) {
//         sol_type_val = sol_type.value
//     }
//     // Get price value from configurator and update price in sale order line
//     var priceinput = $container.find('.unit_price_input').val() || 1;
//     // Product already exist or open from edit button
//     if (productId) {
//         productReady = Promise.resolve(productId);
//         // Create bom for existing product
//         if (useAjax && productReady){
//             var bomroute = '/sale/create_exist_product_bom';
//             ajax.jsonRpc(bomroute, 'call', {product_id: productId, kwargs:params});
//             // Bypass custom value products
//             var route = '/check/exist_product';
//             await ajax.jsonRpc(route, 'call', {product_id: productId, price: priceinput, sol_type: sol_type_val, kwargs:params})
//                 .then(function (result) {
//                     productReady = Promise.resolve(result);
//                     productId = result
//                 });
//         }
//     } else {
//         var params = {
//             product_template_id: productTemplateId,
//             product_template_attribute_value_ids:
//                 JSON.stringify(self.getSelectedVariantValues($container)),
//             sol_type: sol_type_val,
//             price: priceinput,
//         };

//         // Custom input values
//         var custominput = $container
//             .find('.custom_value_radio') || [];
//         if (useAjax && (custominput.length > 0)){
//         // if (custominput.length > 0){
//             const custom_values = [];
//             // custom dictionary
//             _.each($container.find(custominput), function (el) {
//                 var cptav = $(el)[0].getAttribute('data-custom_product_template_attribute_value_id');
//                 var attr = el.parentElement.getAttribute('data-attribute_id');
//                 var catv = $(el).val();
//                 custom_values.push({
//                     'attribute_id': attr,
//                     'val': catv,
//                     'ptav': cptav
//                 });
//             });
//             // create custom ptav and set in params
//             var ptav_ids = params.product_template_attribute_value_ids

//             await ajax.jsonRpc(
//                 '/configurator/custom/ptav',
//                 'call',
//                 {product_tmpl_id: productTemplateId, custom_list: custom_values, ptav_ids: ptav_ids
//             }).then(function (result) {
//                 params.product_template_attribute_value_ids = result
//             });
//         }

//         var route = '/sale/create_product_variant';
//         if (useAjax) {
//             productReady = ajax.jsonRpc(route, 'call', params);
//             // Popup warning when raise error from python code
//             productReady.catch(function onFailure(e) {
//                 alert(JSON.stringify(e.message.data.message))
//             });
//         } else {
//             // create custom ptav and set in params
//             var ptav_ids = params.product_template_attribute_value_ids
//             if (custominput.length > 0){
//                 const custom_values = [];
//                 // custom dictionary
//                 _.each($container.find(custominput), function (el) {
//                     var cptav = $(el)[0].getAttribute('data-custom_product_template_attribute_value_id');
//                     var attr = el.parentElement.getAttribute('data-attribute_id');
//                     var catv = $(el).val();
//                     custom_values.push({
//                         'attribute_id': attr,
//                         'val': catv,
//                         'ptav': cptav
//                     });
//                 });
//                 await ajax.jsonRpc(
//                     '/configurator/custom/ptav',
//                     'call',
//                     {product_tmpl_id: productTemplateId, custom_list: custom_values, ptav_ids: ptav_ids
//                 }).then(function (result) {
//                     params.product_template_attribute_value_ids = result
//                 });
//             }
//             // // Get sol_type value from configurator and create Type in sale order line
//             // params.sol_type = sol_type_val

//             productReady = this._rpc({route: route, params: params});
//         }
//     }

//     return productReady;
// }

// // onchange values
// VariantMixin._getCombinationInfo = function (ev) {
//     if ($(ev.target).hasClass('variant_custom_value')) {
//         return Promise.resolve();
//     }

//     const $parent = $(ev.target).closest('.js_product');

//     const combination = this.getSelectedVariantValues($parent);
//     let parentCombination;
//     if ($parent.hasClass('main_product')) {
//         parentCombination = $parent.find('ul[data-attribute_exclusions]').data('attribute_exclusions').parent_combination;
//         const $optProducts = $parent.parent().find(`[data-parent-unique-id='${$parent.data('uniqueId')}']`);

//         for (const optionalProduct of $optProducts) {
//             const $currentOptionalProduct = $(optionalProduct);
//             const childCombination = this.getSelectedVariantValues($currentOptionalProduct);
//             const productTemplateId = parseInt($currentOptionalProduct.find('.product_template_id').val());
//             ajax.jsonRpc(this._getUri('/sale/get_combination_info'), 'call', {
//                 'product_template_id': productTemplateId,
//                 'product_id': this._getProductId($currentOptionalProduct),
//                 'combination': childCombination,
//                 'add_qty': parseInt($currentOptionalProduct.find('input[name="add_qty"]').val()),
//                 'pricelist_id': this.pricelistId || false,
//                 'parent_combination': combination,
//             }).then((combinationData) => {
//                 if (combinationData['result']){
//                     alert(combinationData['msg']);
//                 }
//                 else{
//                     this._onChangeCombination(ev, $currentOptionalProduct, combinationData);
//                     this._checkExclusions($currentOptionalProduct, childCombination, combinationData.parent_exclusions);
//                 }
//             });
//         }
//     } else {
//         parentCombination = this.getSelectedVariantValues(
//             $parent.parent().find('.js_product.in_cart.main_product')
//         );
//     }

//     return ajax.jsonRpc(this._getUri('/sale/get_combination_info'), 'call', {
//         'product_template_id': parseInt($parent.find('.product_template_id').val()),
//         'product_id': this._getProductId($parent),
//         'combination': combination,
//         'add_qty': parseInt($parent.find('input[name="add_qty"]').val()),
//         'pricelist_id': this.pricelistId || false,
//         'parent_combination': parentCombination,
//     }).then((combinationData) => {
//         if (combinationData['result']){
//             alert(combinationData['msg']);
//         }
//         else{
//             this._onChangeCombination(ev, $parent, combinationData);
//             this._checkExclusions($parent, combination, combinationData.parent_exclusions);
//         }
//     });
// }

});
