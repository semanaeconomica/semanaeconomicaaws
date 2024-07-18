# -*- encoding: utf-8 -*-
{
	'name': 'Kardex Mrp Production',
	'category': 'mrp',
	'author': 'ITGRUPO',
	'depends': ['kardex_valorado_it', 'mrp','mrp_kardex', 'stock_balance_report','atharva_theme_general'],
	'version': '1.0',
	'description':"""
	Modulo para añadir lineas de OP's en Kardex Fisico
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/make_kardex_view.xml'],
	'installable': True
}
