# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools.translate import _

class AccountFollowupReport(models.AbstractModel):
	_inherit = "account.followup.report"

	def _get_lines(self, options, line_id=None):
		aml_dict = super(AccountFollowupReport,self)._get_lines(options, line_id)
		partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
		if not partner:
			return []
		lang_code = partner.lang if self._context.get('print_mode') else self.env.user.lang or get_lang(self.env).code

		for i in aml_dict:
			acc = self.env['account.move'].browse(i.get('move_id'))
			i['name'] = acc.ref if acc.ref else ''
			i['columns'][3]['name'] = acc.ref
			i['columns'][0]['name'] = format_date(self.env,acc.invoice_date, lang_code=lang_code)
		return aml_dict