odoo.define('website_product_configurator_restriction.VariantMixin', function (require) {
"use strict";

var ajax = require('web.ajax');
var VariantMixin = require('sale.VariantMixin');

VariantMixin.handleCustomValues = function ($target) {
    var $variantContainer;
    var $customInput = false;
    if ($target.is('input[type=radio]') && $target.is(':checked')) {
        $variantContainer = $target.closest('ul').closest('li');
        $customInput = $target;
    } else if ($target.is('select')) {
        $variantContainer = $target.closest('li');
        $customInput = $target
            .find('option[value="' + $target.val() + '"]');
    }
    
    if ($variantContainer) {

// Customisation Start
        const $parent = $($target).closest('.js_product');
        var productTemplateId = parseInt($parent.find('.product_template_id').val())
        var attributeId = $variantContainer.data('attribute_id');
        var PTAVId = $customInput.data('value_id');
        const form_data = $parent.find('input, select, textarea').serializeArray();

        var route = '/check/configurator/restriction';
        ajax.jsonRpc(route, 'call', {
            product_template_id: productTemplateId,
            attribute_id: attributeId,
            ptav_id: PTAVId,
            form_data: form_data,
        }).then(function (data) {
            if(data && data.is_configured){
                const domainData = data.domain;
                _.each(domainData, function (valueArray, attributeName) {
                    const allOptions = valueArray[0];  // ["White", "Black"]
                    const allowedOptions = valueArray[1];  // ["White"]
                    const operator = valueArray[2]; // e.g. "in"
                    // console.log(`\n\nAttribute: ${attributeName}`);
                    // console.log('All options:', allOptions);
                    // console.log('Allowed options:', allowedOptions);
                    const $selectOptions = $(`option[data-attribute_name="${attributeName}"]`);
                    const $radioOptions = $(`input[data-attribute_name="${attributeName}"]`);
                    const $alloptions = [...$selectOptions, ...$radioOptions];

                    if ($alloptions.length) {
                        $alloptions.forEach(function (opt) {
                            const $opt = $(opt);
                            const valueName = $opt.data('value_name');
                            // Disable if not in allowed options
                            if (!allowedOptions.includes(valueName)) {
                                $opt.prop('disabled', true);
                                console.log(`❌ Disabled: ${valueName}`);
                            } else {
                                $opt.prop('disabled', false);
                                console.log(`✅ Enabled: ${valueName}`);
                            }
                        });
                    }
            });                
            }
        });
// Customisation End
            if ($customInput && $customInput.data('is_custom') === 'True') {
                var attributeValueId = $customInput.data('value_id');
                var attributeValueName = $customInput.data('value_name');

                if ($variantContainer.find('.variant_custom_value').length === 0
                        || $variantContainer
                              .find('.variant_custom_value')
                              .data('custom_product_template_attribute_value_id') !== parseInt(attributeValueId)) {
                    $variantContainer.find('.variant_custom_value').remove();

                    const previousCustomValue = $customInput.attr("previous_custom_value");
                    var $input = $('<input>', {
                        type: 'text',
                        'data-custom_product_template_attribute_value_id': attributeValueId,
                        'data-attribute_value_name': attributeValueName,
                        class: 'variant_custom_value form-control mt-2'
                    });

                    $input.attr('placeholder', attributeValueName);
                    $input.addClass('custom_value_radio');
                    $variantContainer.append($input);
                    if (previousCustomValue) {
                        $input.val(previousCustomValue);
                    }
                }
            } else {
                $variantContainer.find('.variant_custom_value').remove();
            }
    }
}

});
