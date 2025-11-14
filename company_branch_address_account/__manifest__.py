# -*- coding: utf-8 -*-
{
    'name': 'Company Branch Address in Account',
    'version': '13.0.1',
    'category': 'Account',
    'author': 'Conflux',
    'sequence': 12,
    'description': "",
    'depends': ['company_branch_address','account'],
    'data': [
        'security/res_company_branch_address_security.xml',
        'views/account_move_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'OPL-1',
}