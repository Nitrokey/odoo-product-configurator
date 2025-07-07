# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController


class ConfigWebsiteSaleVariantController(WebsiteSaleVariantController):

    @http.route(['/check/configurator/restriction'], type='json', auth="user", methods=['POST'])
    def check_exist_product(self, product_template_id=False, attribute_id=False, ptav_id=False):
        """ bypass custom value product create time from sale product configurator"""
        updates = {'values': {}, 'domain': {}}
        product_template_id = request.env['product.template'].browse(int(product_template_id))
        ptav_id = request.env['product.template.attribute.value'].browse(int(ptav_id))
        attribute_id = request.env['product.attribute'].browse(int(attribute_id))
        all_domain = product_template_id.check_configurator_restriction(ptav_id, attribute_id, updates)
        # print('\n\n all_domain-------------',all_domain)
        return product_template_id.check_configurator_restriction(ptav_id, attribute_id, updates)
        # return product_template_id.values_available(ptav_id, attribute_id, custom_vals={}, product_tmpl_id=product_template_id)



# import json

# from odoo import http, models
# from odoo.exceptions import UserError, ValidationError
# from odoo.http import request
# from odoo.tools.safe_eval import safe_eval

# from odoo.addons.http_routing.models.ir_http import slug
# from odoo.addons.website_sale.controllers.main import WebsiteSale

# class WebsiteProductConfigSale(WebsiteSale):

#     @http.route(
#         "/website_product_configurator_restriction/onchange",
#         type="json",
#         methods=["POST"],
#         auth="public",
#         website=True,
#     )
#     def onchange(self, form_values, field_name, **post):
#         """Capture onchange events in the website and forward data to backend
#         onchange method"""
#         # config session and product template
#         product_configurator_obj = request.env["product.configurator"]
#         product_template_id = self.get_config_product_template(form_values)
#         try:
#             config_session_id = self.get_config_session(
#                 product_tmpl_id=product_template_id
#             )
#         except Exception as Ex:
#             return {"error": Ex}

#         # prepare dictionary in formate needed to pass in onchage
#         form_values = self.get_orm_form_vals(form_values, config_session_id)
#         config_vals = self._prepare_configurator_values(form_values, config_session_id)

#         # call onchange
#         specs = product_configurator_obj._onchange_spec()
#         updates = {}
#         try:
#             updates = product_configurator_obj.sudo().apply_onchange_values(
#                 values=config_vals, field_name=field_name, field_onchange=specs
#             )
#             updates["value"] = self.remove_recursive_list(updates["value"])
#         except Exception as Ex:
#             return {"error": Ex}

#         # get open step lines according to current configuation
#         value_ids = updates["value"].get("value_ids")
#         if not value_ids:
#             value_ids = self.get_current_configuration(form_values, config_session_id)
#         try:
#             open_cfg_step_line_ids = (
#                 config_session_id.sudo().get_open_step_lines(value_ids).ids
#             )
#         except Exception as Ex:
#             return {"error": Ex}

#         # if no step is defined or some attribute remains to add in a step
#         open_cfg_step_line_ids = [
#             "%s" % (step_id) for step_id in open_cfg_step_line_ids
#         ]
#         extra_attr_line_ids = self.get_extra_attribute_line_ids(product_template_id)
#         if extra_attr_line_ids:
#             open_cfg_step_line_ids.append("configure")

#         # configuration images
#         config_image_ids = config_session_id._get_config_image(value_ids=value_ids)
#         if not config_image_ids:
#             config_image_ids = product_template_id

#         image_vals = self.get_image_vals(
#             image_line_ids=config_image_ids,
#             model_name=config_image_ids[:1]._name,
#         )
#         pricelist = request.website.get_current_pricelist()
#         updates["open_cfg_step_line_ids"] = open_cfg_step_line_ids
#         updates["config_image_vals"] = image_vals
#         decimal_prec_obj = request.env["decimal.precision"]
#         updates["decimal_precision"] = {
#             "weight": decimal_prec_obj.precision_get("Stock Weight") or 2,
#             "price": pricelist.currency_id.decimal_places or 2,
#         }
#         print('\n\n updates--------------',updates)
#         return updates
