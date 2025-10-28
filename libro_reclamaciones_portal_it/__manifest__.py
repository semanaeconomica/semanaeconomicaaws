# -*- coding: utf-8 -*-
{
    'name': 'Libro de Reclamaciones - Portal',
    'version': '1.0',
    'summary': 'Formulario de Libro de Reclamaciones en el Portal Web',
    'depends': [
        'crm',
        'website',
        'portal',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/libro_reclamaciones_views.xml',
        'views/libro_reclamaciones_menu.xml',
        'templates/libro_reclamaciones_portal_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'author': 'ITGRUPO, Diego Aquino',
}