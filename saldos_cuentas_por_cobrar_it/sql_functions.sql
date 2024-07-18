DROP FUNCTION IF EXISTS public.get_saldos_fxc(character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_fxc(
	anio character varying,
	id_company integer)
    RETURNS TABLE(ide text, pventa_mn numeric, pagos_mn numeric,pventa_me numeric,pagos_me numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY 
 SELECT concat(a1.partner_id, '-', a1.type_document_id, '-', a1.nro_comp, '-', a1.account_id) AS ide,
    sum(a1.debit) AS pventa_mn,
    sum(a1.credit) AS pagos_mn,
    sum(
        CASE
            WHEN a1.debit <> 0::numeric THEN a1.amount_currency
            ELSE 0::numeric
        END) AS pventa_me,
    abs(sum(
        CASE
            WHEN a1.credit <> 0::numeric THEN a1.amount_currency
            ELSE 0::numeric
        END)) AS pagos_me
   FROM account_move_line a1
     LEFT JOIN account_move a2 ON a2.id = a1.move_id
  WHERE a2.state = 'posted' AND a1.account_internal_type::text = 'receivable'::text AND a1.type_document_id <> (( SELECT einvoice_catalog_01.id
           FROM einvoice_catalog_01
          WHERE einvoice_catalog_01.code::text = '07'::text)) AND to_char(a2.date::timestamp with time zone, 'yyyy'::text) = $1 AND a2.company_id = $2
  GROUP BY (concat(a1.partner_id, '-', a1.type_document_id, '-', a1.nro_comp, '-', a1.account_id))
UNION ALL
 SELECT concat(a1.partner_id, '-', a1.type_document_id, '-', a1.nro_comp, '-', a1.account_id) AS ide,
    - sum(a1.credit) AS pventa_mn,
    - sum(a1.debit) AS pagos_mn,
    sum(
        CASE
            WHEN a1.credit <> 0::numeric THEN a1.amount_currency
            ELSE 0::numeric
        END) AS pventa_me,
    - sum(
        CASE
            WHEN a1.debit <> 0::numeric THEN a1.amount_currency
            ELSE 0::numeric
        END) AS pagos_me
   FROM account_move_line a1
     LEFT JOIN account_move a2 ON a2.id = a1.move_id
  WHERE a2.state = 'posted' AND a1.account_internal_type::text = 'receivable'::text AND a1.type_document_id = (( SELECT einvoice_catalog_01.id
           FROM einvoice_catalog_01
          WHERE einvoice_catalog_01.code::text = '07'::text)) AND to_char(a2.date::timestamp with time zone, 'yyyy'::text) = $1 AND a2.company_id = $2
  GROUP BY (concat(a1.partner_id, '-', a1.type_document_id, '-', a1.nro_comp, '-', a1.account_id));
END;
$BODY$;
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_cab_cpc(integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_cab_cpc(
	id_company integer)
    RETURNS TABLE(ide text, move_id integer, vendedor integer,partner_id integer,fecha_emi date,fecha_ven date, type_document_id integer, nro_comp character varying, account_id integer, currency_id integer, doc_origin_customer character varying) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY 
 SELECT concat(a1.partner_id, '-', a1.type_document_id, '-', a1.nro_comp, '-', a1.account_id) AS ide,
    a1.move_id,
    a2.invoice_user_id AS vendedor,
    a1.partner_id,
    a2.invoice_date AS fecha_emi,
    a2.invoice_date_due AS fecha_ven,
    a1.type_document_id,
    a1.nro_comp,
    a1.account_id,
	CASE
		WHEN a1.currency_id IS NULL THEN ( SELECT res_company.currency_id
		   FROM res_company
		  WHERE res_company.id = $1)
		ELSE a1.currency_id
	END AS currency_id,
    a2.doc_origin_customer
   FROM account_move_line a1
     RIGHT JOIN ( SELECT account_move.id,
            account_move.invoice_user_id,
            account_move.invoice_date,
            account_move.invoice_date_due,
            account_move.doc_origin_customer
           FROM account_move
          WHERE account_move.type::text in ('out_invoice','out_refund') AND account_move.state::text = 'posted'::text AND account_move.company_id = $1) a2 ON a2.id = a1.move_id
  WHERE a1.account_internal_type::text = 'receivable'::text AND a1.company_id = $1
UNION ALL
 SELECT concat(a1.partner_id, '-', 1, '-', a1.nro_letra, '-', a1.account_id) AS ide,
    a2.asiento_id AS move_id,
    a1.letra_user_id AS vendedor,
    a1.partner_id,
    a1.date_exchange AS fecha_emi,
    a1.expiration_date AS fecha_ven,
    (select id from einvoice_catalog_01 where code = '00' limit 1) AS type_document_id,
    a1.nro_letra AS nro_comp,
    a1.account_id,
    a1.currency_id,
    '' as doc_origin_customer
   FROM account_letras_payment_manual a1
     LEFT JOIN account_letras_payment a2 ON a2.id = a1.letra_payment_id
  WHERE a2.state::text = 'done'::text AND a2.type::text = 'out'::text AND a1.company_id = $1;
END;
$BODY$;