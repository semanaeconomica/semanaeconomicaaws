------------------------------------------account_balance_doc_rep_it---------------------------------------------------------------
----------Obtenemos los saldos por fecha de documento,fecha de documento y si el balance es 0 , fecha contable ,fecha contable y si el balance es 0

DROP FUNCTION IF EXISTS public.get_saldos(date, date, integer, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos(
    IN date_ini date,
    IN date_fin date,
    IN id_company integer,
    IN query_type integer)
  RETURNS TABLE(id bigint, periodo text, fecha_con text, libro character varying, voucher character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric, saldo_mn numeric, saldo_me numeric,aml_ids integer[], journal_id integer, account_id integer, partner_id integer, move_id integer, move_line_id integer, company_id integer) AS
$BODY$
BEGIN
	IF query_type = 0 THEN
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
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
		from vst_diariog a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		)b1
		left join vst_diariog  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	ELSIF query_type = 1 THEN
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
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
		from vst_diariog a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		having sum(a1.balance) <> 0
		)b1
		left join vst_diariog  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	ELSIF query_type = 2 THEN 
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
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
		from vst_diariog a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha_doc::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		)b1
		left join vst_diariog  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	ELSIF query_type = 3 THEN 
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
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
		from vst_diariog a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha_doc::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		having sum(a1.balance) <> 0
		)b1
		left join vst_diariog  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	END IF;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

---------------------------------------------------------------------------------------------------------------------------------------------------------------
----------Con esta funcion obtenemos el detalle de comprobante, donde los parametros son fecha inicial, fecha final y company_id

DROP FUNCTION IF EXISTS public.get_saldo_detalle(date, date, integer) CASCADE;
CREATE OR REPLACE FUNCTION public.get_saldo_detalle(
    IN fec_ini date,
    IN fec_fin date,
    IN id_compannia integer)
  RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying,td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric,balance numeric,importe_me numeric, saldo numeric, saldo_me numeric, partner_id integer, account_id integer) AS
$BODY$
DECLARE 
    var_r record;
    quiebre TEXT;
    contador INT;
BEGIN
   contador = 0 ;
   saldo = 0;
   saldo_me = 0;
   FOR var_r IN(
        select 
		vst_d.periodo, 
		vst_d.fecha, 
		vst_d.libro, 
		vst_d.voucher,
		vst_d.td_partner, 
		vst_d.doc_partner, 
		vst_d.partner, 
		vst_d.td_sunat, 
		vst_d.nro_comprobante, 
		vst_d.fecha_doc, 
		vst_d.fecha_ven, 
		vst_d.cuenta, 
		vst_d.moneda, 
		vst_d.debe, 
		vst_d.haber,
		vst_d.balance,
		vst_d.importe_me,
		vst_d.partner_id,
		vst_d.account_id
		from vst_diariog vst_d
		left join account_account aa on aa.id = vst_d.account_id
		where aa.is_document_an = True and (vst_d.fecha::date between fec_ini::date and fec_fin::date) and vst_d.company_id = id_compannia
		order by vst_d.partner_id,vst_d.account_id,vst_d.td_sunat,vst_d.nro_comprobante,vst_d.fecha       
               )
   LOOP
        -- Obtiene por unica vez el valor del primer registro
        IF contador = 0 THEN 
            quiebre := concat(var_r.partner_id,var_r.account_id,var_r.td_sunat,var_r.nro_comprobante);
            contador = contador + 1;
        END IF;
        
        -- Si los registros son los mismos
        IF quiebre =  concat(var_r.partner_id,var_r.account_id,var_r.td_sunat,var_r.nro_comprobante) THEN
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        -- Si cambia, reinicio el saldo y actualizo
        ELSE
            saldo = 0;
            saldo_me = 0;
            quiebre := concat(var_r.partner_id,var_r.account_id,var_r.td_sunat,var_r.nro_comprobante);
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        END IF;

        periodo = var_r.periodo ;
        fecha = var_r.fecha ;
        libro = var_r.libro ;
        voucher = var_r.voucher ;
        td_partner = var_r.td_partner ;
        doc_partner = var_r.doc_partner;
        partner = var_r.partner;
        td_sunat = var_r.td_sunat ;
        nro_comprobante  = var_r.nro_comprobante ;
        fecha_doc = var_r.fecha_doc ;
        fecha_ven  = var_r.fecha_ven ;
        cuenta  = var_r.cuenta ;
        moneda  = var_r.moneda ;
        debe = var_r.debe ;
        haber  = var_r.haber ;
        balance = var_r.balance ;
        importe_me  = var_r.importe_me ;
        partner_id = var_r.partner_id ;
        account_id = var_r.account_id ;
        
   RETURN NEXT;
   END LOOP;
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

