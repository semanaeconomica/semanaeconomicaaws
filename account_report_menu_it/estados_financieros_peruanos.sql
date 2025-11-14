CREATE OR REPLACE FUNCTION public.get_bc_register(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer)
  RETURNS TABLE(mayor text, cuenta character varying, nomenclatura text, 
                debe numeric(64,2), haber numeric(64,2), saldo_deudor numeric(64,2), 
                saldo_acreedor numeric(64,2), rubro text) AS
$BODY$
BEGIN

RETURN QUERY 
    select
    min(substring(aa.code,0,3)) as mayor,
    aa.code as cuenta,
    min(aa.name) as nomenclatura,
    sum(vd.debe) as debe,
    sum(vd.haber) as haber,
    case 
        when sum(vd.debe) > sum(vd.haber)
        then sum(vd.debe) - sum(vd.haber)
        else 0
    end as saldo_deudor,
    case
        when sum(vd.haber) > sum(vd.debe)
        then sum(vd.haber) - sum(vd.debe)
        else 0
    end as saldo_acreedor,
    min(ati.name) as rubro
    from vst_diariog vd
    left join (select code, name, account_type_it_id from account_account where company_id = $3) aa on aa.code = vd.cuenta
    left join account_type_it ati on ati.id = aa.account_type_it_id
    where (cast(vd.periodo as int ) between cast($1 as int ) and cast($2 as int )) and vd.company_id = $3 
    group by aa.code;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

------------------------------------------account_bc_report---------------------------------------------------------------

