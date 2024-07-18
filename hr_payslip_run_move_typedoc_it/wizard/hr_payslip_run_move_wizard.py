# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrPayslipRunMoveWizard(models.TransientModel):
	_inherit = 'hr.payslip.run.move.wizard'


	def generate_move(self):
		res = super(HrPayslipRunMoveWizard,self).generate_move()
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.type_doc_pla.id:
			raise UserError('No se ha configurado el tipo de comprobante para Planilla')
		PR = self.env['hr.payslip.run'].browse(self._context.get('payslip_run_id'))
		move = PR.account_move_id

		move.button_draft()
		for l in move.line_ids:
			l.type_document_id = MainParameter.type_doc_pla.id
			l.nro_comp = 'Planilla - '+PR.name

		move.action_post()
		return res


