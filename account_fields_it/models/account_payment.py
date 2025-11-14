# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	cash_flow_id = fields.Many2one('account.cash.flow',string='Flujo de Caja')
	catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago')
	type_doc_cash_id = fields.Many2one('einvoice.catalog.01',string='Tipo Documento Caja')
	cash_nro_comp = fields.Char(string='Nro. de Op. Caja',size=42)
	type_document_id = fields.Many2one('einvoice.catalog.01',string='Tipo Documento')
	nro_comp = fields.Char(string='Nro. Comprobante')
	is_personalized_change = fields.Boolean(string='T.C. Personalizado',default=False)
	type_change = fields.Float(string='Tipo de Cambio',digits=(12,4),default=1)

	@api.onchange('cash_nro_comp','type_doc_cash_id')
	def _get_ref(self):
		digits_serie = ('').join(self.type_doc_cash_id.digits_serie*['0'])
		digits_number = ('').join(self.type_doc_cash_id.digits_number*['0'])
		if self.cash_nro_comp:
			if '-' in self.cash_nro_comp:
				partition = self.cash_nro_comp.split('-')
				if len(partition) == 2:
					serie = digits_serie[:-len(partition[0])] + partition[0]
					number = digits_number[:-len(partition[1])] + partition[1]
					self.cash_nro_comp = serie + '-' + number

	@api.onchange('nro_comp','type_document_id')
	def _get_ref(self):
		digits_serie = ('').join(self.type_document_id.digits_serie*['0'])
		digits_number = ('').join(self.type_document_id.digits_number*['0'])
		if self.nro_comp:
			if '-' in self.nro_comp:
				partition = self.nro_comp.split('-')
				if len(partition) == 2:
					serie = digits_serie[:-len(partition[0])] + partition[0]
					number = digits_number[:-len(partition[1])] + partition[1]
					self.nro_comp = serie + '-' + number

		move_lines = self.move_line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
		for move_line in move_lines:
			self.env.cr.execute("""UPDATE ACCOUNT_MOVE_LINE SET NRO_COMP = '%s', TYPE_DOCUMENT_ID = %d WHERE ID = %d""" % (self.nro_comp,self.type_document_id.id,move_line._origin.id))

	def renumber_sequence(self):
		for pay in self:
			if pay.state == 'draft':
				sql = """update account_payment set move_name = '' where id = """+str(pay.id)+""" """
				self.env.cr.execute(sql)
				return self.env['popup.it'].get_message('Se borro correctamente la secuencia')
			else:
				raise UserError("No puede realizar esta accion si el pago no se encuentra en estado: Borrador")