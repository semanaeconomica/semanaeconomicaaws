from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
	_inherit = 'account.move'

	def _auto_create_asset(self):
		t = super(AccountMove,self)._auto_create_asset()
		for asset in t:
			asset.type_document_id = asset.original_move_line_ids[0].move_id.type_document_id.id or None
			asset.nro_comp = asset.original_move_line_ids[0].move_id.ref or None
		return t
	
	@api.model
	def _prepare_move_for_asset_depreciation(self, vals):
		t = super(AccountMove,self)._prepare_move_for_asset_depreciation(vals)
		asset = vals['asset_id']
		t['type_document_id'] = asset.original_move_line_ids[0].move_id.type_document_id.id if asset.original_move_line_ids else None
		t['ref'] = asset.original_move_line_ids[0].move_id.ref if asset.original_move_line_ids else None
		t['line_ids'][0][2]['type_document_id'] = asset.original_move_line_ids[0].move_id.type_document_id.id if asset.original_move_line_ids else None
		t['line_ids'][0][2]['nro_comp'] = asset.original_move_line_ids[0].move_id.ref if asset.original_move_line_ids else None
		t['line_ids'][1][2]['type_document_id'] = asset.original_move_line_ids[0].move_id.type_document_id.id if asset.original_move_line_ids else None
		t['line_ids'][1][2]['nro_comp'] = asset.original_move_line_ids[0].move_id.ref if asset.original_move_line_ids else None
		return t