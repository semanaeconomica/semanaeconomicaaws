# -*- encoding: utf-8 -*-
{
	'name': u'Base y conf. generales de personalización PERÚ SEMANA ECONÓMICA',
	'category': 'base',
	'author': 'ITGRUPO',
	'depends': ['base','sale','popup_it'],
	'version': '1.0',
	'description':"""
		Base y conf. generales de personalización PERÚ SEMANA ECONÓMICA
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		#'security/ir.model.access.csv',
		'security/security.xml',
		'views/perueco_base_it.xml'
	],
	'installable': True
}
