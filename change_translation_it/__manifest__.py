# -*- encoding: utf-8 -*-
{
	'name': 'Cambiar Traducciones',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['base','account'],
	'version': '1.0',
	'description':"""
	- Cambia traduccion del boton "Cancelar Asiento" a "Anular Asiento"
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'update_translation.sql',
		'views/account_payment.xml'
	],
	'installable': True
}