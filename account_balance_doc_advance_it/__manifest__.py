# -*- encoding: utf-8 -*-
{
	'name': 'FUNCIONALIDADES AVANZADAS PARA REPORTE DE CUENTAS CORRIENTES',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_balance_doc_rep_it','account_reports'],
	'version': '1.0',
	'description':"""
	- Modifica Reporte de Saldos por Fecha Contable y le agrega Fecha Prevista de Pago.
	- Utilitario para actualizar Fecha Prevista de Pago en Apuntes Contables.
	- Utilitario para actualizar Tipo y Nro Comprobante en Apuntes Contables.
	- Crea grupo "Actualizar Apuntes Contables" que podran ver los utilitarios.
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'views/account_balance_period.xml',
		'views/account_move_line.xml',
		'wizards/account_mline_type_number_update_wizard.xml',
		'wizards/account_mline_expected_date_update_wizard.xml'
	],
	'installable': True
}
