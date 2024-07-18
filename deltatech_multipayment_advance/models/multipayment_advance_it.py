# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'

	statement_id = fields.Many2one("account.bank.statement", string="Statement", domain="[('journal_id','=',journal_id)]")
	statement_line_id = fields.Many2one("account.bank.statement.line",string="Statement Line",readonly=True,domain="[('statement_id','=',statement_id)]")

	def cancelar(self):
		res = super(MultipaymentAdvanceIt, self).cancelar()
		if self.statement_line_id:
			self.statement_line_id.unlink()
		return res

	@api.onchange("payment_date", "journal_id")
	def onchange_date_journal(self):
		domain = [("date", "=", self.payment_date), ("journal_id", "=", self.journal_id.id),("company_id", "=", self.company_id.id)]
		statement = self.env["account.bank.statement"].search(domain, limit=1)
		if statement:
			self.statement_id = statement

	def crear_asiento(self):
		for multipayment in self:
			auto_statement = multipayment.journal_id.auto_statement
			if auto_statement:
				if not multipayment.statement_line_id and multipayment.statement_id:
					if multipayment.statement_id.state == "confirm":
						multipayment.statement_id.button_reopen()
					amount = 0
					for elem in multipayment.lines_ids:
						amount += elem.debe - elem.haber
					values = {
						"name": multipayment.glosa or "/",
						"statement_id": multipayment.statement_id.id,
						"date": multipayment.payment_date,
						"partner_id": multipayment.partner_cash_id.id,
						"amount": amount,
						"ref": multipayment.nro_operation,
						"catalog_payment_id": multipayment.catalog_payment_id.id,
					}
					line = self.env["account.bank.statement.line"].create(values)
					multipayment.write({"statement_line_id": line.id})
		
		res = super(MultipaymentAdvanceIt, self).crear_asiento()

		for multipayment in self:
			auto_statement = multipayment.journal_id.auto_statement
			if auto_statement:
				for move_line in multipayment.asiento_id.line_ids:
					if not move_line.statement_id and not move_line.reconciled:
						move_line.write(
							{"statement_id": multipayment.statement_id.id, "statement_line_id": multipayment.statement_line_id.id}
						)

		return res