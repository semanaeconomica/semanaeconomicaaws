# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrProvisionsWizard(models.TransientModel):
	_inherit = 'hr.provisions.wizard'


	def generate_move(self):
		res = super(HrProvisionsWizard,self).generate_move()
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.type_doc_prov.id:
			raise UserError('No se ha configurado el tipo de comprobante para Provisiones')
		PR = self.env['hr.provisiones'].browse(self._context.get('active_id'))
		move = PR.asiento_contable

		# move.button_draft()
		for l in move.line_ids:
			l.type_document_id = MainParameter.type_doc_pla.id
			l.nro_comp = u'Provisión - '+PR.payslip_run_id.name

		# move.action_post()
		return res


