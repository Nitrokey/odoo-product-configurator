import json

from odoo import http, models
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools.safe_eval import safe_eval

from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import WebsiteSale


class ProductConfigWebsiteSale(WebsiteSale):

    @http.route()
    def product(self, product, category="", search="", **kwargs):
        # Use parent workflow for regular products
        return super(ProductConfigWebsiteSale, self).product(
            product, category, search, **kwargs
        )

    def convert_form_data(self, form_data):
        """convert the form data ptal to attribute"""
        ProductAttributeLine = request.env['product.template.attribute.line']
        form_values = []
        ptal_count = 0

        for item in form_data:
            name = item.get('name')
            value = item.get('value')

            # Map product_template_id
            if name == 'product_template_id':
                form_values.append({'name': 'product_tmpl_id', 'value': value})

            # Map product_id
            if name == 'product_id':
                form_values.append({'name': 'product_id', 'value': value})

            # Map each ptal-* line to __attribute-<attribute_id>
            elif name.startswith('ptal-') and value:
                ptal_id = int(name.split('-')[1])
                ptal = ProductAttributeLine.browse(ptal_id)
                if ptal.exists():
                    attribute_id = ptal.attribute_id.id
                    form_values.append({'name': f'__attribute-{attribute_id}', 'value': value})
                    ptal_count += 1

        # Optionally fill in empty attributes (not selected)
        product_tmpl_id = next((i['value'] for i in form_data if i['name'] == 'product_template_id'), False)
        if product_tmpl_id:
            ptal_lines = ProductAttributeLine.search([('product_tmpl_id', '=', int(product_tmpl_id))])
            for ptal in ptal_lines:
                key = f'__attribute-{ptal.attribute_id.id}'
                if not any(fv['name'] == key for fv in form_values):
                    form_values.append({'name': key, 'value': ''})  # empty value

            form_values.append({'name': 'total_attributes', 'value': str(len(ptal_lines))})

        return form_values

    @http.route(['/check/configurator/restriction'], type='json', auth="user", methods=['POST'])
    def check_exist_product(self, product_template_id=False, attribute_id=False, ptav_id=False, form_data={}):
        """ bypass custom value product create time from sale product configurator"""
        product_template_id = request.env['product.template'].browse(int(product_template_id))
        if not product_template_id or not (product_template_id and product_template_id.config_ok):
            return False
        # prepare dictionary in formate needed to pass in onchage
        form_values = self.convert_form_data(form_data)
        updates = {'form_data': form_values, 'values': {}, 'domain': {}}
        ptav_id = request.env['product.template.attribute.value'].browse(int(ptav_id))
        attribute_id = request.env['product.attribute'].browse(int(attribute_id))
        all_domain = product_template_id.check_configurator_restriction(ptav_id, attribute_id, updates)
        return all_domain
