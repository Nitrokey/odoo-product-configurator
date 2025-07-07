{
    "name": "Website Product Configurator Restriction",
    "version": "15.0.1.0.0",
    "summary": """Website configure products restriction in e-shop""",
    "author": "Pledra, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/product-configurator",
    "category": "website",
    "depends": [
        "website_sale","sale"
    ],
    "data": [
        "security/ir.model.access.csv",
        "demo/product_template.xml",
        "demo/product_attribute.xml",
        "demo/product_config_domain.xml",
        "demo/product_config_lines.xml",
        "data/menu_configurable_website_product.xml",
        "views/product_config_view.xml",
        "views/product_view.xml",
        # "views/product_configuration_template.xml",
    ],
    "demo": [
    ],
    'assets': {
        'web.assets_frontend': [
            'website_product_configurator_restriction/static/src/js/variant_mixin.js',
        ],
    },

    "application": True,
    "installable": True,
    
}
