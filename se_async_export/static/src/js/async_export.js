odoo.define('se_async_export.AsyncExport', function (require) {
    "use strict";

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var DataExport = require('web.DataExport');
    var framework = require('web.framework');

    var _t = core._t;

    var POLL_INTERVAL = 3000;        // ms entre polls de /status
    var ASYNC_THRESHOLD = 5000;      // >= este count → usar flujo async

    // ------------------------------------------------------------------
    // Modal de progreso del export asíncrono
    // ------------------------------------------------------------------
    var ProgressDialog = Dialog.extend({
        template: 'se_async_export.ProgressModal',

        init: function (parent, options) {
            this.jobId = options.jobId;
            this.totalRows = options.totalRows;
            this.progress = 0;
            this._destroyed = false;
            this._pollHandle = null;

            this._super(parent, {
                title: _t("Preparando tu archivo..."),
                size: 'medium',
                buttons: [],    // se cierra automáticamente al finalizar
                renderFooter: false,
            });
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._updateProgress(0);
                self._schedulePoll();
            });
        },

        destroy: function () {
            this._destroyed = true;
            if (this._pollHandle) {
                clearTimeout(this._pollHandle);
                this._pollHandle = null;
            }
            this._super.apply(this, arguments);
        },

        _schedulePoll: function () {
            var self = this;
            this._pollHandle = setTimeout(function () {
                if (self._destroyed) return;
                self._poll();
            }, POLL_INTERVAL);
        },

        _poll: function () {
            var self = this;
            this._rpc({
                route: '/se_export/status',
                params: { job_id: this.jobId },
            }).then(function (result) {
                if (self._destroyed) return;
                self._onStatus(result);
            }).guardedCatch(function () {
                // error transitorio de red → reintentar en el próximo tick
                if (self._destroyed) return;
                self._schedulePoll();
            });
        },

        _onStatus: function (result) {
            this._updateProgress(result.progress || 0);

            if (result.state === 'done' && result.attachment_url) {
                this._triggerDownload(result.attachment_url, result.filename);
                this.close();
                return;
            }
            if (result.state === 'failed') {
                var msg = result.error_msg || _t("Error generando el archivo.");
                this.close();
                Dialog.alert(this.getParent(), msg, {
                    title: _t("Export fallido"),
                });
                return;
            }
            // pending | running → seguimos polleando
            this._schedulePoll();
        },

        _updateProgress: function (pct) {
            this.progress = pct;
            var txt = pct + '%';
            this.$('.progress-bar')
                .css('width', txt)
                .attr('aria-valuenow', pct)
                .text(txt);
            this.$('.o_async_export_rows').text(
                _t("Filas: ") + this.totalRows
            );
        },

        _triggerDownload: function (url, filename) {
            // Disparar la descarga sin navegar fuera de Odoo
            var a = document.createElement('a');
            a.href = url;
            a.download = filename || '';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        },
    });

    // ------------------------------------------------------------------
    // Include al DataExport nativo: intercepta el click Export
    // ------------------------------------------------------------------
    DataExport.include({
        /**
         * @override
         * Si el formato es xlsx y el count del dominio es grande,
         * dispara el flujo async. En otro caso, comportamiento nativo.
         */
        _exportData: function (exportedFields, exportFormat, idsToExport) {
            var _super = this._super.bind(this);
            var args = arguments;

            // CSV, o selección manual de IDs, o menos que el umbral → nativo
            if (exportFormat !== 'xlsx' || idsToExport) {
                return _super.apply(this, args);
            }

            var self = this;
            return this._rpc({
                model: this.record.model,
                method: 'search_count',
                args: [this.domain || []],
            }).then(function (count) {
                if (count < ASYNC_THRESHOLD) {
                    return _super.apply(self, args);
                }
                return self._runAsyncExport(exportedFields, count);
            });
        },

        _runAsyncExport: function (exportedFields, count) {
            var self = this;
            framework.blockUI();
            return this._rpc({
                route: '/se_export/start',
                params: {
                    model: this.record.model,
                    domain: this.domain || [],
                    fields: exportedFields,
                    name: (_t("Export") + ' ' + this.record.model +
                           ' (' + count + ')'),
                },
            }).then(function (result) {
                framework.unblockUI();
                var parent = self.getParent();
                self.close();    // cierra el dialog de DataExport
                new ProgressDialog(parent, {
                    jobId: result.job_id,
                    totalRows: result.total_rows,
                }).open();
            }).guardedCatch(function () {
                framework.unblockUI();
            });
        },
    });

    return { ProgressDialog: ProgressDialog };
});
