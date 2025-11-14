# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class EinvoiceCatalog01(models.Model):
	_inherit = 'einvoice.catalog.01'

	def unlink(self):
		for einvoice in self:
			self.env.cr.execute("""select id from account_move where type_document_id = %d""" % (einvoice.id))
			res = self.env.cr.dictfetchall()

			self.env.cr.execute("""select id from account_payment where type_document_id = %d or type_doc_cash_id = %d""" % (einvoice.id,einvoice.id))
			res2 = self.env.cr.dictfetchall()

			self.env.cr.execute("""select id from account_move_line where type_document_id = %d""" % (einvoice.id))
			res3 = self.env.cr.dictfetchall()
			if len(res) > 0 or len(res2) > 0 or len(res3) > 0:
				raise UserError("No puede eliminar un Tipo de Comprobante que se esta usando en Facturas/Asientos/Pagos")
		return super(EinvoiceCatalog01, self).unlink()