import logging
from io import StringIO

from mako.runtime import Context
from mako.template import Template

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # @api.depends("product_variant_ids.product_tmpl_id")
    # def _compute_product_variant_count(self):
    #     """For configurable products return the number of variants configured or
    #     1 as many views and methods trigger only when a template has at least
    #     one variant attached. Since we create them from the template we should
    #     have access to them always"""
    #     res = super(ProductTemplate, self)._compute_product_variant_count()
    #     for product_tmpl in self:
    #         restrict_config_ok = product_tmpl.restrict_config_ok
    #         variant_count = product_tmpl.product_variant_count
    #         if restrict_config_ok and not variant_count:
    #             product_tmpl.product_variant_count = 1
    #     return res

    # @api.depends("attribute_line_ids.value_ids")
    # def _compute_template_attr_vals(self):
    #     """Compute all attribute values added in attribute line on
    #     product template"""
    #     for product_tmpl in self:
    #         if product_tmpl.restrict_config_ok:
    #             value_ids = product_tmpl.attribute_line_ids.mapped("value_ids")
    #             product_tmpl.attribute_line_val_ids = value_ids
    #         else:
    #             product_tmpl.attribute_line_val_ids = False

    # @api.constrains("attribute_line_ids", "attribute_value_line_ids")
    # def check_attr_value_ids(self):
    #     """Check attribute lines don't have some attribute value that
    #     is not present in attribute lines of that product template"""
    #     for product_tmpl in self:
    #         if not product_tmpl.env.context.get("check_constraint", True):
    #             continue
    #         attr_val_lines = product_tmpl.attribute_value_line_ids
    #         attr_val_ids = attr_val_lines.mapped("value_ids")
    #         if not attr_val_ids <= product_tmpl.attribute_line_val_ids:
    #             raise ValidationError(
    #                 _(
    #                     "All attribute values used in attribute value lines "
    #                     "must be defined in the attribute lines of the "
    #                     "template"
    #                 )
    #             )

    # @api.constrains("attribute_value_line_ids")
    # def _validate_unique_config(self):
    #     """Check for duplicate configurations for the same
    #     attribute value in image lines"""
    #     for template in self:
    #         attr_val_line_vals = template.attribute_value_line_ids.read(
    #             ["value_id", "value_ids"], load=False
    #         )
    #         attr_val_line_vals = [
    #             (line["value_id"], tuple(line["value_ids"]))
    #             for line in attr_val_line_vals
    #         ]
    #         if len(set(attr_val_line_vals)) != len(attr_val_line_vals):
    #             raise ValidationError(
    #                 _("You cannot have a duplicate configuration for the " "same value")
    #             )

    restrict_config_ok = fields.Boolean(string="Restricted Product")
    restrict_config_line_ids = fields.One2many(
        comodel_name="website.product.config.line",
        inverse_name="product_tmpl_id",
        string="Attribute Dependencies",
        copy=False,
    )

    # @api.depends("weight_dummy", "product_variant_ids", "product_variant_ids.weight")
    # def _compute_weight(self):
    #     config_products = self.filtered(lambda template: template.restrict_config_ok)
    #     for product in config_products:
    #         product.weight = product.weight_dummy
    #     standard_products = self - config_products
    #     return super(ProductTemplate, standard_products)._compute_weight()

    # # pylint:disable=missing-return
    # def _set_weight(self):
    #     for product_tmpl in self:
    #         product_tmpl.weight_dummy = product_tmpl.weight
    #         if not product_tmpl.restrict_config_ok:
    #             super(ProductTemplate, product_tmpl)._set_weight()

    # def _check_default_values(self):
    #     default_val_ids = (
    #         self.attribute_line_ids.filtered(lambda l: l.default_val)
    #         .mapped("default_val")
    #         .ids
    #     )

    #     cfg_session_obj = self.env["product.config.session"]
    #     try:
    #         cfg_session_obj.validate_configuration(
    #             value_ids=default_val_ids, product_tmpl_id=self.id, final=False
    #         )
    #     except ValidationError as ex:
    #         raise ValidationError(ex.name) from ex
    #     except Exception as ex:
    #         raise ValidationError(
    #             _("Default values provided generate an invalid configuration")
    #         ) from ex

    # @api.constrains("restrict_config_line_ids", "attribute_line_ids")
    # def _check_default_value_domains(self):
    #     for template in self:
    #         try:
    #             template._check_default_values()
    #         except ValidationError as e:
    #             raise ValidationError(
    #                 _(
    #                     "Restrictions added make the current default values "
    #                     "generate an invalid configuration.\
    #                   \n%s"
    #                 )
    #                 % (e.name)
    #             ) from e

    def toggle_config(self):
        for record in self:
            record.restrict_config_ok = not record.restrict_config_ok

    def _create_variant_ids(self):
        """Prevent configurable products from creating variants as these serve
        only as a template for the product configurator"""
        templates = self.filtered(lambda t: not t.restrict_config_ok)
        if not templates:
            return None
        return super(ProductTemplate, templates)._create_variant_ids()

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


    # @api.model
    # def values_available(
    #     self,
    #     check_val_ids=None,
    #     value_ids=None,
    #     custom_vals=None,
    #     product_tmpl_id=None,
    # ):
    #     """Determines whether the attr_values from the product_template
    #     are available for selection given the configuration ids and the
    #     dependencies set on the product template

    #     :param check_val_ids: list of attribute value ids to check for
    #                           availability
    #     :param value_ids: list of attribute value ids
    #     :param custom_vals: custom values dict {attr_id: custom_val}

    #     :returns: list of available attribute values
    #     """
    #     if check_val_ids is None:
    #         check_val_ids = self.value_ids.ids
    #     elif check_val_ids:
    #         check_val_ids = check_val_ids.copy()
    #     if product_tmpl_id:
    #         product_tmpl = self.env["product.template"].browse(product_tmpl_id)
    #     else:
    #         product_tmpl = self

    #     product_tmpl.ensure_one()

    #     if value_ids is None:
    #         value_ids = self.value_ids.ids
    #     elif value_ids:
    #         value_ids = value_ids.copy()

    #     if custom_vals is None:
    #         custom_vals = self._get_custom_vals_dict()

    #     avail_val_ids = []
    #     for attr_val_id in check_val_ids:
    #         config_lines = product_tmpl.config_line_ids.filtered(
    #             lambda l: attr_val_id in l.value_ids.ids
    #         )
    #         domains = config_lines.mapped("domain_id").compute_domain()
    #         avail = self.validate_domains_against_sels(domains, value_ids, custom_vals)
    #         if avail:
    #             avail_val_ids.append(attr_val_id)
    #         elif attr_val_id in value_ids:
    #             value_ids.remove(attr_val_id)

    #     return avail_val_ids

    def check_configurator_restriction(self, ptav, attribute_id):
        print('\n\n Product------------', self)
        print('\n\n ptav Name------------', attribute_id.name, '----------', ptav.name)
        # print('\n\n value_ids Name------------', self.restrict_config_line_ids.value_ids.mapped('name'))
        # print('\n\n self.restrict_config_line_ids------------', self.restrict_config_line_ids)
        domain = {}#[]
        # restrict_line = self.restrict_config_line_ids.filtered(
        #     lambda a: a.attribute_line_id.attribute_id.id == attribute_id.id).value_ids.filtered(
        #     lambda l: ptav.name == l.name)
        value_id = ptav.product_attribute_value_id.id
        value_ids = attribute_id.value_ids.ids
        restrict_line = self.env['website.product.config.line'].browse()  # empty recordset
        for line in self.restrict_config_line_ids:
            check_line = line.domain_id.domain_line_ids.filtered(
                lambda l: value_id in l.value_ids.ids)
            if check_line:
                restrict_line |= line  # add line to the recordse
        print('\n\n Doamin----------', restrict_line.mapped("domain_id"))
        # restrict_line = self.restrict_config_line_ids.filtered(
        #     lambda l: value_id in l.value_ids.ids)
        # print('\n\n Doamin----------', restrict_line.mapped("domain_id"))
        domains = restrict_line.mapped("domain_id").compute_domain()
        print('\n\n domains----------', domains)
        # print('\n\n value_ids----------', value_ids)
        avail = self.validate_domains_against_sels(domains, value_ids)
        if avail:
            print('\n\n Value----------', ptav.product_attribute_value_id.name)
            # domain.extend(restrict_line.value_ids.ids)
            domain.update({attribute_id.name: restrict_line.value_ids.mapped('name')})
        elif value_id in value_ids:
            value_ids.remove(value_id)
        print('\n\n domain----------', domain)

        return domain

    # def unlink(self):
    #     """- Prevent the removal of configurable product templates
    #         from variants
    #     - Patch for check access rights of user(configurable products)"""
    #     configurable_templates = self.filtered(lambda template: template.restrict_config_ok)
    #     if configurable_templates:
    #         configurable_templates[:1].check_config_user_access()
    #     for config_template in configurable_templates:
    #         variant_unlink = config_template.env.context.get(
    #             "unlink_from_variant", False
    #         )
    #         if variant_unlink:
    #             self -= config_template
    #     res = super(ProductTemplate, self).unlink()
    #     return res

    # def copy(self, default=None):
    #     """Copy restrictions, config Steps and attribute lines
    #     ith product template"""
    #     if not default:
    #         default = {}
    #     self = self.with_context(check_constraint=False)
    #     res = super(ProductTemplate, self).copy(default=default)

    #     # Attribute lines
    #     attribute_line_dict = {}
    #     for line in res.attribute_line_ids:
    #         attribute_line_dict.update({line.attribute_id.id: line.id})

    #     # Restrictions
    #     for line in self.restrict_config_line_ids:
    #         old_restriction = line.domain_id
    #         new_restriction = old_restriction.copy()
    #         config_line_default = {
    #             "product_tmpl_id": res.id,
    #             "domain_id": new_restriction.id,
    #         }
    #         new_attribute_line_id = attribute_line_dict.get(
    #             line.attribute_line_id.attribute_id.id, False
    #         )
    #         if not new_attribute_line_id:
    #             continue
    #         config_line_default.update({"attribute_line_id": new_attribute_line_id})
    #         line.copy(config_line_default)

    #     # Config steps
    #     config_step_line_default = {"product_tmpl_id": res.id}
    #     for line in self.config_step_line_ids:
    #         new_attribute_line_ids = [
    #             attribute_line_dict.get(old_attr_line.attribute_id.id)
    #             for old_attr_line in line.attribute_line_ids
    #             if old_attr_line.attribute_id.id in attribute_line_dict
    #         ]
    #         if new_attribute_line_ids:
    #             config_step_line_default.update(
    #                 {"attribute_line_ids": [(6, 0, new_attribute_line_ids)]}
    #             )
    #         line.copy(config_step_line_default)
    #     return res

    # def configure_product(self):
    #     """launches a product configurator wizard with a linked
    #     template in order to configure new product."""
    #     return self.with_context(product_tmpl_id_readonly=True).create_config_wizard(
    #         click_next=False
    #     )

    # def create_config_wizard(
    #     self,
    #     model_name="product.configurator",
    #     extra_vals=None,
    #     click_next=True,
    # ):
    #     """create product configuration wizard
    #     - return action to launch wizard
    #     - click on next step based on value of click_next"""
    #     wizard_obj = self.env[model_name]
    #     wizard_vals = {"product_tmpl_id": self.id}
    #     if extra_vals:
    #         wizard_vals.update(extra_vals)
    #     wizard = wizard_obj.create(wizard_vals)
    #     if click_next:
    #         action = wizard.action_next_step()
    #     else:
    #         wizard_obj = wizard_obj.with_context(
    #             wizard_model=model_name,
    #             allow_preset_selection=True,
    #         )
    #         action = wizard_obj.get_wizard_action(wizard=wizard)
    #     return action

    # @api.model
    # def _check_config_group_rights(self):
    #     """Return True/False from system parameter
    #     - Signals access rights needs to check or not
    #     :Params: return : boolean"""
    #     ICPSudo = self.env["ir.config_parameter"].sudo()
    #     manager_product_configuration_settings = ICPSudo.get_param(
    #         "product_configurator.manager_product_configuration_settings"
    #     )
    #     return manager_product_configuration_settings

    # @api.model
    # def check_config_user_access(self):
    #     """Check user have access to perform action(create/write/delete)
    #     on configurable products"""
    #     if not self._check_config_group_rights():
    #         return True
    #     config_manager = self.env.user.has_group(
    #         "product_configurator.group_product_configurator_manager"
    #     )
    #     user_root = self.env.ref("base.user_root")
    #     user_admin = self.env.ref("base.user_admin")
    #     if (
    #         config_manager
    #         or self.env.user.id in [user_root.id, user_admin.id]
    #         or self.env.su
    #     ):
    #         return True
    #     raise ValidationError(
    #         _(
    #             "Sorry, you are not allowed to create/change this kind of "
    #             "document. For more information please contact your manager."
    #         )
    #     )

    # @api.model
    # def create(self, vals):
    #     """Patch for check access rights of user(configurable products)"""
    #     restrict_config_ok = vals.get("restrict_config_ok", False)
    #     if restrict_config_ok:
    #         self.check_config_user_access()
    #     return super(ProductTemplate, self).create(vals)

    # def write(self, vals):
    #     """Patch for check access rights of user(configurable products)"""
    #     change_restrict_config_ok = "restrict_config_ok" in vals
    #     configurable_templates = self.filtered(lambda template: template.restrict_config_ok)
    #     if change_restrict_config_ok or configurable_templates:
    #         self[:1].check_config_user_access()

    #     return super(ProductTemplate, self).write(vals)

    # @api.constrains("restrict_config_line_ids")
    # def _check_config_line_domain(self):
    #     attribute_line_ids = self.attribute_line_ids
    #     tmpl_value_ids = attribute_line_ids.mapped("value_ids")
    #     tmpl_attribute_ids = attribute_line_ids.mapped("attribute_id")
    #     error_message = False
    #     for domain_id in self.restrict_config_line_ids.mapped("domain_id"):
    #         domain_attr_ids = domain_id.domain_line_ids.mapped("attribute_id")
    #         domain_value_ids = domain_id.domain_line_ids.mapped("value_ids")
    #         invalid_value_ids = domain_value_ids - tmpl_value_ids
    #         invalid_attribute_ids = domain_attr_ids - tmpl_attribute_ids
    #         if not invalid_value_ids and not invalid_value_ids:
    #             continue
    #         if not error_message:
    #             error_message = _(
    #                 "Following Attribute/Value from restriction "
    #                 "are not present in template attributes/values. "
    #                 "Please make sure you are adding right restriction"
    #             )
    #         error_message += _("\nRestriction: %s") % (domain_id.name)
    #         error_message += (
    #             invalid_attribute_ids
    #             and _("\nAttribute/s: %s")
    #             % (", ".join(invalid_attribute_ids.mapped("name")))
    #             or ""
    #         )
    #         error_message += (
    #             invalid_value_ids
    #             and _("\nValue/s: %s\n") % (", ".join(invalid_value_ids.mapped("name")))
    #             or ""
    #         )
    #     if error_message:
    #         raise ValidationError(error_message)

    # @api.model
    # def name_search(self, name="", args=None, operator="ilike", limit=100):
    #     domain = args or []
    #     domain += ["|", ("name", operator, name), ("default_code", operator, name)]
    #     return self.search(domain, limit=limit).name_get()


