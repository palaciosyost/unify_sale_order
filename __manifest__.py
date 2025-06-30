{
    'name': 'Unificar Cotizaciones',
    'version': '1.0',
    'description': 'Funcionalidad nueva para unificar cotizaciones con el mismo cliente registrado',
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
        'view/form_sale_order.xml',
        'view/acton_wizard_order_compra.xml',  # ← corregido
        'view/server_action_sale.xml',
    ],
    'application': False,
    'installable': True,
}
