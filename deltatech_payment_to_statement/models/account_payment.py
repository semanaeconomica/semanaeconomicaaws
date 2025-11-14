# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
	_inherit = "account.payment"

	statement_id = fields.Many2one(
		"account.bank.statement", string="Statement", domain="[('journal_id','=',journal_id)]"
	)

	statement_destination_id = fields.Many2one(
		"account.bank.statement", string="Statement Destination", domain="[('journal_id','=',destination_journal_id)]"
	)

	statement_line_id = fields.Many2one(
		"account.bank.statement.line",
		string="Statement Line",
		readonly=True,
		domain="[('statement_id','=',statement_id)]",
	)

	statement_destination_line_id = fields.Many2one(
		"account.bank.statement.line",
		string="Statement Destination Line",
		readonly=True,
		domain="[('statement_id','=',statement_destination_id)]",
	)

	@api.onchange("payment_date", "journal_id")
	def onchange_date_journal(self):
		domain = [("date", "=", self.payment_date), ("journal_id", "=", self.journal_id.id),("company_id", "=", self.company_id.id)]
		statement = self.env["account.bank.statement"].search(domain, limit=1)
		if statement:
			self.statement_id = statement

	def action_draft(self):
		res = super(AccountPayment, self).action_draft()
		if self.statement_line_id:
			self.statement_line_id.unlink()
		if self.statement_destination_line_id:
			self.statement_destination_line_id.unlink()

		return res

	def post(self):
		lines = self.env["account.bank.statement.line"]
		statement_payment = {}

		for payment in self:
			auto_statement = payment.destination_journal_id.auto_statement or payment.journal_id.auto_statement
			if auto_statement:
				if not payment.statement_line_id and payment.statement_id:
					if payment.statement_id.state == "confirm":
						payment.statement_id.button_reopen()
					values = {
						"name": payment.communication or "/",
						"statement_id": payment.statement_id.id,
						"date": payment.payment_date,
						"partner_id": payment.partner_id.id,
						"amount": payment.amount,
						"payment_id": payment.id,
						"ref": payment.cash_nro_comp,
						"catalog_payment_id": payment.catalog_payment_id.id,
					}
					if payment.payment_type in ["outbound", "transfer"]:
						values["amount"] = -1 * payment.amount

					line = self.env["account.bank.statement.line"].create(values)
					lines |= line
					payment.write({"statement_line_id": line.id})
					statement_payment[payment] = {"line": line}
					# ==== 'transfer' ====
					if payment.payment_type == "transfer":
						if not payment.statement_destination_line_id and payment.statement_destination_id:
							if payment.statement_destination_id.state == "confirm":
								payment.statement_destination_id.button_reopen()
							detination_statement = payment.statement_destination_id
							values["statement_id"] = detination_statement.id
							values["amount"] = payment.amount
							values["ref"] = payment.nro_comp
							line = self.env["account.bank.statement.line"].create(values)
							lines |= line
							payment.write({"statement_destination_line_id": line.id})
							statement_payment[payment]["line_destination"] = line

		res = super(AccountPayment, self).post()

		if lines:
			for line in lines:
				if line.name == "/":
					line.write({"name": line.payment_id.name})
		for payment in self:
			auto_statement = payment.destination_journal_id.auto_statement or payment.journal_id.auto_statement
			if auto_statement:
				payment.reconciliation_statement_line()
			payment.force_cash_sequence()

		return res

	def force_cash_sequence(self):
		# force cash in/out sequence
		for payment in self:
			if payment.partner_type == "customer" and payment.journal_id.type == "cash":
				if payment.journal_id.cash_in_sequence_id and payment.payment_type == "inbound":
					payment.name = payment.journal_id.cash_in_sequence_id.next_by_id()
				if payment.journal_id.cash_out_sequence_id and payment.payment_type == "outbound":
					payment.name = payment.journal_id.cash_out_sequence_id.next_by_id()

	def reconciliation_statement_line(self):
		for payment in self:
			for move_line in payment.move_line_ids:
				if payment.statement_id:
					if not move_line.statement_id and not move_line.reconciled and move_line.nro_comp == payment.cash_nro_comp:
						move_line.write(
							{"statement_id": payment.statement_id.id, "statement_line_id": payment.statement_line_id.id}
						)
				if payment.statement_destination_id:
					if not move_line.statement_id and not move_line.reconciled and move_line.nro_comp == payment.nro_comp:
						move_line.write(
							{"statement_id": payment.statement_destination_id.id, "statement_line_id": payment.statement_destination_line_id.id}
						)
'''
	def get_reconciled_statement_line(self):
		for payment in self:
			for move_line in payment.move_line_ids:
				if move_line.statement_id and move_line.statement_line_id:
					payment.write(
						{"statement_id": move_line.statement_id.id, "statement_line_id": move_line.statement_line_id.id}
					)

	def add_statement_line(self):
		lines = self.env["account.bank.statement.line"]
		self.get_reconciled_statement_line()
		for payment in self:
			auto_statement = payment.destination_journal_id.auto_statement or payment.journal_id.auto_statement
			if auto_statement and not payment.statement_id:  # type == 'cash'
				domain = [("date", "=", self.payment_date), ("journal_id", "=", self.journal_id.id)]
				statement = self.env["account.bank.statement"].search(domain, limit=1)
				if not statement:
					values = {"journal_id": payment.journal_id.id, "date": payment.payment_date, "name": "/"}
					statement = payment.env["account.bank.statement"].create(values)
				payment.write({"statement_id": statement.id})

			if payment.state == "posted" and not payment.statement_line_id and payment.statement_id:
				ref = ""
				for invoice in payment.invoice_ids:
					ref += invoice.number
				for invoice in payment.reconciled_invoice_ids:
					ref += invoice.number
				values = {
					"name": payment.communication or payment.name,
					"statement_id": payment.statement_id.id,
					"date": payment.payment_date,
					"partner_id": payment.partner_id.id,
					"amount": payment.amount,
					"payment_id": payment.id,
					"ref": ref,
				}
				if payment.payment_type in ["outbound", "transfer"]:
					values["amount"] = -1 * payment.amount

				line = self.env["account.bank.statement.line"].create(values)
				lines |= line
				payment.write({"statement_line_id": line.id})

				if payment.payment_type == "transfer":
					payment.write({"stare": "reconciled"})
					if payment.destination_journal_id.auto_statement:  # type == 'cash':
						domain = [
							("date", "=", payment.payment_date),
							("journal_id", "=", payment.destination_journal_id.id),
						]
						detination_statement = self.env["account.bank.statement"].search(domain, limit=1)
						if not detination_statement:
							statement_values = {
								"journal_id": payment.destination_journal_id.id,
								"date": payment.payment_date,
								"name": "/",
							}
							detination_statement = self.env["account.bank.statement"].create(statement_values)
						values["statement_id"] = detination_statement.id
						values["amount"] = payment.amount
						line = self.env["account.bank.statement.line"].create(values)
						lines |= line

				payment.reconciliation_statement_line()
'''