------------------------------------------account_efective_rep_it---------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_efective_flow(
	periodo_ini character varying,
	periodo_fin character varying,
	period_saldo_inicial character varying,
	company integer)
    RETURNS TABLE(name character varying, efective_group character varying, total numeric, efective_order integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN

RETURN QUERY

SELECT T.* FROM (SELECT aet.name, aet.group as efective_group, SUM(aml.balance)*-1 as total, aet.order as efective_order FROM account_move_line aml
LEFT JOIN account_account aa ON aa.id = aml.account_id
LEFT JOIN account_efective_type aet ON aet.id = aa.account_type_cash_id
WHERE LEFT(aa.code,2) <> '10' AND aa.account_type_cash_id IS NOT NULL AND aml.move_id in (
SELECT
DISTINCT ON (aml.move_id) move_id
FROM account_move_line aml
LEFT JOIN account_account aa ON aa.id = aml.account_id
LEFT JOIN account_move am ON am.id = aml.move_id
WHERE am.state = 'posted' AND am.company_id = $4 AND aml.display_type IS NULL AND am.is_opening_close <> TRUE
AND (am.date BETWEEN $1::date AND $2::date)
AND LEFT(aa.code,2) = '10')
GROUP BY aet.name, aet.group, aet.order

UNION ALL

SELECT 'Saldo EFECT y EQUIV de EFECT al inicio del Ejercicio' as name, 'E7' as efective_group, SUM(aml.balance) as total, -1 as efective_order FROM account_move_line aml
LEFT JOIN account_account aa ON aa.id = aml.account_id
LEFT JOIN account_move am ON am.id = aml.move_id
LEFT JOIN account_efective_type aet ON aet.id = aa.account_type_cash_id
WHERE LEFT(aa.code,2) = '10' AND am.state = 'posted' AND am.company_id = $4 AND aml.display_type IS NULL
AND (CASE
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
		ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
	END = $3)
				)T
ORDER BY T.efective_order;

END;
$BODY$;

-------------------------------------------------account_efective_rep_it------------------------------------------------------------------

-------------------------------------------------account_htf1_report------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f1_register(character varying,character varying,integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f1_register(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer,
	IN currency character varying)
  RETURNS TABLE(mayor text, cuenta character varying, nomenclatura character varying, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric, rubro character varying) AS
$BODY$
BEGIN

RETURN QUERY 
    
	select left(aa.code,2) as mayor,aa.code as cuenta,aa.name as nomenclatura,T.debe,T.haber,
		   T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and aa.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and aa.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun,
	ati.name as rubro
	from(
	select
	vd.account_id,
	CASE WHEN $4 = 'pen' THEN sum(vd.debe) ELSE sum(coalesce(vst_diariog_me.debe_me,0)) END as debe,
	CASE WHEN $4 = 'pen' THEN sum(vd.haber) ELSE sum(coalesce(vst_diariog_me.haber_me,0)) END as haber,
	case 
		when (CASE WHEN $4 = 'pen' THEN sum(vd.debe) ELSE sum(coalesce(vst_diariog_me.debe_me,0)) END) > (CASE WHEN $4 = 'pen' THEN sum(vd.haber) ELSE sum(coalesce(vst_diariog_me.haber_me,0)) END)
		then (CASE WHEN $4 = 'pen' THEN sum(vd.debe) ELSE sum(coalesce(vst_diariog_me.debe_me,0)) END) - (CASE WHEN $4 = 'pen' THEN sum(vd.haber) ELSE sum(coalesce(vst_diariog_me.haber_me,0)) END)
		else 0
	end as saldo_deudor,
	case
		when (CASE WHEN $4 = 'pen' THEN sum(vd.haber) ELSE sum(coalesce(vst_diariog_me.haber_me,0)) END) > (CASE WHEN $4 = 'pen' THEN sum(vd.debe) ELSE sum(coalesce(vst_diariog_me.debe_me,0)) END)
		then (CASE WHEN $4 = 'pen' THEN sum(vd.haber) ELSE sum(coalesce(vst_diariog_me.haber_me,0)) END) - (CASE WHEN $4 = 'pen' THEN sum(vd.debe) ELSE sum(coalesce(vst_diariog_me.debe_me,0)) END)
		else 0
	end as saldo_acreedor
	from vst_diariog as vd 
	LEFT JOIN vst_diariog_me on vst_diariog_me.move_id = vd.move_id and vst_diariog_me.move_line_id = vd.move_line_id
	where vd.company_id = $3 and (cast(vd.periodo as int ) between cast($1 as int ) and cast($2 as int ))
	group by vd.account_id
	)T
	left join (select * from account_account where company_id = $3) aa on aa.id = T.account_id
	left join account_type_it ati on ati.id = aa.account_type_it_id
	order by left(aa.code,2),aa.code
	;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
-------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f1_balance(character varying,character varying,integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f1_balance(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer,
	IN currency character varying)
  RETURNS TABLE(mayor text, nomenclatura character varying, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric) AS
$BODY$
BEGIN

RETURN QUERY 
    
	select T.mayor,T.name,T.debe,T.haber,
		   T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and ag.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and ag.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun
	from(
		select
		f1r.mayor,
		ag.name,
		ag.id,
		sum(f1r.debe) as debe,
		sum(f1r.haber) as haber,
		case 
			when sum(f1r.debe) > sum(f1r.haber) 
			then sum(f1r.debe) - sum(f1r.haber)
			else 0
		end as saldo_deudor,
		case
			when sum(f1r.haber) > sum(f1r.debe)
			then sum(f1r.haber) - sum(f1r.debe)
			else 0
		end as saldo_acreedor
		from get_f1_register($1,$2,$3,$4) f1r
		left join account_group ag on ag.code_prefix = f1r.mayor
    	group by f1r.mayor,ag.name,ag.id)T
	inner join account_group ag on ag.id = T.id
	order by T.mayor;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

-------------------------------------------------account_htf1_report------------------------------------------------------------------

-------------------------------------------------account_htf2_report------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f2_register(character varying,integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f2_register(
	IN period character varying,
	IN company integer,
	IN currency character varying)
    RETURNS TABLE(mayor text, cuenta character varying, nomenclatura character varying, debe_inicial numeric, haber_inicial numeric, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric, rubro character varying) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
    
AS $BODY$
BEGIN
RETURN QUERY 
	select 
		left(cta.code,2) as mayor,
		cta.code as cuenta,
		cta.name as nomenclatura,
		t.debeini as debe_inicial,
		t.haberini as haber_inicial,
		t.debep as debe,
		t.haberp as haber,
		t.saldo_deudor,
		t.saldo_acreedor,
			case 
				when t.saldo_deudor > 0 and cta.clasification_sheet = '0'
				then t.saldo_deudor
				else 0.00
			end as activo,
			case 
				when t.saldo_acreedor > 0 and cta.clasification_sheet = '0'
				then t.saldo_acreedor
				else 0.00
			end as pasivo,
			case 
				when (t.saldo_deudor > 0 and cta.clasification_sheet = '1') or 
					 (t.saldo_deudor > 0 and cta.clasification_sheet = '3')
				then t.saldo_deudor
				else 0.00
			end as perdinat,
			case 
				when (t.saldo_acreedor > 0 and cta.clasification_sheet = '1') or
					 (t.saldo_acreedor > 0 and cta.clasification_sheet = '3')
				then t.saldo_acreedor
				else 0.00
			end as ganannat,
			case 
				when (t.saldo_deudor > 0 and cta.clasification_sheet = '2') or
					 (t.saldo_deudor > 0 and cta.clasification_sheet = '3')
				then T.saldo_deudor
				else 0.00
			end as perdifun,
			case 
				when (t.saldo_acreedor > 0 and cta.clasification_sheet = '2') or
					 (t.saldo_acreedor > 0 and cta.clasification_sheet = '3')
				then t.saldo_acreedor
				else 0.00
			end as gananfun,
			tipo.name as rubro
		from 
		(

		select 
		distinct integral.account_id,
		coalesce(saldoini.debeini,0.00) as debeini,
		coalesce(saldoini.haberini,0.00) as haberini,
		coalesce(saldoac.debeac,0.00) as debep,
		coalesce(saldoac.haberac,0.00) as haberp,
		case when 
			coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00) > coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00)
		then
			(coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00)) - (coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00))
		else	0.00
		end as saldo_deudor,

		case when 
			  coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00) > coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00)
		then 
			 ( coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00)) - (coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00))
		else 0.00
		end as saldo_acreedor
		from vst_diariog integral 
		left join 
		-- ACA PONER LOS PARAMETROS PARA COMPAÑIA Y PERIODO INICIAL QUE SERA EL AÑO DEL PERIODO ELEGIDO ( CUATRO DIGITOS PRIMERO) CONCATENADO CON '00'
		(select diario_a.account_id,
		CASE WHEN $3 = 'pen' THEN sum(diario_a.debe) ELSE sum(coalesce(vst_diariog_me.debe_me,0)) END AS debeini,
		CASE WHEN $3 = 'pen' THEN sum(diario_a.haber) ELSE sum(coalesce(vst_diariog_me.haber_me,0)) END AS haberini
		from vst_diariog diario_a
		LEFT JOIN vst_diariog_me on vst_diariog_me.move_id = diario_a.move_id and vst_diariog_me.move_line_id = diario_a.move_line_id
		where diario_a.company_id=$2 and cast(diario_a.periodo as int) = cast(left($1,4) || '00' as int) group by diario_a.account_id)
		saldoini on saldoini.account_id=integral.account_id
		left join 
		-- ACA PONER LOS PARAMETROS PARA COMPAÑIA Y PERIODO HASTA EL CUAL SE QUIERE ,  SIN CONSIDERAR EL PERIODO INICIAL 
		(select diario_b.account_id,
		CASE WHEN $3 = 'pen' THEN sum(diario_b.debe) ELSE sum(coalesce(vst_diariog_me.debe_me,0)) END AS debeac,
		CASE WHEN $3 = 'pen' THEN sum(diario_b.haber) ELSE sum(coalesce(vst_diariog_me.haber_me,0)) END AS haberac
		from vst_diariog diario_b 
		LEFT JOIN vst_diariog_me on vst_diariog_me.move_id = diario_b.move_id and vst_diariog_me.move_line_id = diario_b.move_line_id
		where diario_b.company_id=$2 and (cast(diario_b.periodo as int) between cast(left($1,4) || '01' as int) and cast($1 as int))   and cast(diario_b.periodo as int) <> cast(left($1,4) || '00' as int) group by diario_b.account_id)
		saldoac on saldoac.account_id=integral.account_id
		-- EN ESTE WHERE VA EL PARAMETRO DE LA COMPAÑIA Y DE LOS PERIODOS INICAL SIEMPRE 00  Y FINAL PORQUE SE NECESITA EL ACUMULADO DE LAS CUENTAS 
		where company_id=$2 and (cast(periodo as int) between cast(left($1,4) || '00' as int) and cast($1 as int))
		) t
		left join account_account cta on cta.id=t.account_id                 
		left join account_type_it tipo on tipo.id=cta.account_type_it_id
		order by left(cta.code,2),cta.code;              
