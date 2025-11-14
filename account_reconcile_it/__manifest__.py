# -*- encoding: utf-8 -*-
{
	'name': 'Account Reconcile IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','web','account_fields_it'],
	'version': '1.0',
	'description':"""
		Modulo para agregar Tipo de Documento y Numero de Comprobante a las lineas de Asiento Generadas en la Conciliacion desde Extractos Bancarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/assets.xml'
	],
	'installable': True
}
