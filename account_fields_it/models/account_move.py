# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountMove(models.Model):
	_inherit = 'account.move'

	td_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago', copy=False)
	ple_state = fields.Selection([('1','Fecha del Comprobante Corresponde al Periodo'),
								('8','Corresponde a un Periodo Anterior y no ha sido Anotado en dicho Periodo'),
								('9','Corresponde a un Periodo Anterior y si ha sido Anotado en dicho Periodo')],string='Estado PLE Diario', default='1', copy=False)
	date_corre_ple = fields.Date(string='Fecha Correccion PLE Diario', copy=False)
	#SIRE
	c_sire = fields.Boolean(string=u'Complementa SIRE',copy=False,default=False)
	adj_sire = fields.Boolean(string=u'Ajuste SIRE',copy=False,default=False)
	corre_sire = fields.Selection([('0','Adicionar'),('1','Excluir'),('2','Incluir'),('3','Ajuste')],string='Tipo SIRE Compras', copy=False)
	#
	type_document_id = fields.Many2one('einvoice.catalog.01',string='Tipo de Documento')
	ref = fields.Char(string='Reference', copy=False)
	serie_id = fields.Many2one('it.invoice.serie',string='Serie')
	currency_rate = fields.Float(string='Tipo de Cambio',digits=(16,4),default=1)
	date = fields.Date(string='Date', required=True, index=True, readonly=True,states={'draft': [('readonly', False)]},default=fields.Date.context_today,copy=False)

	@api.model
	def _get_default_tc_per(self):
		move_type = self._context.get('default_type', 'entry')
		boole = False
		if move_type in self.get_sale_types(include_receipts=True):
			boole = True
		elif move_type in self.get_purchase_types(include_receipts=True):
			boole = True
		return boole

	tc_per = fields.Boolean(string='Usar Tc Personalizado',copy=False,default=_get_default_tc_per)
	glosa = fields.Char(string='Glosa')
	is_opening_close = fields.Boolean(string=u'Apertura/Cierre',default=False)
	perception_date = fields.Date(string='Fecha Uso Percepcion')
	es_editable = fields.Boolean('Es editable',related='journal_id.voucher_edit')
	is_descount = fields.Boolean(string=u'Es descuento', default=False)
	acc_number_partner_id = fields.Many2one('res.partner.bank',string=u'Cuenta Bancaria Partner',domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

	#Pestaña: SUNAT
	linked_to_detractions = fields.Boolean(string='Sujeto a Detracciones',default=False, copy=False)
	type_op_det = fields.Char(string=u'Tipo de Operación',size=2, copy=False, default='01')
	date_detraccion = fields.Date(string='Fecha', copy=False)
	code_operation = fields.Char(string='Bien o Servicio',size=5, copy=False)
	voucher_number = fields.Char(string='Numero de Comprobante', copy=False)
	detra_amount = fields.Float(string='Monto',digits=(16, 2), copy=False)
	linked_to_perception = fields.Boolean(string='Sujeto a Percepcion',default=False, copy=False)
	type_t_perception = fields.Char(string='Tipo Tasa Percepcion',size=3, copy=False)
	number_perception = fields.Char(string='Numero Percepcion',size=6, copy=False)
	petty_cash_id = fields.Many2one('account.petty.cash',string='Nro. Caja')
	switch = fields.Boolean(string='Actualizar', default=False)
	####Moving this field from saldos_cuentas_por_cobrar_it to here 'cause dependencies issues
	doc_origin_customer = fields.Char(string='Doc Origen Cliente', copy=False)

	automatic_destiny = fields.Boolean(string='Destino automatico',default=False, copy=False)

	#for SUNAT of accounting entries
	register_sunat = fields.Selection(string='Registro SUNAT',related='journal_id.register_sunat',readonly=True)

	#@api.returns('self', lambda value: value.id)
	#def copy(self, default=None):
	#	default = dict(default or {}, tc_per=self.tc_per)
	#	return super(AccountMove, self).copy(default=default)

	@api.onchange('partner_id')
	def _default_acc_number_partner_id(self):
		self.acc_number_partner_id = self.partner_id.bank_ids and self.partner_id.bank_ids[0]

	@api.constrains('name', 'journal_id', 'state','date')
	def _check_unique_sequence_number(self):
		moves = self.filtered(lambda move: move.state == 'posted')
		if not moves:
			return

		self.flush()

		# /!\ Computed stored fields are not yet inside the database.
		self._cr.execute('''
			SELECT move2.id
			FROM account_move move
			INNER JOIN account_move move2 ON
				move2.name = move.name
				AND move2.journal_id = move.journal_id
				AND move2.type = move.type
				AND EXTRACT (YEAR FROM move2.date) = EXTRACT (YEAR FROM move.date) 
				AND move2.id != move.id
			WHERE move.id IN %s AND move2.state = 'posted'
		''', [tuple(moves.ids)])
		res = self._cr.fetchone()
		if res:
			raise ValidationError(u"El número de Asiento ya existe en este año para la compañía : %s"%(str(res)))

	@api.constrains('ref', 'type', 'partner_id', 'journal_id', 'register_sunat','type_document_id')
	def _check_duplicate_supplier_reference(self):
		moves = self.filtered(lambda move: move.is_purchase_document() and move.ref)
		if not moves:
			return

		self.env["account.move"].flush([
			"ref", "type", "invoice_date", "journal_id",
			"company_id", "partner_id", "commercial_partner_id","register_sunat","type_document_id",
		])
		self.env["account.journal"].flush(["company_id", "type","register_sunat"])
		self.env["res.partner"].flush(["commercial_partner_id"])

		# /!\ Computed stored fields are not yet inside the database.
		self._cr.execute('''
			SELECT move2.id
			FROM account_move move
			JOIN account_journal journal ON journal.id = move.journal_id
			JOIN res_partner partner ON partner.id = move.partner_id
			INNER JOIN account_move move2 ON
					move2.ref = move.ref
					AND move2.type_document_id = move.type_document_id
					AND move2.company_id = journal.company_id
					AND move2.commercial_partner_id = partner.commercial_partner_id
					AND move2.type = move.type
					AND move2.id != move.id
			LEFT JOIN account_journal journal2 ON journal2.id = move2.journal_id
			WHERE journal2.register_sunat = journal.register_sunat AND
			move.id IN %s
		''', [tuple(moves.ids)])
		duplicated_moves = self.browse([r[0] for r in self._cr.fetchall()])
		if duplicated_moves:
			raise ValidationError(_('Duplicated vendor reference detected. You probably encoded twice the same vendor bill/credit note:\n%s') % "\n".join(
				duplicated_moves.mapped(lambda m: "%(partner)s - %(ref)s - %(type_document)s - Tipo (Diario - Registro Sunat):%(type)s" % {'ref': m.ref, 'partner': m.partner_id.display_name, 'type_document': m.type_document_id.name, 'type': dict(m.journal_id._fields['register_sunat'].selection).get(m.journal_id.register_sunat)})
			))

	@api.constrains('ref', 'type','type_document_id')
	def _check_duplicate_customer_reference(self):
		moves = self.filtered(lambda move: move.is_sale_document() and move.ref)
		if not moves:
			return

		self.env["account.move"].flush([
			"ref", "type", "invoice_date",
			"company_id","type_document_id",
		])

		self._cr.execute('''
			SELECT move2.id
			FROM account_move move
			INNER JOIN account_move move2 ON
					move2.ref = move.ref
					AND move2.type_document_id = move.type_document_id
					AND move2.company_id = move.company_id
					AND move2.type = move.type
					AND move2.id != move.id
			WHERE move.id IN %s
		''', [tuple(moves.ids)])
		duplicated_moves = self.browse([r[0] for r in self._cr.fetchall()])
		if duplicated_moves:
			raise ValidationError(_('Referencia de cliente duplicada detectada. Probablemente registró dos veces la misma factura / factura rectificativa del cliente:\n%s') % "\n".join(
				duplicated_moves.mapped(lambda m: "%(ref)s - %(type_document)s" % {'ref': m.ref, 'type_document': m.type_document_id.name})
			))

	@api.model
	def get_invoice_payment_term(self):
		invoice_payment_term = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).invoice_payment_term
		if not invoice_payment_term:
			return 1
		else:
			return invoice_payment_term.id

	invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
		domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
		readonly=True, states={'draft': [('readonly', False)]}, default=lambda self:self.get_invoice_payment_term())

	@api.onchange('type','ref')
	def domain_partner(self):
		if self.type in ['in_invoice','in_refund','in_receipt']:
			domain = [('supplier_rank','>',0),('parent_id','=',False)]
			res = {'domain': {'partner_id': domain}}
			return res
		if self.type in ['out_invoice','out_refund','out_receipt']:
			domain = [('customer_rank','>',0),('parent_id','=',False)]
			res = {'domain': {'partner_id': domain}}
			return res

	@api.onchange('ref','type_document_id')
	def _get_ref(self):
		if self.type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
			digits_serie = ('').join(self.type_document_id.digits_serie*['0'])
			digits_number = ('').join(self.type_document_id.digits_number*['0'])
			if self.ref:
				if '-' in self.ref:
					partition = self.ref.split('-')
					if len(partition) == 2:
						serie = digits_serie[:-len(partition[0])] + partition[0]
						number = digits_number[:-len(partition[1])] + partition[1]
						self.ref = serie + '-' + number

	def action_change_name(self):
		for move in self:
			if move.state == 'draft':
				move.name = "/"
			else:
				raise UserError("No puede alterar el nombre si no se encuentra en estado Borrador")

		return self.env['popup.it'].get_message('Se borro correctamente la secuencia.')


	def action_change_line(self):
		if self.type not in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
			sql = """update account_move_line set debit = 1 where move_id = """+str(self.id)+""" and credit = 0 and debit = 0 """
			self.env.cr.execute(sql)
			return self.env['popup.it'].get_message('Se actualizaron correctamente las lineas.')
		else:
			raise UserError("No es un asiento")

	def show_move_line_ids(self):
		self.ensure_one()
		action = self.env.ref('account.action_account_moves_all').read()[0]
		domain = [('id', 'in', self.line_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_line_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)
		
	def post(self):
		for move in self:
			if move.partner_id.p_detraction and move.amount_total_signed:
				move.detra_amount = abs(move.amount_total_signed) * (float(move.partner_id.p_detraction)/100.0)
		return super(AccountMove, self).post()

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	type_document_id = fields.Many2one('einvoice.catalog.01',string='T.D.')
	nro_comp = fields.Char(string='Nro Comp.',size=40)
	tc = fields.Float(string='T.C.',digits=(12,4),default=1)
	cash_flow_id = fields.Many2one('account.cash.flow',string="Flujo Caja")
	tax_amount_it = fields.Monetary(default=0.0, currency_field='company_currency_id',string='Importe Imp.')
	tax_amount_me = fields.Monetary(default=0.0,string='Importe Imp. ME')
	cuo = fields.Integer(string="CUO")
	location_id = fields.Many2one('stock.location', string='Almacen')
	is_advance_check = fields.Boolean(string='ANT.',default=False)

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