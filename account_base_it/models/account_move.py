# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
	_inherit = 'account.move'

	doc_invoice_relac = fields.One2many('doc.invoice.relac','move_id')

	#INVOICE PLE
	_sql_constraints = [
		('campo_26_purchase_nd_negative', 'CHECK (campo_26_purchase_nd >= 0)', 'El valor de Renta Bruta no puede ser negativo.'),
		('campo_28_purchase_nd_negative', 'CHECK (campo_28_purchase_nd >= 0)', 'El valor de Renta Neta no puede ser negativo.'),
		('campo_29_purchase_nd_negative', 'CHECK (campo_29_purchase_nd >= 0)', 'El valor de Tasa de Retencion no puede ser negativo.'),
		('campo_30_purchase_nd_negative', 'CHECK (campo_30_purchase_nd >= 0)', 'El valor de Impuesto Retenido no puede ser negativo.'),
	]
	
	#SALES
	campo_09_sale = fields.Char(string='Ultimo Número Consolidado',size=20)
	campo_31_sale = fields.Char(string='Numero de Contrato',size=12)
	campo_32_sale = fields.Boolean(string='Inconsistencia en Tipo de Cambio', default=False)
	campo_33_sale = fields.Boolean(string='Cancelado con Medio de Pago', default=False)
	campo_34_sale = fields.Selection([
									('0',u'Anotacion optativa sin efecto en el IGV'),
									('1',u'Fecha del comprobante corresponde al periodo'),
									('2',u'Documento anulado'),
									('8',u'Corresponde a un periodo anterior'),
									('9',u'Se esta corrigiendo una notacion del periodo anterior')
									],string='Estado PLE Venta',default='1')
	date_modify_sale = fields.Date(string='Fecha Modificacion PLE Venta')

	#PURCHASES
	campo_09_purchase = fields.Char(string='Numero Inicial Consolidado',size=20)
	campo_33_purchase = fields.Boolean(string='Sujeto a Retencion', default=False)
	campo_34_purchase = fields.Selection([
									('1',u'Mercaderia, materia prima, suministro, envases y embalajes'),
									('2',u'Activo Fijo'),
									('3',u'Otros activos no considerados en los numerales 1 y 2'),
									('4',u'Gastos de educacion, recreacion, salud, culturales, representacion, capacitacion, de viaje, mantenimiento de vehiculos, y de premios'),
									('5',u'Otros gastos no incluidos en el numeral 4')
									],string='Tipo de Adquisicion', help='Tabla 30 SUNAT',default='1')
	campo_35_purchase = fields.Char(string='Contrato o Proyecto',size=20)
	campo_36_purchase = fields.Boolean(string='Inconsistencia en Tipo de Cambio', default=False)
	campo_37_purchase = fields.Boolean(string='Proveedor No Habido', default=False)
	campo_38_purchase = fields.Boolean(string='Renuncio Exoineracion al IGV', default=False)
	campo_39_purchase = fields.Boolean(string='Inconsistencia DNI, Liquidacion de Compra', default=False)
	campo_40_purchase = fields.Boolean(string='Cancelado con Medio de Pago', default=False)
	campo_41_purchase = fields.Selection([
									('0',u'ANOTACION OPTATIVAS SIN EFECTO EN EL IGV'),
									('1',u'FECHA DEL DOCUMENTO CORRESPONDE AL PERIODO EN QUE SE ANOTÓ'),
									('6',u'FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, DENTRO DE LOS 12 MESES'),
									('7',u'FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, LUEGO DE LOS 12 MESES'),
									('9',u'ES AJUSTE O RECTIFICACION')
									],string='Estado PLE Compra',default='1')
	date_modify_purchase = fields.Date(string='Fecha Modificacion PLE Compra')
	#SIRE
	participation_percent_sire = fields.Float(string=u'% Participación del Contrato de las Sociedades',copy=False)
	tax_mat_exo_igv_sire = fields.Float(string=u'Impuesto materia de beneficio Ley 31053 - Están exonerados del IGV la importación y/o venta en el país de los libros y productos editoriales afines',copy=False)
	#PLE NO DOMICILIADOS
	campo_26_purchase_nd = fields.Float(string='Renta Bruta',digits=(12, 2)) # It can't be negative
	campo_27_purchase_nd = fields.Float(string='Deduccion Costo Eneajenación',digits=(12, 2))
	campo_28_purchase_nd = fields.Float(string='Renta Neta',digits=(12, 2)) # It can't be negative
	campo_29_purchase_nd = fields.Float(string='Tasa de Retencion',digits=(3, 2)) # It can't be negative
	campo_30_purchase_nd = fields.Float(string='Impuesto Retenido',digits=(12, 2)) # It can't be negative
	campo_32_purchase_nd = fields.Char(help='Tabla 33 SUNAT',string='Exoneracion Aplicada')
	campo_33_purchase_nd = fields.Char(help='Tabla 31 SUNAT',string='Tipo de Renta')
	campo_34_purchase_nd = fields.Char(help='Tabla 32 SUNAT',string='Modalidad de Servicio')
	campo_35_purchase_nd = fields.Boolean(string='Articulo 76 IR', default=False)
	campo_23_purchase_nd = fields.Many2one('res.partner', string='Beneficiario de los Pagos')


	#SUSTENTO CREDITO FISCAL
	campo_11_purchase_nd = fields.Many2one('einvoice.catalog.01',string='Tipo Documento')
	campo_12_purchase_nd = fields.Char(string='Serie',size=20)
	campo_13_purchase_nd = fields.Char(string='Año Emsion DUA',size=4)
	campo_14_purchase_nd = fields.Char(string='Nro Comprobante',size=20)
	campo_15_purchase_nd = fields.Float(string='Monto de Retencion del IGV',digits=(12,2),default=0)


class DocInvoiceRelac(models.Model):
	_name = 'doc.invoice.relac'

	move_id = fields.Many2one('account.move')
	type_document_id = fields.Many2one('einvoice.catalog.01',string='TD')
	date = fields.Date(string='Fecha de Emision')
	nro_comprobante = fields.Char(string='Comprobante',size=40)
	amount_currency = fields.Float(string='Monto Me',digits=(16, 2))
	amount = fields.Float(string='Total Mn',digits=(16, 2))
	bas_amount = fields.Float(string='Base Imponible',digits=(16, 2))
	tax_amount = fields.Float(string='IGV',digits=(16, 2))

	@api.onchange('nro_comprobante','type_document_id')
	def _get_ref(self):
		digits_serie = ('').join(self.type_document_id.digits_serie*['0'])
		digits_number = ('').join(self.type_document_id.digits_number*['0'])
		if self.nro_comprobante:
			if '-' in self.nro_comprobante:
				partition = self.nro_comprobante.split('-')
				if len(partition) == 2:
					serie = digits_serie[:-len(partition[0])] + partition[0]
					number = digits_number[:-len(partition[1])] + partition[1]
					self.nro_comprobante = serie + '-' + number
