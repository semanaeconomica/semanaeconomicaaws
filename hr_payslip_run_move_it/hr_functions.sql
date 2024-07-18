---------------------------- Asiento Contable de Nomina -------------------------------------
DROP VIEW IF EXISTS payslip_run_move;
CREATE OR REPLACE VIEW payslip_run_move AS (
	select distinct
	hsr.sequence,
	hsr.id as salary_rule_id,
	hp.id as slip_id,
	hp.payslip_run_id,
	hsr.company_id,
	case 
		when ipd.value_reference is not null 
		then split_part(ipd.value_reference, ',', 2)::integer
		else null
	end as account_debit,
	case 
		when ipc.value_reference is not null 
		then split_part(ipc.value_reference, ',', 2)::integer
		else null
	end as account_credit,
	hpl.total as total
	from hr_payslip_line hpl
	inner join hr_payslip hp on hp.id = hpl.slip_id
	inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
	inner join ir_model_fields imfd on imfd.model = 'hr.salary.rule' and imfd.name = 'account_debit'
	inner join ir_model_fields imfc on imfc.model = 'hr.salary.rule' and imfc.name = 'account_credit'
	left join ir_property ipd on ipd.res_id = 'hr.salary.rule,'||hsr.id and imfd.id = ipd.fields_id
	left join ir_property ipc on ipc.res_id = 'hr.salary.rule,'||hsr.id and imfc.id = ipc.fields_id
);

CREATE OR REPLACE FUNCTION payslip_run_move(
	payslip_run integer,
	company integer)
	RETURNS TABLE(sequence integer, salary_rule_id integer, analytic_account_id integer, account_id integer, debit numeric, credit numeric) 
	LANGUAGE 'plpgsql'

	COST 100
	VOLATILE 
	ROWS 1000
AS $BODY$
BEGIN

RETURN QUERY

	select distinct
	prm.sequence,
	prm.salary_rule_id,
	0 as analytic_account_id,
	prm.account_debit as account_id,
	round(sum(prm.total)::numeric, 2) as debit,
	0::numeric as credit
	from payslip_run_move prm
	where prm.payslip_run_id = $1 and
	prm.company_id = $2 and
	prm.account_debit is not null
	group by prm.sequence, prm.salary_rule_id, prm.account_debit
	union all
	select distinct
	prm.sequence,
	prm.salary_rule_id,
	0 as analytic_account_id,
	prm.account_credit as account_id,
	0::numeric as debit,
	round(sum(prm.total)::numeric, 2) as credit
	from payslip_run_move prm
	inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
	where hsr.code not in ('COMFI','COMMIX','SEGI','A_JUB') and
	prm.payslip_run_id = $1 and
	prm.company_id = $2 and
	prm.account_credit is not null
	group by prm.sequence, prm.salary_rule_id, prm.account_credit
	union all
	select distinct
	prm.sequence,
	prm.salary_rule_id,
	0 as analytic_account_id,
	hm.account_id as account_id,
	0::numeric as debit,
	round(sum(prm.total)::numeric, 2) as credit
	from payslip_run_move prm
	inner join hr_payslip hp on hp.id = prm.slip_id
	inner join hr_contract hc on hc.id = hp.contract_id
	inner join hr_membership hm on hm.id = hc.membership_id
	inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
	where hsr.code in ('COMFI','COMMIX','SEGI','A_JUB') and
	prm.payslip_run_id = $1 and
	prm.company_id = $2 and
	hm.account_id is not null
	group by prm.sequence, prm.salary_rule_id, hm.account_id;

END;
$BODY$;

CREATE OR REPLACE FUNCTION payslip_run_analytic_move(
	payslip_run integer,
	company integer)
	RETURNS TABLE(sequence integer, salary_rule_id integer, analytic_account_id integer, account_id integer, debit numeric, credit numeric) 
	LANGUAGE 'plpgsql'

	COST 100
	VOLATILE 
	ROWS 1000
AS $BODY$
BEGIN

RETURN QUERY

	select distinct
	prm.sequence,
	prm.salary_rule_id,
	aaa.id as analytic_account_id,
	prm.account_debit as account_id,
	round(sum(prm.total * hadl.percent * 0.01)::numeric, 2) as debit,
	0::numeric as credit
	from payslip_run_move prm
	inner join hr_payslip hp on hp.id = prm.slip_id
	inner join hr_contract hc on hc.id = hp.contract_id 
	inner join hr_analytic_distribution had on had.id = hc.distribution_id
	inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
	inner join account_analytic_account aaa on aaa.id = hadl.analytic_id
	where prm.payslip_run_id = $1 and
	prm.company_id = $2 and
	prm.account_debit is not null
	group by prm.sequence, prm.salary_rule_id, aaa.id, prm.account_debit
	union all
	select distinct
	prm.sequence,
	prm.salary_rule_id,
	0 as analytic_account_id,
	prm.account_credit as account_id,
	0::numeric as debit,
	round(sum(prm.total)::numeric, 2) as credit
	from payslip_run_move prm	
	inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
	where hsr.code not in ('COMFI','COMMIX','SEGI','A_JUB') and
	prm.payslip_run_id = $1 and
	prm.company_id = $2 and
	prm.account_credit is not null
	group by prm.sequence, prm.salary_rule_id, prm.account_credit
	union all
	select distinct
	prm.sequence,
	prm.salary_rule_id,
	0 as analytic_account_id,
	hm.account_id as account_id,
	0::numeric as debit,
	round(sum(prm.total)::numeric, 2) as credit
	from payslip_run_move prm
	inner join hr_payslip hp on hp.id = prm.slip_id
	inner join hr_contract hc on hc.id = hp.contract_id
	inner join hr_membership hm on hm.id = hc.membership_id
	inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
	where hsr.code in ('COMFI','COMMIX','SEGI','A_JUB') and
	prm.payslip_run_id = $1 and
	prm.company_id = $2 and
	hm.account_id is not null
	group by prm.sequence, prm.salary_rule_id, hm.account_id;

END;
$BODY$;

---------------------------- Asiento Contable de Nomina -------------------------------------