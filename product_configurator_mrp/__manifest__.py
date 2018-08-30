{
    'name': 'Product Configurator Manufacturing',
    'version': '11.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'BOM Support for configurable products',
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['mrp', 'product_configurator'],
    "data": [
        'security/configurator_security.xml',
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/product_config_view.xml',
        'views/mrp_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': False,
    'auto_install': False,
}
