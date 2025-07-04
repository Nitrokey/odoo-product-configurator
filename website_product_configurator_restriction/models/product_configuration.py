import logging
from ast import literal_eval

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang

_logger = logging.getLogger(__name__)


class WebsiteProductConfigDomain(models.Model):
    _name = "website.product.config.domain"
    _description = "Domain for Config Restrictions"

    @api.depends("implied_ids")
    def _get_trans_implied(self):
        """Computes the transitive closure of relation implied_ids"""

        def linearize(domains):
            trans_domains = domains
            for domain in domains:
                implied_domains = domain.implied_ids - domain
                if implied_domains:
                    trans_domains |= linearize(implied_domains)
            return trans_domains

        for domain in self:
            domain.trans_implied_ids = linearize(domain)

    def compute_domain(self):
        """Returns a list of domains defined on a
        website.product.config.domain_line_ids and all implied_ids"""
        # TODO: Enable the usage of OR operators between implied_ids
        # TODO: Add implied_ids sequence field to enforce order of operations
        # TODO: Prevent circular dependencies
        computed_domain = []
        for domain in self:
            lines = domain.trans_implied_ids.mapped("domain_line_ids").sorted()
            if not lines:
                continue
            for line in lines[:-1]:
                if line.operator == "or":
                    computed_domain.append("|")
                computed_domain.append(
                    (line.attribute_id.id, line.condition, line.value_ids.ids)
                )
            # ensure 2 operands follow the last operator
            computed_domain.append(
                (
                    lines[-1].attribute_id.id,
                    lines[-1].condition,
                    lines[-1].value_ids.ids,
                )
            )
        return computed_domain

    name = fields.Char(required=True)
    domain_line_ids = fields.One2many(
        comodel_name="website.product.config.domain.line",
        inverse_name="domain_id",
        string="Restrictions",
        required=True,
        copy=True,
    )
    implied_ids = fields.Many2many(
        comodel_name="website.product.config.domain",
        relation="product_config_domain_implied_rel",
        string="Inherited",
        column1="domain_id",
        column2="parent_id",
    )
    trans_implied_ids = fields.Many2many(
        comodel_name="website.product.config.domain",
        compute=_get_trans_implied,
        column1="domain_id",
        column2="parent_id",
        string="Transitively inherits",
    )


class WebsiteProductConfigDomainLine(models.Model):
    _name = "website.product.config.domain.line"
    _order = "sequence"
    _description = "Domain Line for Config Restrictions"

    def _get_domain_conditions(self):
        operators = [("in", "In"), ("not in", "Not In")]

        return operators

    def _get_domain_operators(self):
        andor = [("and", "And"), ("or", "Or")]

        return andor

    @api.depends("attribute_id")
    def _compute_template_attribute_value_ids(self):
        for domain in self:
            domain.template_attribute_value_ids = (
                domain._get_allowed_attribute_value_ids()
            )

    def _get_allowed_attribute_value_ids(self):
        self.ensure_one()
        product_template = self.env["product.template"]
        if self.env.context.get("product_tmpl_id"):
            product_template = product_template.browse(
                self.env.context.get("product_tmpl_id")
            )
        template_lines = product_template.attribute_line_ids
        attribute_values = self.attribute_id.value_ids
        return (
            product_template
            and (template_lines.mapped("value_ids") & attribute_values)
            or attribute_values
        )

    template_attribute_value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        string="Template Attribute Values",
        compute="_compute_template_attribute_value_ids",
    )
    attribute_id = fields.Many2one(
        comodel_name="product.attribute", string="Attribute", required=True
    )
    domain_id = fields.Many2one(
        comodel_name="website.product.config.domain", required=True, string="Rule"
    )
    condition = fields.Selection(selection=_get_domain_conditions, required=True)
    value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="product_config_domain_line_attr_rel",
        column1="line_id",
        column2="attribute_id",
        string="Values",
        required=True,
    )
    operator = fields.Selection(
        selection=_get_domain_operators,
        string="Operators",
        default="and",
        required=True,
    )
    sequence = fields.Integer(
        default=1,
        help="Set the order of operations for evaluation domain lines",
    )


class WebsiteProductConfigLine(models.Model):
    _name = "website.product.config.line"
    _description = "Product Config Restrictions"
    _order = "product_tmpl_id, sequence, id"

    # TODO: Prevent config lines having dependencies that are not set in other
    # config lines
    # TODO: Prevent circular depdencies: Length -> Color, Color -> Length

    @api.onchange("attribute_line_id")
    def onchange_attribute(self):
        self.value_ids = False
        self.domain_id = False

    @api.depends(
        "product_tmpl_id",
        "attribute_line_id",
        "product_tmpl_id.attribute_line_ids",
        "product_tmpl_id.restrict_config_line_ids",
    )
    def _compute_template_attribute_ids(self):
        for config_line in self:
            product_template = config_line.product_tmpl_id
            attribute_line_ids = product_template.attribute_line_ids
            config_line.template_attribute_ids = attribute_line_ids.mapped(
                "attribute_id"
            )

    template_attribute_ids = fields.Many2many(
        comodel_name="product.attribute",
        string="Template Attributes",
        compute="_compute_template_attribute_ids",
    )
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Product Template",
        ondelete="cascade",
        required=True,
    )
    attribute_line_id = fields.Many2one(
        comodel_name="product.template.attribute.line",
        string="Attribute Line",
        ondelete="cascade",
        required=True,
    )
    # TODO: Find a more elegant way to restrict the value_ids
    attr_line_val_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        related="attribute_line_id.value_ids",
        string="Attribute Line Values",
    )
    value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="cfg_line_attr_val_id_rel",
        column1="cfg_line_id",
        column2="attr_val_id",
        string="Values",
    )
    domain_id = fields.Many2one(
        comodel_name="website.product.config.domain",
        required=True,
        string="Restrictions",
    )
    sequence = fields.Integer(default=10)

    @api.constrains("value_ids")
    def check_value_attributes(self):
        """Values selected in config lines must belong to the
        attribute exist on linked attribute line"""
        for line in self:
            value_attributes = line.value_ids.mapped("attribute_id")
            if value_attributes != line.attribute_line_id.attribute_id:
                raise ValidationError(
                    _(
                        "Values must belong to the attribute of the "
                        "corresponding attribute_line set on the "
                        "configuration line"
                    )
                )
