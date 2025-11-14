# -*- encoding: utf-8 -*-
{
	'name': 'Account Base IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','base','product','l10n_latam_base','account_accountant','popup_it'],
	'version': '1.0',
	'description':"""
	Creacion de Catalogos y Tablas
		-Catalogo 1 Codigo Tipo de Comprobante
		-Catalogo 6 Tipos de Documento de Identidad
		-Medio de Pago SUNAT
		-Tipos Estados Financieros
		-Rubros Flujo de Efectivo
		-Rubros Cambios en el Patrimonio Neto
		-Año Fiscal
		-Periodos
		-Flujo de Caja
		-Tabla de Parametros Modulo Contable
		-Tipos Contables
		-Tipos de Existencias
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/security.xml',
			'security/ir.model.access.csv',
			'data/einvoice_catalog_01.xml',
			'data/einvoice_catalog_05.xml',
			'data/einvoice_catalog_07.xml',
			'data/einvoice_catalog_09.xml',
			'data/einvoice_catalog_10.xml',
			'data/einvoice_catalog_17.xml',
			'data/einvoice_catalog_25.xml',
			'data/einvoice_catalog_51.xml',
			'data/einvoice_catalog_54.xml',
			'data/einvoice_catalog_payment.xml',
			'data/account_type_it.xml',
			'data/account_efective_type.xml',
			'data/account_patrimony_type.xml',
			'data/existence_type.xml',
			'views/account_bank_statement.xml',
			'views/account_cash_flow.xml',
			'views/account_register_values_it.xml',
			'views/account_efective_type.xml',
			'views/account_patrimony_type.xml',
			'views/account_period.xml',
			'views/account_type_it.xml',
			'views/einvoice_catalog_01.xml',
			'views/einvoice_catalog_05.xml',
			'views/einvoice_catalog_06.xml',
			'views/einvoice_catalog_07.xml',
			'views/einvoice_catalog_09.xml',
			'views/einvoice_catalog_10.xml',
            'views/einvoice_catalog_13.xml',
			'views/einvoice_catalog_17.xml',
			'views/einvoice_catalog_25.xml',
			'views/einvoice_catalog_51.xml',
			'views/einvoice_catalog_54.xml',
			'views/einvoice_catalog_payment.xml',
			'views/it_invoice_serie.xml',
			'views/existence_type.xml',
			'views/main_parameter.xml',
			'views/menu_items.xml',
			'views/product_template.xml',
		    'views/uom_uom.xml'
			],
	'installable': True
}
