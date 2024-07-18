# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	##DATOS RENDICION
	date_surrender = fields.Date(string='Fecha Entrega')
	employee_id = fields.Many2one('res.partner',string='Empleado')
	amount_surrender = fields.Float(string='Monto Entregado',default=0)
	einvoice_catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago', copy=False)
	comp_number = fields.Char(string=u'Número Comprobante')
	memory = fields.Char(string=u'Memoria')
	date_render_it = fields.Date(string=u'Fecha Rendición')


	def get_wizard_report_c(self):
		wizard = self.env['report.render.wizard'].create({
			'statement_id': self.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_report_render_wizard' % module)
		return {
			'name':u'Reporte',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'report.render.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def reg_account_move_lines_it(self):
		for statement in self:
			if statement.journal_check_surrender:
				sql = """update account_move_line set partner_id = %s, type_document_id = (SELECT ID FROM einvoice_catalog_01 where code = '00' LIMIT 1), nro_comp = '%s' 
						where statement_id = %d and account_id = %d """%(str(statement.employee_id.id) if statement.employee_id else 'null',statement.comp_number if statement.comp_number else '',statement.id,statement.journal_id.default_debit_account_id.id)
				self.env.cr.execute(sql)

		return self.env['popup.it'].get_message('Se regularizaron correctamente los registros seleccionados.')