------------------------------------------account_balance_doc_rep_it---------------------------------------------------------------
UPDATE account_account SET is_document_an=TRUE WHERE internal_type IN ('payable','receivable');
UPDATE account_account SET is_document_an=FALSE WHERE internal_type NOT IN ('payable','receivable');
------------------------------------------exchange_diff_config_it--------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_saldos_me_global(
	periodo_apertura character,
	periodo character,
	company_id integer)
    RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY   
	SELECT a1.account_id,
		sum(a1.debe) AS debe,
		sum(a1.haber) AS haber,
		sum(coalesce(a1.balance,0)) AS saldomn,
		sum(coalesce(a1.importe_me,0)) AS saldome
	   	FROM vst_diariog a1
		LEFT JOIN account_account a2 ON a2.id = a1.account_id
		LEFT JOIN res_currency a4 on a4.id = a2.currency_id
	  	WHERE a4.name = 'USD' AND
		a2.is_document_an <> TRUE AND a1.periodo::integer >= $1::integer AND a1.periodo::integer <= $2::integer AND a1.company_id = $3
	  	GROUP BY a1.account_id;
END;
$BODY$;

--------------------------------------------------------------------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_saldos_me_global_2(
	periodo_apertura character,
	periodo character,
	company_id integer)
    RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
 SELECT
    b1.account_id,
    b1.debe,
    b1.haber,
    b1.saldomn,
    b1.saldome,
    b3.group_balance,
        CASE
            WHEN b3.group_balance::text = ANY (ARRAY['B1'::character varying, 'B2'::character varying]::text[]) THEN ( SELECT edcl.compra
               FROM exchange_diff_config_line edcl
                 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
                 LEFT JOIN account_period ap ON ap.id = edcl.period_id
              WHERE edc.company_id = $3 AND ap.code::text = $2::text)
            ELSE ( SELECT edcl.venta
               FROM exchange_diff_config_line edcl
                 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
                 LEFT JOIN account_period ap ON ap.id = edcl.period_id
              WHERE edc.company_id = $3 AND ap.code::text = $2::text)
        END AS tc
   FROM get_saldos_me_global($1,$2,$3) b1
     LEFT JOIN account_account b2 ON b2.id = b1.account_id
     LEFT JOIN account_type_it b3 ON b3.id = b2.account_type_it_id;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_saldos_me_global_final(
	fiscal_year character,
	periodo character,
	company_id integer)
    RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric, saldo_act numeric, diferencia numeric, difference_account_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	SELECT *,
	round(coalesce(vst.tc,0) * vst.saldome,2) AS saldo_act,
	vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) AS diferencia,
	CASE 
	WHEN vst.saldomn < round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN vst.saldomn > round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) > (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) < (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3) END AS difference_account_id
	FROM get_saldos_me_global_2($1||'00',$2,$3) vst
	WHERE vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) <> 0;