END; $BODY$;
-------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f2_balance(character varying,integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f2_balance(
	IN period character varying,
	IN company integer,
	IN currency character varying)
    RETURNS TABLE(mayor text, nomenclatura character varying, debe_inicial numeric, haber_inicial numeric, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
    
AS $BODY$
BEGIN

RETURN QUERY 
    
	select T.mayor,T.name,T.debe_inicial,T.haber_inicial,
		   T.debe,T.haber,T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and ag.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and ag.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun
	from(
		select
		f2r.mayor,
		ag.name,
		ag.id,
		sum(f2r.debe_inicial) as debe_inicial,
		sum(f2r.haber_inicial) as haber_inicial,
		sum(f2r.debe) as debe,
		sum(f2r.haber) as haber,
		case 
			when sum(f2r.debe) + sum(f2r.debe_inicial) > sum(f2r.haber) + sum(f2r.haber_inicial) 
			then (sum(f2r.debe) + sum(f2r.debe_inicial)) - (sum(f2r.haber) + sum(f2r.haber_inicial))
			else 0
		end as saldo_deudor,
		case
			when sum(f2r.haber) + sum(f2r.haber_inicial) > sum(f2r.debe) + sum(f2r.debe_inicial)
			then (sum(f2r.haber) + sum(f2r.haber_inicial)) - (sum(f2r.debe) + sum(f2r.debe_inicial))
			else 0
		end as saldo_acreedor
		from get_f2_register($1,$2,$3) f2r
		left join account_group ag on ag.code_prefix = f2r.mayor
    	group by f2r.mayor,ag.name,ag.id)T
	inner join account_group ag on ag.id = T.id
	order by T.mayor;
                  
END; $BODY$;

-------------------------------------------------account_htf2_report------------------------------------------------------------------