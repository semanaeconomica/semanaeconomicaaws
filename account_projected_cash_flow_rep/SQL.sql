DROP VIEW IF EXISTS public.vst_diariog_projected_cash CASCADE;

CREATE OR REPLACE VIEW public.vst_diariog_projected_cash AS
 SELECT row_number() OVER () AS id,
    tt.periodo,
    tt.fecha,
    tt.libro,
    tt.voucher,
    tt.cuenta,
    tt.debe,
    tt.haber,
    tt.balance,
    tt.moneda,
    tt.tc,
    tt.importe_me,
    tt.cta_analitica,
    tt.glosa,
    tt.td_partner,
    tt.doc_partner,
    tt.partner,
    tt.td_sunat,
    tt.nro_comprobante,
    tt.fecha_doc,
    tt.fecha_ven,
    tt.col_reg,
    tt.monto_reg,
    tt.medio_pago,
    tt.estado,
    tt.ple_diario,
    tt.ple_compras,
    tt.ple_ventas,
    tt.journal_id,
    tt.account_id,
    tt.partner_id,
    tt.registro,
    tt.move_id,
    tt.move_line_id,
    tt.company_id,
    tt.col_reg_id,
    tt.perception_date,
    tt.code_cta_analitica,
    tt.analytic_tag_ids,
	tt.analytic_tag_names
   FROM ( SELECT
                CASE
                    WHEN a1.is_opening_close = true AND to_char(a1.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(a1.date::timestamp with time zone, 'yyyy'::text) || '00'::text
                    WHEN a1.is_opening_close = true AND to_char(a1.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(a1.date::timestamp with time zone, 'yyyy'::text) || '13'::text
                    ELSE to_char(a1.date::timestamp with time zone, 'yyyymm'::text)
                END AS periodo,
            to_char(a1.date::timestamp with time zone, 'yyyy/mm/dd'::text) AS fecha,
            a3.code AS libro,
            a1.name AS voucher,
            a4.code AS cuenta,
            a2.debit AS debe,
            a2.credit AS haber,
            a2.balance,
                CASE
                    WHEN a2.currency_id IS NULL THEN 'PEN'::character varying
                    ELSE a5.name
                END AS moneda,
            coalesce(case when a2.tc = 0 then  1 else a2.tc end,1) as tc,
            a2.amount_currency AS importe_me,
            a2.analytic_account_id AS cta_analitica,
            a1.glosa,
            a7.code_sunat AS td_partner,
            a6.vat AS doc_partner,
            a6.name AS partner,
            a8.code AS td_sunat,
            REPLACE(a2.nro_comp,'/','-')::character varying AS nro_comprobante,
            a1.invoice_date AS fecha_doc,
            a2.date_maturity AS fecha_ven,
            a10.name AS col_reg,
            a2.tax_amount_it AS monto_reg,
            a12.code AS medio_pago,
            a1.state AS estado,
            a1.ple_state AS ple_diario,
            a1.campo_41_purchase AS ple_compras,
            a1.campo_34_sale AS ple_ventas,
            a1.journal_id,
            a2.account_id,
            a2.partner_id,
            a3.register_sunat AS registro,
            a1.id AS move_id,
            a2.id AS move_line_id,
            a1.company_id,
            a10.id AS col_reg_id,
            a1.perception_date,
            a11.name AS code_cta_analitica,
            a13.analytic_tag_ids,
			a13.analytic_tag_names
           FROM account_move a1
             LEFT JOIN account_move_line a2 ON a2.move_id = a1.id
             LEFT JOIN account_journal a3 ON a3.id = a1.journal_id
             LEFT JOIN account_account a4 ON a4.id = a2.account_id
             LEFT JOIN res_currency a5 ON a5.id = a2.currency_id
             LEFT JOIN res_partner a6 ON a6.id = a2.partner_id
             LEFT JOIN l10n_latam_identification_type a7 ON a7.id = a6.l10n_latam_identification_type_id
             LEFT JOIN einvoice_catalog_01 a8 ON a8.id = a2.type_document_id
             LEFT JOIN account_account_tag_account_move_line_rel a9 ON a9.account_move_line_id = a2.id
             LEFT JOIN account_account_tag a10 ON a10.id = a9.account_account_tag_id
             LEFT JOIN account_analytic_account a11 ON a11.id = a2.analytic_account_id
             LEFT JOIN einvoice_catalog_payment a12 ON a12.id = a1.td_payment_id
             LEFT JOIN (SELECT ARRAY_AGG(aatamlr.account_analytic_tag_id) as analytic_tag_ids,
						ARRAY_AGG(aat.name) AS analytic_tag_names, account_move_line_id 
						FROM account_analytic_tag_account_move_line_rel aatamlr
						LEFT JOIN account_analytic_tag aat ON aat.id = aatamlr.account_analytic_tag_id
						GROUP BY aatamlr.account_move_line_id) a13 ON a13.account_move_line_id = a2.id
          WHERE a1.state::text in ('posted','draft') AND a2.display_type IS NULL AND a2.account_id IS NOT NULL
          ORDER BY (date_part('month'::text, a1.date)), a3.code, a1.name, a2.debit DESC, a4.code) tt;

--------------------------------------------------------------------------------------------------------------------------------------------------

DROP FUNCTION IF EXISTS public.get_saldos_projected_cash(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_projected_cash(
	IN date_ini date,
	IN date_fin date,
	IN id_company integer)
  RETURNS TABLE(periodo text, fecha_con date, libro character varying, voucher character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric, saldo_mn numeric, saldo_me numeric,aml_ids integer[], journal_id integer, account_id integer, partner_id integer, move_id integer, move_line_id integer, company_id integer) AS
	$BODY$
	BEGIN

	RETURN QUERY 
		select 
		b2.periodo, 
		b2.fecha::date as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		CASE WHEN acc.date_due_option = '1' THEN am.date_aprox_payment ELSE b2.fecha_ven END AS fecha_ven,
		b2.cuenta,
		b2.moneda,
		b1.sum_debe as debe,
		b1.sum_haber as haber,
		b1.sum_balance as saldo_mn,
		b1.sum_importe_me as saldo_me,
		b1.aml_ids,
		b2.journal_id,
		b2.account_id,
		b2.partner_id,
		b2.move_id,
		b2.move_line_id,
		b2.company_id
		from(
		select a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante,
		sum(a1.debe) as sum_debe, sum(a1.haber) as sum_haber, sum(a1.balance) as sum_balance, 
		sum(a1.importe_me) as sum_importe_me, min(a1.move_line_id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from vst_diariog_projected_cash a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		having sum(a1.balance) <> 0
		)b1
		left join vst_diariog_projected_cash  b2 on b2.move_line_id = b1.min_line_id
		inner join account_data_projected_cash_flow acc on acc.account_id = b2.account_id
		left join account_move am on am.id = b2.move_id
		where (acc.is_draft = True AND am.state in ('draft','posted')) or (acc.is_draft <> True AND am.state in ('posted'))
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc;
	END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;