END;
$BODY$;
----------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento(
	periodo_apertura character,
	periodo character,
	company_id integer)
    RETURNS TABLE(partner integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY   
	select a1.partner_id,
	a1.account_id,
	a1.td_sunat,
	a1.nro_comprobante,
	sum(a1.debe) debe,
	sum(a1.haber) haber,
	sum(coalesce(a1.balance,0))as saldomn,
	sum(coalesce(a1.importe_me,0)) as saldome 
	from vst_diariog a1
	left join account_account a2 on a2.id=a1.account_id
	left join account_type_it a3 on a3.id=a2.account_type_it_id
	left join res_currency a4 on a4.id = a2.currency_id
	where 
	a2.is_document_an = TRUE and
	a4.name = 'USD' and
	a1.td_sunat is not null and
	a1.nro_comprobante is not null and
	a1.company_id = $3 and
	(a1.periodo::int between $1::int and $2::int)
	group by a1.partner_id,a1.account_id,a1.td_sunat,a1.nro_comprobante
	having (sum(a1.balance)+sum(a1.importe_me)) <> 0;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento_2(
	periodo_apertura character,
	periodo character,
	company_id integer)
    RETURNS TABLE(partner integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
select b1.partner,
b1.account_id,
b1.td_sunat,
b1.nro_comprobante,
b1.debe,
b1.haber,
b1.saldomn,
b1.saldome,
b3.group_balance,
CASE
		WHEN b3.group_balance::text = ANY (ARRAY['B1'::character varying, 'B2'::character varying]::text[]) THEN ( SELECT edcl.compra
		   FROM exchange_diff_config_line edcl
			 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
			 LEFT JOIN account_period ap ON ap.id = edcl.period_id
		  WHERE edc.company_id = $3 AND ap.code::text = $2::text)
		ELSE ( SELECT edcl.venta
		   FROM exchange_diff_config_line edcl
			 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
			 LEFT JOIN account_period ap ON ap.id = edcl.period_id
		  WHERE edc.company_id = $3 AND ap.code::text = $2::text)
	END AS tc
from get_saldos_me_documento($1,$2,$3) b1
LEFT JOIN account_account b2 ON b2.id = b1.account_id
LEFT JOIN account_type_it b3 ON b3.id = b2.account_type_it_id;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento_final(
	fiscal_year character,
	periodo character,
	company_id integer)
    RETURNS TABLE(partner integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric, saldo_act numeric, diferencia numeric, difference_account_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	SELECT *,
	round(coalesce(vst.tc,0) * vst.saldome,2) AS saldo_act,
	vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) AS diferencia,
	CASE 
	WHEN vst.saldomn < round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN vst.saldomn > round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) > (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) < (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3) END AS difference_account_id
	FROM get_saldos_me_documento_2($1||'00',$2,$3) vst
	WHERE vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) <> 0;
END;
$BODY$;

------------------------------------------exchange_diff_config_it--------------------------------------------------------------------------------------
------------------------------------------maturity_analysis_rep_it------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_maturity_analysis(date, date, integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_maturity_analysis(
	first_date date,
	end_date date,
	company_id integer,
	type character varying)
    RETURNS TABLE(fecha_emi date, fecha_ven date, cuenta character varying, divisa character varying, tdp character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, saldo_mn numeric, saldo_me numeric, partner_id integer, cero_treinta numeric, treinta1_sesenta numeric, sesenta1_noventa numeric, noventa1_ciento20 numeric, ciento21_ciento50 numeric, ciento51_ciento80 numeric, ciento81_mas numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	select 
	b1.fecha_emi,
	b1.fecha_ven,
	b1.cuenta,
	b1.divisa,
	b1.tdp,
	b1.doc_partner,
	b1.partner,
	b1.td_sunat,
	b1.nro_comprobante,
	b1.saldo_mn,
	b1.saldo_me,
	b1.partner_id,
	case when b1.atraso between 0 and 30 then b1.saldo_mn else 0 end as cero_treinta,
	case when b1.atraso between 31 and 60 then b1.saldo_mn else 0 end as treinta1_sesenta,
	case when b1.atraso between 61 and 90 then b1.saldo_mn else 0 end as sesenta1_noventa,
	case when b1.atraso between 91 and 120 then b1.saldo_mn else 0 end as noventa1_ciento20,
	case when b1.atraso between 121 and 150 then b1.saldo_mn else 0 end as ciento21_ciento50,
	case when b1.atraso between 151 and 180 then b1.saldo_mn else 0 end as ciento51_ciento80,
	case when b1.atraso >180 then b1.saldo_mn else 0 end as ciento81_mas 
	from
	(
	select 
	case when a1.fecha_doc::date is null then a1.fecha_con::date else a1.fecha_doc::date end as fecha_emi,
	a1.fecha_ven as fecha_ven,
	a1.cuenta as cuenta,
	case when a3.name is not null then a3.name else 'PEN' end as divisa,
	a1.td_partner as tdp,
	a1.doc_partner as doc_partner,
	a1.partner,
	a1.td_sunat,
	a1.nro_comprobante,
	case when  a2.internal_type='receivable' then a1.saldo_mn else -a1.saldo_mn end as saldo_mn,
	case when  a2.internal_type='receivable' then a1.saldo_me else -a1.saldo_me end as saldo_me,
	case when a1.fecha_ven is not null then $2 - a1.fecha_ven else 0 end as atraso,
	a1.account_id,
	a2.internal_type,
	a1.partner_id
	from 
	get_saldos($1,$2,$3,1) a1
	left join account_account a2 on a2.id=a1.account_id
	left join res_currency a3 on a3.id=a2.currency_id
	where a1.nro_comprobante is not null
	)b1
	where b1.internal_type = $4;
END;
$BODY$;
------------------------------------------maturity_analysis_rep_it------------------------------------------------------------------------------------------------------------