# -*- coding: utf-8 -*-
{
    'name': 'Import Vacations Rest',
    'version': '1.0.0',
    'category': 'HR',
    'description': """
        Import Vacations Rest
     """,
    'author': 'ITGrupo',
    'depends': ['base','popup_it','hr_vacations_it'],
    'data': [
        'data/attachment_sample.xml',
        'views/hr_vacation_rest_import_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
