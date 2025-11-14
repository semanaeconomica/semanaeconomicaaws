# -*- encoding: utf-8 -*-
{
	'name': 'Disabled MultiPayment in Invoice',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','base'],
	'version': '1.0',
	'description':"""
	Desaparecer la opcion de pago multiple
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'views/ir_action_server.xml'
			],
	'installable': True
}
