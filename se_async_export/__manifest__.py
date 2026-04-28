# -*- coding: utf-8 -*-
{
    'name': 'Semana Económica - Async XLSX Export',
    'version': '13.0.1.0.0',
    'category': 'Tools',
    'summary': 'Exporta a XLSX en segundo plano, con barra de progreso y '
               'descarga automática al finalizar. Evita el timeout del '
               'firewall del cliente en listados grandes.',
    'author': 'Semana Económica / ITGrupo',
    'website': 'https://itgrupo.pe',
    'license': 'LGPL-3',
    'depends': [
        'web',
        'mail',
        'bus',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/export_xlsx_job_rules.xml',
        'data/ir_cron_data.xml',
        'views/assets.xml',
        'views/export_job_views.xml',
    ],
    'qweb': [
        'static/src/xml/async_export.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
