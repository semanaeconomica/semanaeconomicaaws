# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'LLIKHA NOTIFICATION',
    'summary': 'Notificaciones',
    'category': 'All',
    'author':'LLIKHA-BO',
    'description': """Notificationes
    """,
    'depends': ['account_accountant','web'],
    'data': [
        'assets.xml'
    ],
    'qweb': [    
        'static/src/js/export_file_manager_tmpl.xml',
        'static/src/js/notification_button.xml',        
    ],
    'auto_install': False,
    'installable': True,
}
