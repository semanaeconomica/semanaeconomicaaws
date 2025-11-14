odoo.define('account_reconcile_it.inheritance', function (require){
"use strict";

var StatementModel = require('account.ReconciliationModel').StatementModel;

var StatementModel = StatementModel.include({
	_formatToProcessReconciliation: function (line, prop) {
		var result = this._super(line, prop);
		result['nro_comp'] = prop.nro_comp;
		result['type_document_id'] = prop.type_document_id;
		return result;
	},
});
return {
	StatementModel : StatementModel,
};

});