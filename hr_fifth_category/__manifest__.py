# -*- encoding: utf-8 -*-
{
	'name': 'Hr Fifth Category',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it', 'hr_social_benefits', 'account'],
	'version': '1.0',
	'description':"""
	Modulo para el calculo de Quinta Category
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/security.xml',
			 'security/ir.model.access.csv',
			 'views/account_fiscal_year.xml',
			 'views/hr_contract.xml',
			 'views/hr_fifth_category.xml',
			 'views/hr_main_parameter.xml'
			],
	'installable': True
}
