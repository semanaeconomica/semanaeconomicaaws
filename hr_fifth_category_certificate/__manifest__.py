# -*- encoding: utf-8 -*-
{
	'name': 'Hr Fifth Category Certificate',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fifth_category'],
	'version': '1.0',
	'description':"""
	Modulo para generar Certificado de Quinta Categoria
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'views/hr_employee.xml',
			'wizard/hr_fifth_category_wizard.xml'
		],
	'installable': True
}