import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    restrict_config_ok = fields.Boolean(string="Restricted Product")
    restrict_config_line_ids = fields.One2many(
        comodel_name="website.product.config.line",
        inverse_name="product_tmpl_id",
        string="Attribute Dependencies",
        copy=False,
    )

    def toggle_config(self):
        for record in self:
            record.restrict_config_ok = not record.restrict_config_ok

    def validate_domains_against_sels(self, domains, value_ids=None):

        if value_ids is None:
            value_ids = self.value_ids.ids

        # process domains as shown in this wikipedia pseudocode:
        # https://en.wikipedia.org/wiki/Polish_notation#Order_of_operations
        stack = []
        for domain in reversed(domains):
            if type(domain) == tuple:
                # evaluate operand and push to stack
                if domain[1] == "in":
                    if not set(domain[2]) & set(value_ids):
                        stack.append(False)
                        continue
                else:
                    if set(domain[2]) & set(value_ids):
                        stack.append(False)
                        continue
                stack.append(True)
            else:
                # evaluate operator and previous 2 operands
                # compute_domain() only inserts 'or' operators
                # compute_domain() enforces 2 operands per operator
                operand1 = stack.pop()
                operand2 = stack.pop()
                stack.append(operand1 or operand2)

        # 'and' operator is implied for remaining stack elements
        avail = True
        while stack:
            avail &= stack.pop()
        return avail

    def update_restrict_dict(self, ptav, attribute_id, updates):
        value_id = ptav.product_attribute_value_id
        value_ids = attribute_id.value_ids.ids

        # Find matching config lines where the selected value is in domain
        restrict_lines = self.restrict_config_line_ids.filtered(
            lambda line: any(value_id.id in domain_line.value_ids.ids for domain_line in line.domain_id.domain_line_ids)
        )

        for line in restrict_lines:
            domains = line.domain_id.compute_domain()
            # For Changed values
            if self.validate_domains_against_sels(domains, value_ids):
                available_lines = line.value_ids.mapped('name')
                operator = domains[0][1]

                if operator == 'in':
                    available_lines = line.value_ids.mapped('name')
                else:
                    allowed_values = line.attribute_line_id.value_ids - line.value_ids
                    available_lines = allowed_values.mapped('name')

                updates['values'].update({attribute_id.name: value_id.name})
                updates['domain'].update({
                    line.attribute_line_id.attribute_id.name: [
                        line.attribute_line_id.value_ids.mapped('name'),
                        available_lines,
                        operator,
                    ]
                })
        return updates

    def check_configurator_restriction(self, ptav, attribute_id, updates):
        """Check restriction conditions and update the values"""
        # Existing values domain
        form_data = updates['form_data']
        attribute_values = {
            item['name'].replace('__attribute-', ''): item['value']
            for item in form_data
            if item['name'].startswith('__attribute-')
        }
        for attribute, value in attribute_values.items():
            attribute_id = self.env['product.attribute'].browse(int(attribute))
            ptav = self.env['product.template.attribute.value'].browse(int(value))
            updates = self.update_restrict_dict(ptav, attribute_id, updates)

        updates = self.update_restrict_dict(ptav, attribute_id, updates)
        return updates

    @api.model
    def check_config_user_access(self):
        """Check user have access to perform action(create/write/delete)
        on configurable products"""
        user_root = self.env.ref("base.user_root")
        user_admin = self.env.ref("base.user_admin")
        if (
            self.env.user.id in [user_root.id, user_admin.id]
            or self.env.su
        ):
            return True
        raise ValidationError(
            _(
                "Sorry, you are not allowed to create/change this kind of "
                "document. For more information please contact your manager."
            )
        )

    @api.model
    def create(self, vals):
        """Patch for check access rights of user(configurable products)"""
        restrict_config_ok = vals.get("restrict_config_ok", False)
        if restrict_config_ok:
            self.check_config_user_access()
        return super(ProductTemplate, self).create(vals)
