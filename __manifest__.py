{
    'name': 'Unificar Cotizaciones',
    'version': '1.0',
    'description': 'Funcionalidad nueva para unificar cotizaciones con el mismo cliente regstrado',
    'summary': '',
    'author': 'F.P.C. Technology',
    'website': 'https://fpc-technology.com',
    'license': 'LGPL-3',
    'category': 'sale',
    'depends': [
        'base', 'sale'
    ],
    'data': [
        'security/ir.model.access.csv',
        'view/action_tree_sale_order.xml',
        "view/form_sale_order.xml",
        "view/server_action_sale.xml",
    ],
    'images': [
        'static/description/icon_sale.png',
    ],
    'auto_install': False,
    'application': False,
    'sequence': 1,
    'installable': True,
    'price' : 40,
    'currency': 'EUR',
}