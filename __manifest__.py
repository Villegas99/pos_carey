{
    "name": "Carey - Aislamiento de clientes por sucursal",
    "version": "1.0.0",
    "category": "Point of Sale",
    "summary": "Restringe la visibilidad y edición de clientes según la sucursal del usuario",
    "author": "Aurux",
    "license": "LGPL-3",
    "depends": [
        "base",
        "point_of_sale",
    ],
    "data": [
        "security/pos_carey_groups.xml",
        'security/pos_carey_pos_rules.xml', 
        "security/ir.model.access.csv",
        "security/pos_carey_rules.xml",
        "views/carey_res_users_views.xml",
        "views/carey_res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}