# -*- coding: utf-8 -*-
{
    'name': 'CRM Export en Segundo Plano',
    'version': '13.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Exportar oportunidades a Excel en segundo plano',
    'description': 'Permite exportar grandes cantidades de oportunidades sin timeout del navegador',
    'depends': ['crm'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/crm_export_wizard_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
