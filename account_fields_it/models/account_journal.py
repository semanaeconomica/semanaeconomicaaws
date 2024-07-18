# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountJournal(models.Model):
	_inherit = 'account.journal'

	register_sunat = fields.Selection([('1','Compras'),
								('2','Ventas'),
								('3','Honorarios'),
								('4','Retenciones'),
								('5','Percepciones'),
								('6','No Deducibles')],string='Registro Sunat')
	voucher_edit = fields.Boolean(string=u'Editar Asiento', default=False)
	check_surrender = fields.Boolean(string=u'Diario de Rendición',default=False)

	@api.constrains('type')
	def _check_type_in_journal_entries(self):
		self.env["account.move"].flush(["journal_id"])
		self.env.cr.execute("""select journal_id from account_move where journal_id = %d""" % (self.id))
		res = self.env.cr.dictfetchall()
		if len(res) > 0:
			raise ValidationError(u"No puede cambiar el Tipo de Diario si es que ya existen Asientos/Facturas.")