class ProductProduct(models.Model):
    _inherit = "product.product"
    # _rec_name = "config_name"


    def _get_conversions_dict(self):
        conversions = {"float": float, "integer": int}
        return conversions

    # @api.constrains("product_template_attribute_value_ids")
    # def _check_duplicate_product(self):
    #     """Check for prducts with same attribute values/custom values"""
    #     for product in self:
    #         if not product.restrict_config_ok:
    #             continue

    #         # At the moment, I don't have enough confidence with my
    #         # understanding of binary attributes, so will leave these
    #         # as not matching...
    #         # In theory, they should just work, if they are set to "non search"
    #         # in custom field def!
    #         # TODO: Check the logic with binary attributes
    #         config_session_obj = product.env["product.config.session"]
    #         ptav_ids = product.product_template_attribute_value_ids.mapped(
    #             "product_attribute_value_id"
    #         )
    #         duplicates = config_session_obj.search_variant(
    #             product_tmpl_id=product.product_tmpl_id,
    #             value_ids=ptav_ids.ids,
    #         ).filtered(lambda p: p.id != product.id)

    #         if duplicates:
    #             raise ValidationError(
    #                 _(
    #                     "Configurable Products cannot have duplicates "
    #                     "(identical attribute values)"
    #                 )
    #             )

    # def _get_config_name(self):
    #     """Name for configured products
    #     :param: return : String"""
    #     self.ensure_one()
    #     return self.name

    # def _get_mako_context(self, buf):
    #     """Return context needed for computing product name based
    #     on mako-tamplate define on it's product template"""
    #     self.ensure_one()
    #     ptav_ids = self.product_template_attribute_value_ids.mapped(
    #         "product_attribute_value_id"
    #     )
    #     return Context(
    #         buf,
    #         product=self,
    #         attribute_values=ptav_ids,
    #         steps=self.product_tmpl_id.config_step_line_ids,
    #         template=self.product_tmpl_id,
    #     )

    # def _get_mako_tmpl_name(self):
    #     """Compute and return product name based on mako-tamplate
    #     define on it's product template"""
    #     self.ensure_one()
    #     if self.mako_tmpl_name:
    #         try:
    #             mytemplate = Template(self.mako_tmpl_name or "")
    #             buf = StringIO()
    #             ctx = self._get_mako_context(buf)
    #             mytemplate.render_context(ctx)
    #             return buf.getvalue()
    #         except Exception:
    #             _logger.error(
    #                 _("Error while calculating mako product name: %s")
    #                 % self.display_name
    #             )
    #     return self.display_name

    # @api.depends("product_template_attribute_value_ids.weight_extra")
    # def _compute_product_weight_extra(self):
    #     for product in self:
    #         product.weight_extra = sum(
    #             product.mapped("product_template_attribute_value_ids.weight_extra")
    #         )

    # @api.depends("weight_dummy", "weight_extra", "product_tmpl_id.weight")
    # def _compute_product_weight(self):
    #     for product in self:
    #         if product.restrict_config_ok:
    #             tmpl_weight = product.product_tmpl_id.weight
    #             product.weight = tmpl_weight + product.weight_extra
    #         else:
    #             product.weight = product.weight_dummy

    # def _inverse_product_weight(self):
    #     """Store weight in dummy field"""
    #     self.weight_dummy = self.weight

    # config_name = fields.Char(
    #     string="Configuration Name", compute="_compute_config_name"
    # )
    # weight_extra = fields.Float(compute="_compute_product_weight_extra", store=True)
    # weight_dummy = fields.Float(string="Manual Weight", digits="Stock Weight")
    # weight = fields.Float(
    #     compute="_compute_product_weight",
    #     inverse="_inverse_product_weight",
    #     store=True,
    # )

    # # product preset
    # config_preset_ok = fields.Boolean(string="Is Preset")

    # def _compute_config_name(self):
    #     """Compute the name of the configurable products and use template
    #     name for others"""
    #     for product in self:
    #         if product.restrict_config_ok:
    #             product.config_name = product._get_config_name()
    #         else:
    #             product.config_name = product.name

    def reconfigure_product(self):
        """launches a product configurator wizard with a linked
        template and variant in order to re-configure an existing product.
        It is essentially a shortcut to pre-fill configuration
        data of a variant"""
        self.ensure_one()
        return False

        # extra_vals = {"product_id": self.id}
        # return self.product_tmpl_id.create_config_wizard(extra_vals=extra_vals)

    # @api.model
    # def check_config_user_access(self, mode):
    #     """Check user have access to perform action(create/write/delete)
    #     on configurable products"""
    #     if not self.env["product.template"]._check_config_group_rights():
    #         return True
    #     config_manager = self.env.user.has_group(
    #         "product_configurator.group_product_configurator_manager"
    #     )
    #     config_user = self.env.user.has_group(
    #         "product_configurator.group_product_configurator"
    #     )
    #     user_root = self.env.ref("base.user_root")
    #     user_admin = self.env.ref("base.user_admin")
    #     if (
    #         config_manager
    #         or (config_user and mode not in ["delete"])
    #         or self.env.user.id in [user_root.id, user_admin.id]
    #     ):
    #         return True
    #     raise ValidationError(
    #         _(
    #             "Sorry, you are not allowed to create/change this kind of "
    #             "document. For more information please contact your manager."
    #         )
    #     )

    # def unlink(self):
    #     """- Signal unlink from product variant through context so
    #     removal can be stopped for configurable templates
    #     - check access rights of user(configurable products)"""
    #     config_product = any(p.restrict_config_ok for p in self)
    #     if config_product:
    #         self.env["product.product"].check_config_user_access(mode="delete")
    #     ctx = dict(self.env.context, unlink_from_variant=True)
    #     self.env.context = ctx
    #     return super(ProductProduct, self).unlink()

    # @api.model
    # def create(self, vals):
    #     """Patch for check access rights of user(configurable products)"""
    #     restrict_config_ok = vals.get("restrict_config_ok", False)
    #     if restrict_config_ok:
    #         self.check_config_user_access(mode="create")
    #     return super(ProductProduct, self).create(vals)

    # def write(self, vals):
    #     """Patch for check access rights of user(configurable products)"""
    #     change_restrict_config_ok = "restrict_config_ok" in vals
    #     configurable_products = self.filtered(lambda product: product.restrict_config_ok)
    #     if change_restrict_config_ok or configurable_products:
    #         self[:1].check_config_user_access(mode="write")

    #     return super(ProductProduct, self).write(vals)

    # # pylint:disable=missing-return
    # def _compute_product_price_extra(self):
    #     standard_products = self.filtered(lambda product: not product.restrict_config_ok)
    #     config_products = self - standard_products
    #     if standard_products:
    #         super(ProductProduct, standard_products)._compute_product_price_extra()
    #     for product in config_products:
    #         attribute_value_obj = self.env["product.attribute.value"]
    #         value_ids = (
    #             product.product_template_attribute_value_ids.product_attribute_value_id
    #         )
    #         extra_prices = attribute_value_obj.get_attribute_value_extra_prices(
    #             product_tmpl_id=product.product_tmpl_id.id, pt_attr_value_ids=value_ids
    #         )
    #         product.price_extra = sum(extra_prices.values())
