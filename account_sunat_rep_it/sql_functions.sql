DROP FUNCTION IF EXISTS public.get_detalle_pdf_10(integer, integer,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_detalle_pdf_10(
	periodo_apertura integer,
	periodo integer,
	company_id integer)
    RETURNS TABLE(cuenta character varying, nomenclatura character varying, code_bank character varying, account_number character varying, moneda integer, debe numeric, haber numeric, account_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY 
SELECT 
aa.code as cuenta,
aa.name as nomenclatura,
aa.code_bank,
aa.account_number,
CASE 
	WHEN rc.name = 'USD' THEN 2 ELSE 1
END AS moneda,
T.debe,
T.haber,
T.account_id
FROM
(SELECT vst.account_id,SUM(vst.debe) AS debe,SUM(vst.haber) AS haber FROM vst_diariog vst
LEFT JOIN account_account aa ON aa.id = vst.account_id
WHERE LEFT(vst.cuenta,2) = '10' AND (CAST(vst.periodo AS int) BETWEEN $1 AND $2)
AND vst.company_id = $3
GROUP BY vst.account_id)T
LEFT JOIN account_account aa ON aa.id = T.account_id
LEFT JOIN res_currency rc ON rc.id = aa.currency_id;
END;
$BODY$;