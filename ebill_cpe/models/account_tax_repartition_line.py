from odoo import models, fields, api

class account_tax_repartition_line(models.Model):
	_inherit='account.tax.repartition.line'

	eb_afect_igv_id = fields.Many2one('einvoice.catalog.07',string='F.E. Tipo Afectacion IGV')
	eb_tributes_type_id = fields.Many2one('einvoice.catalog.05',string='F.E. Tipo de Tributos')
	tipo_de_isc  = fields.Many2one('einvoice.catalog.08',string='Tipo de ISC')