# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

####LEYENDA####
#nc = National Currency
#fc = Foreign Currency
#ed = Exchange Difference
#dt = Document Type
#wa = Without Address

class MainParameter(models.Model):
	_name = 'main.parameter'

	name = fields.Char(default='Parametros Principales')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	####CUENTAS PARA ASISTENTES####
	surrender_nc = fields.Many2one('account.account',string=u'Rendición Moneda Nacional')
	surrender_fc = fields.Many2one('account.account',string=u'Rendición Moneda Extranjera')
	supplier_advance_account_nc = fields.Many2one('account.account',string=u'Cuenta Anticipo Proveedor M.N.')
	supplier_advance_account_fc = fields.Many2one('account.account',string=u'Cuenta Anticipo Proveedor M.E.')
	customer_advance_account_nc = fields.Many2one('account.account',string=u'Cuenta Anticipo Cliente M.N.')
	customer_advance_account_fc = fields.Many2one('account.account',string=u'Cuenta Anticipo Cliente M.E.')
	detractions_account = fields.Many2one('account.account',string=u'Cuenta Detracciones Proveedor')
	customer_account_detractions = fields.Many2one('account.account',string=u'Cuenta Detracciones Clientes')
	profit_account_ed = fields.Many2one('account.account',string=u'Cuenta de Ganancias Diferencia de Cambio')
	loss_account_ed = fields.Many2one('account.account',string=u'Cuenta de Perdidas Diferencia de Cambio')
	free_transer_account_id = fields.Many2one('account.account',string=u'Cuenta de Transferencias Gratuitas')

	####DIARIOS PARA ASISTENTES####

	surrender_journal_nc = fields.Many2one('account.journal',string=u'Diario Rendiciones M.N.')
	surrender_journal_fc = fields.Many2one('account.journal',string=u'Diario Rendiciones M.E.')
	destination_journal = fields.Many2one('account.journal',string=u'Diario Asientos Automaticos')
	detraction_journal = fields.Many2one('account.journal',string=u'Diario Detracciones')
	credit_journal = fields.Many2one('account.journal',string=u'Diario de Aplicaciones de Notas de Credito')
	miscellaneous_journal = fields.Many2one('account.journal',string=u'Diario Misceláneo')

	####SECUENCIAS PARA ASISTENTES####

	supplier_advance_sequence = fields.Many2one('ir.sequence',string=u'Secuencia Anticipo Proveedor')

	####NOTA DE CREDITO NACIONAL####

	dt_national_credit_note = fields.Many2one('einvoice.catalog.01',string=u'Tipo de Documento')

	####RECIBO POR HONORARIOS####

	td_recibos_hon = fields.Many2one('einvoice.catalog.01',string=u'Tipo de Documento Recibo de Honorarios Predeterminado')

	####TRANSFERENCIAS GRATUITAS####

	free_transer_tax = fields.Many2one('account.tax',string=u'Impuesto Transf. Gratuita')
	free_transer_tax_ids = fields.Many2many('account.tax','free_transer_tax_main_parameter_rel','main_parameter_id','free_transer_tax_id',string=u'Impuestos Transf. Gratuita')
	free_transfer_journal_id = fields.Many2one('account.journal',string=u'Diario Transf. Gratuita')

	####LEASING####

	capital_account = fields.Many2one('account.account',string=u'Cuenta Capital')
	capital_tax = fields.Many2one('account.tax',string=u'Impuesto Capital')
	expenses_account = fields.Many2one('account.account',string=u'Cuenta Gastos')
	expenses_tax = fields.Many2one('account.tax',string=u'Impuesto Gastos')
	comission_account = fields.Many2one('account.account',string=u'Cuenta Comision')
	comission_tax = fields.Many2one('account.tax',string=u'Impuesto Comision')
	insurance_account = fields.Many2one('account.account',string=u'Cuenta Seguro')
	insurance_tax = fields.Many2one('account.tax',string=u'Impuesto Seguro')
	interest_account_leasing = fields.Many2one('account.account',string=u'Cuenta Interes')
	interest_tax = fields.Many2one('account.tax',string=u'Impuesto Interes')
	accrual_charge_account = fields.Many2one('account.account',string=u'Cuenta Cargo Devengamiento')
	accrual_charge_tax = fields.Many2one('account.tax',string='Impuesto Cargo Devengamiento')
	accrual_suscription_account = fields.Many2one('account.account',string=u'Cuenta Abono Devengamiento')
	accrual_suscription_tax = fields.Many2one('account.tax',string=u'Impuesto Abono Devengamiento')
	monetary_interest_charge_account = fields.Many2one('account.account',string=u'Cuenta Cargo Interes Monetario')
	monetary_interest_charge_tax = fields.Many2one('account.tax',string=u'Impuesto Cargo Interes Monetario')
	accrue_seat_journal_leasing = fields.Many2one('account.journal',string=u'Diario Asiento Devengo')
	proof_fees_type = fields.Many2one('einvoice.catalog.01',string=u'Tipo Comprobante Cuotas')

	####PRESTAMOS####

	capital_amortization_account = fields.Many2one('account.account',string=u'Cuenta Amortizacion Capital')
	interest_account_loan = fields.Many2one('account.account',string=u'Cuenta Interes')
	itf_account = fields.Many2one('account.account',string=u'Cuenta ITF')
	debt_account = fields.Many2one('account.account',string=u'Cuenta Mora')
	accrue_seat_journal_loan = fields.Many2one('account.journal',string=u'Diario Asiento Devengo')
	payment_proof_type = fields.Many2one('einvoice.catalog.01',string=u'Tipo Comprobante Pago')
	accrue_charge_account = fields.Many2one('account.account',string=u'Cuenta Cargo Devengo')
	accrue_suscription_account = fields.Many2one('account.account',string=u'Cuenta Abono Devengo')

	####EXPORTACION####

	exportation_document = fields.Many2one('einvoice.catalog.01',string=u'Documento de Exportación')
	proff_payment_wa = fields.Many2one('einvoice.catalog.01',string=u'Comprobante de Pago No Domiciliado')
	debit_note_wa = fields.Many2one('einvoice.catalog.01',string=u'Nota Debito No Domiciliado')
	credit_note_wa = fields.Many2one('einvoice.catalog.01',string=u'Nota Credito No Domiciliado')

	####DOCUMENTOS SUNAT####

	dt_sunat_ruc = fields.Many2one('l10n_latam.identification.type',string=u'Tipo de Documento RUC')
	ruc_size = fields.Integer(string=u'Longitud RUC')
	dt_sunat_dni = fields.Many2one('l10n_latam.identification.type',string=u'Tipo de Documento DNI')
	dni_size = fields.Integer(string=u'Longitud DNI')

	####SUNAT####

	account_plan_code = fields.Many2one('account.chart.template',string=u'Codigo Plan de Cuentas')
	cash_account_prefix = fields.Char(string=u'Prefijo Cuentas Caja',help=u'LOS PREFIJOS DEBEN SER DE TRES DÍGITOS Y DEBEN IR SEPARADOS POR COMA, ADEMÁS ENTRE COMILLA')
	bank_account_prefix = fields.Char(string=u'Prefijo Cuentas Banco',help=u'LOS PREFIJOS DEBEN SER DE TRES DÍGITOS Y DEBEN IR SEPARADOS POR COMA, ADEMÁS ENTRE COMILLA')
	uit_value = fields.Float(string=u'UIT',digits=(64,2))

	####PARTNER ANULADO####

	cancelation_partner = fields.Many2one('res.partner',string=u'Partner para Anulaciones')
	cancelation_product = fields.Many2one('product.product',string=u'Producto para Anulaciones')
	sale_ticket_partner = fields.Many2one('res.partner',string=u'Partner para Ventas Boletas')

	####CONFIGURACION####

	dir_create_file = fields.Char(string=u'Directorio Exportadores')
	dir_ple_create_file = fields.Char(string=u'Directorio PLE')
	dir_download = fields.Char(string=u'Directorio Descarga Completa')
	dir_download_url = fields.Char(string=u'Directorio Descarga URL')
	fiscal_year = fields.Many2one('account.fiscal.year',string=u'Año Fiscal')
	invoice_payment_term = fields.Many2one('account.payment.term', string='Terminos de Pago',
		domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

	####PERCEPCION####

	tax_account = fields.Many2one('account.account.tag',string=u'Cuenta de Impuesto')
	dt_perception = fields.Many2one('einvoice.catalog.01',string=u'Tipo de Documento')

	####CUENTAS DE LETRAS####

	customer_invoice_account_nc = fields.Many2one('account.account',string=u'Cuenta Factura Cliente M.N.')
	customer_invoice_account_fc = fields.Many2one('account.account',string=u'Cuenta Factura Cliente M.E.')
	customer_letter_account_nc = fields.Many2one('account.account',string=u'Cuenta Letra Cliente M.N.')
	customer_letter_account_fc = fields.Many2one('account.account',string=u'Cuenta Letra Cliente M.E.')
	rounding_gain_account = fields.Many2one('account.account',string=u'Cuenta Ganancia por Redondeo')
	rounding_loss_account = fields.Many2one('account.account',string=u'Cuenta Perdida por Redondeo')
	supplier_invoice_account_nc = fields.Many2one('account.account',string=u'Cuenta Factura Proveedor M.N.')
	supplier_invoice_account_fc = fields.Many2one('account.account',string=u'Cuenta Factura Proveedor M.E.')
	supplier_letter_account_nc = fields.Many2one('account.account',string=u'Cuenta Letra Proveedor M.N.')
	supplier_letter_account_fc = fields.Many2one('account.account',string=u'Cuenta Letra Proveedor M.E.')

	####ASIENTO DIFERENCIA####

	exchange_difference = fields.Boolean(string='Generar Diferencia de Cambio', default=False)

	####TRANSITO####

	transit_merchandise = fields.Boolean(string='Trabajar con Mercaderia en Transito', default=False)

	####MONEDAS####

	currency_parameter_lines = fields.One2many('currency.parameter.line','main_parameter_id')

	####CIERRE CONTABLE####

	balance_sheet_account = fields.Many2one('account.account',string='Cuenta Cierre Contable Utilidad')
	lost_sheet_account = fields.Many2one('account.account',string='Cuenta Cierre Contable Perdida')
	lost_result_account = fields.Many2one('account.account',string='Cuenta Resultados A.C. Perdida')
	profit_result_account = fields.Many2one('account.account',string='Cuenta Resultados A.C. Ganancia')

	####KARDEX####

	analytic_tag_kardex = fields.Many2one('account.analytic.tag',string='Etiqueta para Kardex')
	#consumption_operation_type = fields.Many2one('stock.picking.type',string='Tipo de Operacion Consumo')
	#entry_operation_type = fields.Many2one('stock.picking.type',string='Tipo de Operacion Ingreso')
	#outbound_operation = fields.Many2one('einvoice.catalog.12')

	@api.constrains('company_id')
	def _check_unique_parameter(self):
		self.env.cr.execute("""select id from main_parameter where company_id = %s""" % (str(self.company_id.id)))
		res = self.env.cr.dictfetchall()
		if len(res) > 1:
			raise UserError(u"Ya existen Parametros Principales para esta Compañía")


class CurrencyParameterLine(models.Model):
	_name = 'currency.parameter.line'

	main_parameter_id = fields.Many2one('main.parameter')
	currency_id = fields.Many2one('res.currency',string='Moneda')
	singular_name = fields.Char(string='Nombre Singular')
	plural_name = fields.Char(string='Nombre Plural')
	debit_account_id = fields.Many2one('account.account',string='Cuenta a Pagar')
	credit_account_id = fields.Many2one('account.account',string='Cuenta a Cobrar')