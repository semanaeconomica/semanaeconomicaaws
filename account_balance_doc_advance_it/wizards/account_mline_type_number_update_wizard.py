# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMlineTypeNumberUpdateWizard(models.TransientModel):
	_name = 'account.mline.type.number.update.wizard'

	type_document_id = fields.Many2one('einvoice.catalog.01',string='T.D.')
	nro_comp = fields.Char(string='Nro Comp.',size=40)

	@api.onchange('nro_comp','type_document_id')
	def _get_ref(self):
		for i in self:
			digits_serie = ('').join(i.type_document_id.digits_serie*['0'])
			digits_number = ('').join(i.type_document_id.digits_number*['0'])
			if i.nro_comp:
				if '-' in i.nro_comp:
					partition = i.nro_comp.split('-')
					if len(partition) == 2:
						serie = digits_serie[:-len(partition[0])] + partition[0]
						number = digits_number[:-len(partition[1])] + partition[1]
						i.nro_comp = serie + '-' + number

	def update_type_number(self):
		line_obj = self.env['account.move.line']
		line_obj.browse(self.env.context['active_ids']).with_context({'type_document_id':self.type_document_id.id,'nro_comp':self.nro_comp,'active_ids':self.env.context['active_ids']}).update_type_number_it()
		return self.env['popup.it'].get_message(u'SE FUSIONARON CORRECTAMENTE LOS COMPROBANTES.')

	def update_type_number_saldos(self):
		line_obj = self.env['account.balance.period.book']
		line_obj.browse(self.env.context['active_ids']).with_context({'type_document_id':self.type_document_id.id,'nro_comp':self.nro_comp,'active_ids':self.env.context['active_ids']}).update_type_number_it()
		return self.env['popup.it'].get_message(u'SE FUSIONARON CORRECTAMENTE LOS COMPROBANTES.')