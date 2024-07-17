library(bigrquery)
library(dplyr)
library(glue)
library(highcharter)
library(openxlsx)
library(kableExtra)
library(knitr)
library(lubridate)
library(tidyverse)
library(plotly)
library(formattable)
library(devtools)
library(purrrlyr)
library(DT)
library(hash)
library(scales)
# library(ggplot2)
library(shinyjs)
library(data.table)
library(htmltools)
library(htmlwidgets)
options(scipen=20)
source("config.R",local = knitr::knit_global())


#### Queries ####

single_stat_payments <-  "select count(distinct case when status = 'CHARGED' then a.order_id end) as successful_orders,
ROUND(safe_divide(count(distinct case when status='CHARGED' then a.order_id end),count(distinct a.order_id)) *100,2) as osr,
sum( case when status='CHARGED' then a.amount end) as processed_gmv,
ROUND(safe_divide(count(distinct case when b.Txn_count = 'Single Txn' and status = 'CHARGED' then a.order_id end),count(distinct a.order_id)) *100,2) as txn_o_ratio,
round(safe_divide(count(distinct case when a.status = 'CHARGED' and a.txn_conflict = 'CONFLICTED' then a.order_id end),count(distinct a.order_id))*100,2) as txn_conflict,
APPROX_QUANTILES(timestamp_diff(cast(txn_completed as TIMESTAMP), cast(txn_initiated as TIMESTAMP), SECOND), 1001)[OFFSET(991)] as tp90_txn
from
(select order_id, status,amount,txn_conflict,txn_completed,txn_id,txn_initiated
  from `express_checkout_v2.express_checkout*`
  where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
  and {merchant_clause}
  and date_created >='{bq_start_date} 18:30'
  and  date_created <='{bq_end_date} 18:30'
) as a
left outer join
(
  select order_id, count(distinct txn_id) as count, 'Single Txn' as Txn_count,
  from `express_checkout_v2.express_checkout*`
  where  _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
  and {merchant_clause}
  and date_created >='{bq_start_date} 18:30'
  and  date_created <='{bq_end_date} 18:30'
  group by order_id,Txn_count
  having count = 1
) as b
on a.order_id = b.order_id"

  
singlestats_refunds <- "  select
  count(distinct refund_id) as count_refunds,
  SUM( case when refund_status='SUCCESS' then refund_amount end) as refund_gmv,
  ROUND(safe_divide(count(distinct case when refund_status = 'SUCCESS' then refund_id end), count(distinct refund_id))*100,2) as refund_sr,
  count(distinct case when refund_status = 'PENDING' then refund_id end) as pending_refunds,
  count(distinct case when refund_status = 'MANUAL_REVIEW' then refund_id end) as manual_review_refunds,
  APPROX_QUANTILES(timestamp_diff(cast(refund_updated as TIMESTAMP), cast(refund_date as TIMESTAMP), SECOND), 1001)[OFFSET(991)] as tp90,
  count(DISTINCT case when txn_conflict = 'CONFLICTED' then refund_id end) as refunds_conflicted_ratio
  From
  (
    Select refund_id,refund_status,refund_amount,refund_updated,refund_date,order_id
    from `express_checkout_v2.ec_refund*`
    where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
    and {merchant_clause}
    and refund_date >='{bq_start_date} 18:30'
    and  refund_date <='{bq_end_date} 18:30') as b
  left outer join
  (
    Select order_id as ec_order_id, txn_conflict
    from `express_checkout_v2.express_checkout*`
    where _table_suffix between  '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
    and {merchant_clause}
    and date_created >='{bq_start_date} 18:30'
    and date_created <='{bq_end_date} 18:30'
  ) as a
  on a.ec_order_id = b.order_id"
# singlestats_refunds <- "select
# count(distinct refund_id) as count_refunds,
# SUM( case when refund_status='SUCCESS' then refund_amount end) as refund_gmv,
# ROUND(safe_divide(count(distinct case when refund_status = 'SUCCESS' then refund_id end), count(distinct refund_id))*100,2) as refund_sr,
# count(distinct case when refund_status = 'PENDING' then refund_id end) as pending_refunds,
# count(distinct case when refund_status = 'MANUAL_REVIEW' then refund_id end) as manual_review_refunds,
# APPROX_QUANTILES(timestamp_diff(cast(refund_updated as TIMESTAMP), cast(refund_date as TIMESTAMP), SECOND), 1001)[OFFSET(991)] as tp90,
# ROUND(safe_divide(count(DISTINCT refund_id),count(distinct order_id))*100,2) as refunds_order_ratio,
# 
# from `express_checkout_v2.ec_refund*`
# where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
# and {merchant_clause}
# and refund_date >='{bq_start_date} 18:30'
# and  refund_date <='{bq_end_date} 18:30'
# "

  singlestats_payments_historic <-  "select count(distinct case when status = 'CHARGED' then a.order_id end) as successful_orders,
  ROUND(safe_divide(count(distinct case when status='CHARGED' then a.order_id end),count(distinct a.order_id)) *100,2) as osr,
  sum( case when status='CHARGED' then a.amount end) as processed_gmv,
  ROUND(safe_divide(count(distinct case when b.Txn_count = 'Single Txn' and status = 'CHARGED' then a.order_id end),count(distinct a.order_id)) *100,2) as txn_o_ratio,
  round(safe_divide(count(distinct case when a.status = 'CHARGED' and a.txn_conflict = 'CONFLICTED' then a.order_id end),count(distinct a.order_id))*100,2) as txn_conflict,
  APPROX_QUANTILES(timestamp_diff(cast(txn_completed as TIMESTAMP), cast(txn_initiated as TIMESTAMP), SECOND), 1001)[OFFSET(991)] as tp90_txn
  from
    (select order_id, status,amount,txn_conflict,txn_completed,txn_id,txn_initiated
      from `express_checkout_v2.express_checkout*`
      where _table_suffix between '{bq_previous_start_date_suffix}' AND '{bq_previous_end_date_suffix}'
       and {merchant_clause}
      and date_created >='{bq_previous_start_date} 18:30'
      and  date_created <='{bq_previous_end_date} 18:30'
    ) as a
  left outer join
  (
    select order_id, count(distinct txn_id) as count, 'Single Txn' as Txn_count,
    from `express_checkout_v2.express_checkout*`
    where _table_suffix between '{bq_previous_start_date_suffix}' AND '{bq_previous_end_date_suffix}'
    and {merchant_clause}
    and date_created >='{bq_previous_start_date} 18:30'
    and  date_created <='{bq_previous_end_date} 18:30'
    group by order_id,Txn_count
    having count = 1
  ) as b
  on a.order_id = b.order_id"

  
  singlestats_refunds_historic <- "select
count(distinct refund_id) as count_refunds,
SUM( case when refund_status='SUCCESS' then refund_amount end) as refund_gmv,
ROUND(safe_divide(count(distinct case when refund_status = 'SUCCESS' then refund_id end), count(distinct refund_id))*100,2) as refund_sr,
count(distinct case when refund_status = 'PENDING' then refund_id end) as pending_refunds,
count(distinct case when refund_status = 'MANUAL_REVIEW' then refund_id end) as manual_review_refunds,
APPROX_QUANTILES(timestamp_diff(cast(refund_updated as TIMESTAMP), cast(refund_date as TIMESTAMP), SECOND), 1001)[OFFSET(991)] as tp90,
ROUND(safe_divide(count(DISTINCT case when txn_conflict = 'CONFLICTED' then refund_id end),count(distinct refund_id))*100,2) as refunds_conflicted_ratio
From
(
Select refund_id,refund_status,refund_amount,refund_updated,refund_date,order_id
from `express_checkout_v2.ec_refund*`
    where _table_suffix between '{bq_previous_start_date_suffix}' AND '{bq_previous_end_date_suffix}'
      and {merchant_clause}
      and refund_date >='{bq_previous_start_date} 18:30'
      and  refund_date <='{bq_previous_end_date} 18:30') as b
left outer join
(
Select order_id as ec_order_id, txn_conflict
from `express_checkout_v2.express_checkout*`
 where _table_suffix between '{bq_previous_start_date_suffix}' AND '{bq_previous_end_date_suffix}'
      and {merchant_clause}
      and date_created >='{bq_previous_start_date} 18:30'
      and  date_created <='{bq_previous_end_date} 18:30'
) as a
on a.ec_order_id = b.order_id

"
  
auth_query_2 <- 'select 
ROUND(sum(success_otp_txns) / sum(total_otp_txns) *100,2)  as otp_sr, 
ROUND(sum(success_3ds_txns) / sum(total_3ds_txns) *100,2) as threeds_sr,
sum(success_otp_txns) as s_otp_txns,sum(total_otp_txns) as t_otp_txns,
sum(success_3ds_txns) as s_3ds_txns,sum(total_3ds_txns) as t_3ds_txns
from
(select 
card_isin, card_issuer_bank_name, gateway,
count(distinct case when status = "CHARGED" then txn_id end) as success_otp_txns,
count(distinct txn_id) as total_otp_txns
FROM `express_checkout_v2.express_checkout*`
where _table_suffix between "{bq_previous_start_date_suffix}" AND "{bq_previous_end_date_suffix}"
and auth_type = "OTP"
and {merchant_clause}
group by card_isin, card_issuer_bank_name, gateway
) as OTP
LEFT JOIN
(select
card_isin, card_issuer_bank_name, gateway,
count(distinct case when status = "CHARGED" then txn_id end) as success_3ds_txns,
count(distinct txn_id) as total_3ds_txns
FROM `express_checkout_v2.express_checkout*`
where _table_suffix between "{bq_previous_start_date_suffix}" AND "{bq_previous_end_date_suffix}"
and auth_type = "THREE_DS"
and {merchant_clause}
group by card_isin, card_issuer_bank_name, gateway
)AS THREE_DS
on OTP.card_isin = THREE_DS.card_isin
where OTP.gateway = THREE_DS.gateway'

auth_query_2_juspay <- 'select 
ROUND(sum(success_otp_txns) / sum(total_otp_txns) *100,2)  as otp_sr, 
ROUND(sum(success_3ds_txns) / sum(total_3ds_txns) *100,2) as threeds_sr,
sum(success_otp_txns) as s_otp_txns,sum(total_otp_txns) as t_otp_txns,
sum(success_3ds_txns) as s_3ds_txns,sum(total_3ds_txns) as t_3ds_txns
from
(select 
card_isin, card_issuer_bank_name, gateway,
count(distinct case when status = "CHARGED" then txn_id end) as success_otp_txns,
count(distinct txn_id) as total_otp_txns
FROM `express_checkout_v2.express_checkout*`
where _table_suffix between "{bq_previous_start_date_suffix}" AND "{bq_previous_end_date_suffix}"
and auth_type = "OTP"
group by card_isin, card_issuer_bank_name, gateway
) as OTP
LEFT JOIN
(select
card_isin, card_issuer_bank_name, gateway,
count(distinct case when status = "CHARGED" then txn_id end) as success_3ds_txns,
count(distinct txn_id) as total_3ds_txns
FROM `express_checkout_v2.express_checkout*`
where _table_suffix between "{bq_previous_start_date_suffix}" AND "{bq_previous_end_date_suffix}"
and auth_type = "THREE_DS"
and {merchant_clause}
group by card_isin, card_issuer_bank_name, gateway
)AS THREE_DS
on OTP.card_isin = THREE_DS.card_isin
where OTP.gateway = THREE_DS.gateway'


gpay_query <- 'with currentdata as (
select payment_method_type as payment_type, count(distinct txn_id) as volume, "sdk" as type,
  ROUND(count(distinct case when status = "CHARGED" then txn_id end)/count(distinct txn_id)*100, 2) as SR
  FROM `express_checkout_v2.express_checkout*`
  where _table_suffix between "{bq_start_date_suffix}" AND "{bq_end_date_suffix}"
and date_created >="{bq_start_date} 18:30"
and  date_created <="{bq_end_date} 18:30"
and  gateway = "GOOGLEPAY"
and payment_method_type = "WALLET"
and {merchant_clause}
group by payment_type
),
historicdata as
(
select payment_method_type as payment_type, count(distinct txn_id) as volume, "upi" as type,
  ROUND(count(distinct case when status = "CHARGED" then txn_id end)/count(distinct txn_id)*100, 2) as SR
  FROM `express_checkout_v2.express_checkout*`
  where _table_suffix between "{bq_start_date_suffix}" AND "{bq_end_date_suffix}"
and date_created >="{bq_start_date} 18:30"
and  date_created <="{bq_end_date} 18:30"
and  payment_method_type = "UPI"
and source_object = "UPI_PAY"
and payment_source = "com.google.android.apps.nbu.paisa.user"
and {merchant_clause}
group by payment_type
)

select * from currentdata
union all
select * from historicdata'
gpay_query_2_juspay <- 'with currentdata as (
select payment_method_type as payment_type, count(distinct txn_id) as volume, "sdk" as type,
  ROUND(count(distinct case when status = "CHARGED" then txn_id end)/count(distinct txn_id)*100, 2) as SR
  FROM `express_checkout_v2.express_checkout*`
  where _table_suffix between "{bq_start_date_suffix}" AND "{bq_end_date_suffix}"
and date_created >="{bq_start_date} 18:30"
and  date_created <="{bq_end_date} 18:30"
and  gateway = "GOOGLEPAY"
and payment_method_type = "WALLET"
group by payment_type
),
historicdata as
(
select payment_method_type as payment_type, count(distinct txn_id) as volume, "upi" as type,
  ROUND(count(distinct case when status = "CHARGED" then txn_id end)/count(distinct txn_id)*100, 2) as SR
  FROM `express_checkout_v2.express_checkout*`
  where _table_suffix between "{bq_start_date_suffix}" AND "{bq_end_date_suffix}"
and date_created >="{bq_start_date} 18:30"
and  date_created <="{bq_end_date} 18:30"
and  payment_method_type = "UPI"
and source_object = "UPI_PAY"
and payment_source = "com.google.android.apps.nbu.paisa.user"
and {merchant_clause}
group by payment_type
)

select * from currentdata
union all
select * from historicdata'


# 
# phonepe_table <- glue("select merchant_id,
# count(distinct CASE WHEN  payment_method = 'PHONEPE' and payment_method_type = 'WALLET' then  txn_id end) as sdk_volume,
# ROUND(safe_divide(
#   count(distinct CASE WHEN  payment_method = 'PHONEPE' and payment_method_type = 'WALLET' and status = 'CHARGED' then txn_id end)*100,
#   count(distinct CASE WHEN  payment_method = 'PHONEPE' and payment_method_type = 'WALLET' then  txn_id end)), 2) as sdk_SR,
# count(distinct CASE WHEN  payment_method = 'UPI' and source_object = 'UPI_PAY' and payment_source ='com.phonepe.app' then  txn_id end) as upi_volume,
# ROUND(safe_divide(
#   count(distinct CASE WHEN payment_method = 'UPI' and source_object = 'UPI_PAY' and payment_source = 'com.phonepe.app' and status ='CHARGED' then txn_id end)*100,
#   count(distinct case when payment_method = 'UPI' and source_object = 'UPI_PAY' and payment_source = 'com.phonepe.app' then  txn_id end)), 2) as upi_sr
# FROM `express_checkout_v2.express_checkout*`
# where _table_suffix between '20210601' AND '20210630'
# and merchant_id = ''
# group by merchant_id")



vies_query <- "select 
sum(repeat_count) as repeat_txns,
ROUND(ieee_divide(sum(repeat_success_count)*100,sum(repeat_count)),2) as repeat_sr,
sum(txns_count) as threeds_txns,
ROUND(ieee_divide(sum(succ_count)*100,sum(txns_count)),2) as threeds_sr
from
(select card_isin,
count(distinct case when JSON_EXTRACT_SCALAR(gateway_auth_req_params, '$.flow') = 'VIES_REPEAT' then txn_id end) as repeat_count,
count(distinct case when JSON_EXTRACT_SCALAR(gateway_auth_req_params, '$.flow') = 'VIES_REPEAT' and status = 'CHARGED' then txn_id end) as repeat_success_count,
ROUND(ieee_divide(count(distinct case when JSON_EXTRACT_SCALAR(gateway_auth_req_params, '$.flow') = 'VIES_REPEAT' and  JSON_EXTRACT_SCALAR(gateway_auth_req_params, '$.flowStatus') ='SUCCESS' then txn_id end),count(distinct case when JSON_EXTRACT_SCALAR(gateway_auth_req_params, '$.flow') = 'VIES_REPEAT' then txn_id end))*100,2) as repeat_succ_rate
from `express_checkout_v2.express_checkout*`
where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
and date_created >='{bq_start_date} 18:30'
and  date_created <='{bq_end_date} 18:30'
and {merchant_clause}
group by card_isin) as a
LEFT OUTER JOIN (
    select card_isin,
    count(distinct  txn_id) as txns_count,
    count(distinct case when status='CHARGED' then txn_id end) as succ_count
    from `express_checkout_v2.express_checkout*`
    where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
    and auth_type = 'THREE_DS'
    and {merchant_clause}
and date_created >='{bq_start_date} 18:30'
and  date_created <='{bq_end_date} 18:30'
group by card_isin
)as b
on a.card_isin = b.card_isin"



vies_juspay_query <- "select 
sum(repeat_count) as repeat_txns,
ROUND(ieee_divide(sum(repeat_success_count)*100,sum(repeat_count)),2) as repeat_sr,
sum(txns_count) as threeds_txns,
ROUND(ieee_divide(sum(succ_count)*100,sum(txns_count)),2) as threeds_sr
from
(select card_isin,
count(distinct case when JSON_EXTRACT_SCALAR(gateway_auth_req_params, '$.flow') = 'VIES_REPEAT' then txn_id end) as repeat_count,
count(distinct case when JSON_EXTRACT_SCALAR(gateway_auth_req_params, '$.flow') = 'VIES_REPEAT' and status = 'CHARGED' then txn_id end) as repeat_success_count,
ROUND(ieee_divide(count(distinct case when JSON_EXTRACT_SCALAR(gateway_auth_req_params, '$.flow') = 'VIES_REPEAT' and  JSON_EXTRACT_SCALAR(gateway_auth_req_params, '$.flowStatus') ='SUCCESS' then txn_id end),count(distinct case when JSON_EXTRACT_SCALAR(gateway_auth_req_params, '$.flow') = 'VIES_REPEAT' then txn_id end))*100,2) as repeat_succ_rate
from `express_checkout_v2.express_checkout*`
where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
and date_created >='{bq_start_date} 18:30'
and  date_created <='{bq_end_date} 18:30'
group by card_isin) as a
LEFT OUTER JOIN (
    select card_isin,
    count(distinct  txn_id) as txns_count,
    count(distinct case when status='CHARGED' then txn_id end) as succ_count
    from `express_checkout_v2.express_checkout*`
    where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
    and auth_type = 'THREE_DS'
and date_created >='{bq_start_date} 18:30'
and  date_created <='{bq_end_date} 18:30'
group by card_isin
)as b
on a.card_isin = b.card_isin"




vol_sr_pmt_query <- "select payment_method_type,count(distinct order_id) as total_orders,
ROUND(count(distinct case when status='CHARGED' then order_id end)/count(distinct order_id) *100,2) as osr,
from `express_checkout_v2.express_checkout*`
where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
and date_created >='{bq_start_date} 18:30'
and  date_created <='{bq_end_date} 18:30'
and {merchant_clause}
group by payment_method_type
"

vol_sr_pg_query <- "select gateway,count(distinct order_id) as total_orders,
ROUND(count(distinct case when status='CHARGED' then order_id end)/count(distinct order_id) *100,2) as osr,
from `express_checkout_v2.express_checkout*`
where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
and date_created >='{bq_start_date} 18:30'
and date_created <='{bq_end_date} 18:30'
and {merchant_clause}
group by gateway
"


reorder_query <- "select payment_method_type as payment_type,
count(distinct txn_id) as volume,
ROUND(count(distinct case when status = 'CHARGED' then txn_id end)/count(distinct txn_id)*100,2) as SR
FROM `express_checkout_v2.express_checkout*`
where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
and date_created >='{bq_start_date} 18:30'
and  date_created <='{bq_end_date} 18:30'
and {merchant_clause}
group by payment_type
order by volume desc,SR DESC"

#####################################table is not there
otp_query <- "SELECT ec_merchant_id, ec_card_issuer_bank_name, count(distinct session_id) as volume,    
count(distinct CASE WHEN auth_method='otp' THEN SESSION_ID END) AS auth_method_otp,
count(distinct CASE WHEN auth_method='otp' AND otp_detected='T' THEN SESSION_ID END) AS otp_detected,
count(distinct CASE WHEN auth_method='otp' AND otp_detected='T' AND otp_populated='T' THEN SESSION_ID END) AS otp_populated,
count(distinct CASE WHEN auth_method='otp' AND otp_detected='T' AND otp_populated='T' AND
                     (approve_otp='T' OR otp_auto_submitted='T') THEN SESSION_ID END) AS approve_auto_submit,
count(distinct CASE WHEN auth_method='otp' AND otp_detected='T' AND otp_populated='T'
                     AND (approve_otp='T' OR otp_auto_submitted='T')  AND authentication_status='Y' THEN SESSION_ID END) AS authentication_success,
count(distinct case when auth_method = 'otp' and (authentication_status='Y' or status = 'CHARGED') and (otp_auto_submitted = 'T' or approve_otp = 'T') then session_id end) as ASR,
FROM
`godel_logs_v2.godel_session202106*`
 where _table_suffix between '01' AND '30'
    and auth_method = 'otp'
AND ec_card_type in ('CREDIT','DEBIT','NB')
and {merchant_clause}
and is_godel = TRUE
GROUP BY  ec_merchant_id,  ec_card_issuer_bank_name"



sr_query <- glue(
  sep = "",
  "SELECT payment_method_type as payment_type, card_type,
    card_isin as bin,
    (case when payment_method_type in ('CARD') then payment_method
when payment_method_type in ('UPI') then source_object 
when payment_method_type in ('NB') then card_issuer_bank_name end) as payment_method,
          SUBSTR(CAST((DATETIME(TIMESTAMP(date_created), '+05:30')) AS STRING), 0, 10) AS date,
    gateway,
    source_object,
    status,
    card_issuer_bank_name as Bank,
    card_switch_provider as card_brand,
    payment_source,emi, auth_type,
  count(distinct txn_id) AS txn_count,
  count(distinct order_id) AS order_count,
  count(distinct CASE WHEN status = 'CHARGED'
  THEN txn_id END) AS txn_success_count,
  count(distinct CASE WHEN status = 'CHARGED'
  THEN order_id END) AS order_success_count,
  (
case when merchant_id in ('",
  paste(ind_no_merch_list,
        collapse = "','", sep = ""),
  "')  then 'Industry'
  when merchant_id in (",
  merchant_filter_custom,
  ") then ",
  merchant_filter_custom,
  " end ) as merchants,
FROM `express_checkout_v2.express_checkout*`
 where _table_suffix between '{bq_start_date_suffix}' and '{bq_end_date_suffix}'
    and merchant_id IN ('",
  paste(all_list, collapse = "','", sep = ""),
  "') 
    and date_created >= '{bq_start_date} 18:30'
and date_created <'{bq_end_date} 18:30'
GROUP BY payment_type,bin,gateway,source_object,merchants,card_type,
status,Bank,payment_method,
card_brand,payment_source,date,emi, auth_type"
)

dim5p_query <- "select
  gateway,payment_method_type,payment_method, auth_type,txn_object_type,volume, SR
from
   ( select
   merchant_id,gateway,payment_method_type,(case when payment_method in ('UPI') then source_object else payment_method end) as payment_method, auth_type,
   txn_object_type,
   COUNT(DISTINCT txn_id) as volume,
    round(ieee_divide( COUNT(DISTINCT case when status = 'CHARGED' then txn_id end)*100, COUNT(DISTINCT  txn_id)),2)  as SR,
    FROM `express_checkout_v2.express_checkout*`
    where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
    and date_created >='{bq_start_date} 18:30'
    and  date_created <='{bq_end_date} 18:30'
    and {merchant_clause}
    and merchant_id not in ('jiosaavn','gaana','instamojo_wallet')
    and gateway is not null
    group by   merchant_id,gateway,payment_method_type,payment_method, auth_type,txn_object_type)
        where SR between 0 and 5
        group by gateway,payment_method_type,payment_method, auth_type,txn_object_type,volume, SR
        having volume >100
        ORDER BY volume desc"

mandate_vs_normal <- "select 
ROUND(sum(success_Order_txns) / sum(total_order_txns) *100,2)  as order_sr, 
ROUND(sum(success_Mandate_txns) / sum(total_Mandate_txns) *100,2) as mandate_sr,
sum(total_order_txns) as t_order_txns,
sum(total_Mandate_txns) as t_mandate_txns
from
(select 
  card_isin, card_issuer_bank_name, gateway,
  count(distinct case when status = 'CHARGED' then txn_id end) as success_Order_txns,
  count(distinct txn_id) as total_order_txns
  FROM `express_checkout_v2.express_checkout*`
  where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
    and date_created >='{bq_start_date} 18:30'
    and  date_created <='{bq_end_date} 18:30'
  and order_type = 'ORDER_PAYMENT'
  and payment_method_type = 'CARD'
  and merchant_id = 'icicipru'
  group by card_isin, card_issuer_bank_name, gateway
) as OTP
LEFT JOIN
(select
  card_isin, card_issuer_bank_name, gateway,
  count(distinct case when status = 'CHARGED' then txn_id end) as success_Mandate_txns,
  count(distinct txn_id) as total_Mandate_txns
  FROM `express_checkout_v2.express_checkout*`
  where _table_suffix between '{bq_start_date_suffix}' AND '{bq_end_date_suffix}'
    and date_created >='{bq_start_date} 18:30'
    and  date_created <='{bq_end_date} 18:30'
  and source_object = 'MANDATE'
  and merchant_id = 'icicipru'
  group by card_isin, card_issuer_bank_name, gateway
)AS mandate
on OTP.card_isin = mandate.card_isin
"

# execute_query <- function(query) {
#   df <- bq_project_query(
#     project,
#     query = query,
#     use_legacy_sql = FALSE,
#     max_pages = Inf,
#     location = "asia-south1",
#     destination_table = NULL,
#     default_dataset = NULL
#   ) %>% bq_table_download(max_results = Inf, start_index = 0) %>% as_tibble() 
#   write.csv(df, "report")
#   df
# }

#######query function #######3
execute_query <- function(query) {
  bq_project_query(
    project,
    query = query,
    use_legacy_sql = FALSE,
    max_pages = Inf,
    location = "asia-south1",
    destination_table = NULL,
    default_dataset = NULL
  ) %>% bq_table_download(max_results = Inf, start_index = 0) %>% as_tibble()
}

####executing queries and storing to data frame ####

# 
# singlestat_data <- single_stat_payments %>%
#   glue() %>%
#   execute_query()

singlestat_data <- single_stat_payments %>%
  glue() %>%
  execute_query()
# singlestat_data <- read.csv("singlestats.csv")
singlestat_data_refunds <- singlestats_refunds %>%
  glue() %>%
  execute_query()
# singlestat_data_refunds <- read.csv("refunds_currrent.csv")
singlestat_data_historic <- singlestats_payments_historic %>%
  glue() %>%
  execute_query()
# singlestat_data_historic <-  read.csv("historic.csv")

singlestats_refunds_historic <- singlestats_refunds_historic %>%
  glue() %>%
  execute_query()
# singlestats_refunds_historic <- read.csv("refunds_historic.csv")
# singlestat_data_historic <- read.csv("./pay_refund_historic.csv")



auth_table_2 <- auth_query_2 %>%
  glue() %>%
  execute_query
# auth_table_2 <- read.csv( "com.swiggy_auth_type_1.csv")

auth_table_2_juspay <- data.frame()

if(all(is.na(auth_table_2))){
  auth_table_2 <- data.frame()
}else{
auth_table_2[is.na(auth_table_2)] <- 0
if(auth_table_2$t_otp_txns < 1 ){

  auth_table_2 <- data.frame()
  auth_table_2_juspay <- auth_query_2_juspay %>%
    glue() %>%
    execute_query
  # auth_table_2_juspay <- read.csv("auth_table_2.csv")
  auth_table_2_juspay[is.na(auth_table_2_juspay)] <- 0
  }
  
}

if(nrow(auth_table_2) == 0){
  auth_table_2_juspay <- auth_query_2_juspay %>%
    glue() %>%
    execute_query
  # auth_table_2_juspay <- read.csv("auth_table_2.csv")
  auth_table_2_juspay[is.na(auth_table_2_juspay)] <- 0
  
}




 
gpay_table <- gpay_query %>%
  glue() %>%
  execute_query()
# phonepe_table <- phonepe_table %>%
#   glue() %>%
#   execute_query()
# gpay_table <- read_csv("gpay_table1.csv")
# phonepe_table <- read_csv("phonepe_tbl - Sheet1.csv")
gpay_table_juspay <- data.frame()

if(all(is.na(gpay_table))){
  gpay_table <- data.frame()
}else{
  gpay_table[is.na(gpay_table)] <- 0
  if(nrow(gpay_table) == 1 ){
    gpay_table <- data.frame()
    # gpay_table_juspay <- gpay_query_2_juspay %>%
    #   glue() %>%
    #   execute_query
    gpay_table_juspay <- read_csv("olacabs_juspay_all_gpay.csv")
    gpay_table_juspay[is.na(gpay_table_juspay)] <- 0
    if(nrow(gpay_table_juspay) == 1){
      gpay_table_juspay <- data.frame()
    }
  }
}

if(nrow(gpay_table) == 0){
  gpay_table_juspay <- gpay_query_2_juspay %>%
    glue() %>%
    execute_query
  # gpay_table_juspay <- read_csv("olacabs_juspay_all_gpay.csv")
  gpay_table_juspay[is.na(gpay_table_juspay)] <- 0
  if(nrow(gpay_table_juspay) == 1){
    gpay_table_juspay <- data.frame()
  }
  
}




#

vol_sr_pmt_table <- vol_sr_pmt_query %>%
  glue() %>%
  execute_query()
# write.csv(vol_sr_pmt_table,"sr_pmt.csv")
# vol_sr_pmt_table <- read.csv("vol_sr_pmt_query.csv")
vol_sr_pmt_table <- vol_sr_pmt_table %>% drop_na()

vol_sr_pg_table <- vol_sr_pg_query %>%
  glue() %>%
  execute_query()
# write.csv(vol_sr_pg_table,"sr_pg.csv")
# vol_sr_pg_table <- read.csv("vol_sr_pg_query.csv")
vol_sr_pg_table <- vol_sr_pg_table %>% drop_na()


reorder_table <- reorder_query %>%
  glue() %>%
  execute_query()
# reorder_table <- read.csv("reorder_.csv")
colnames(reorder_table) <- c("Payment Method Type",
                         "Volume",
                         "Success Rate")
if(nrow(reorder_table) == 0){
  heading_text_value_reord <- ""
}else{
  reorder_text <- paste("You can Re-Order your Payment Methods in the following order to increase user conversion :: ◉",
                        paste(na.omit( reorder_table$`Payment Method Type`), collapse = " ◉ "))
}

mandate_vs_normal <- mandate_vs_normal  %>%  glue() %>%  execute_query()

vies_table <- vies_query %>%
  glue() %>%
  execute_query()
# vies_table <- read.csv("vies_query.csv")
vies_table[is.na(vies_table)] <- 0
vies_table_juspay <- data.frame()

if(vies_table$repeat_txns == 0){
  vies_table <- data.frame()
  vies_table_juspay <- vies_juspay_query %>%
    glue() %>%
    execute_query()
  # vies_table_juspay <- read_csv("vies_juspay.csv")
  vies_table_juspay[is.na(vies_table_juspay)] <- 0
  
}



# 
otp_table <- otp_query %>%
  glue() %>%
  execute_query()

# otp_table <- read.csv("otp_swigggy.csv")

sr_results <- sr_query %>%
  execute_query()
# sr_results <- read.csv("sr.csv")
sr_results = sr_results %>% replace_na( list( payment_type = "Null",
                                              bin = "Null",
                                              Bank = "Null",
                                              source_object = "Null", 
                                              gateway = "Null",
                                              merchants = "Null",
                                              status = "Null",
                                              card_brand = "Null",
                                              payment_source = "Null", 
                                              payment_method = "Null"))

###### Payments and Refunds Data Processing ############

singlestat_data[is.na(singlestat_data)] <- 0
singlestat_data_refunds[is.na(singlestat_data_refunds)] <- 0
singlestats_payments_historic[is.na(singlestat_data_historic)] <- 0
singlestats_refunds_historic[is.na(singlestats_refunds_historic)] <- 0


payments_table <- singlestat_data %>% select(successful_orders, osr, txn_o_ratio, txn_conflict, tp90_txn, processed_gmv)
# print(payments_table)
refunds_table <- singlestat_data_refunds %>% select(count_refunds,refund_sr, pending_refunds, manual_review_refunds, tp90, refund_gmv,refunds_conflicted_ratio)
payments_table$net_gmv <- payments_table$processed_gmv - refunds_table$refund_gmv

payments_table_historic <- singlestat_data_historic %>% select(successful_orders, osr, txn_o_ratio, txn_conflict, tp90_txn, processed_gmv)
refunds_table_historic <- singlestats_refunds_historic %>% select(count_refunds,refund_sr, pending_refunds, manual_review_refunds, tp90, refund_gmv,refunds_conflicted_ratio)
payments_table_historic$net_gmv <- payments_table_historic$processed_gmv - refunds_table_historic$refund_gmv
# print(payments_table_historic)
delta_payment <- round(payments_table,2) - round(payments_table_historic,2)
payment_vector_historic <- as.numeric(payments_table_historic[1,])
payment_vector <- as.numeric(payments_table[1,])

delta_payment_vector <- as.numeric(delta_payment[1,])
delta_payment_color <- c()
for (i in 1:length(delta_payment_vector)) {
  if(delta_payment_vector[i] >= 0){
    delta_payment_color[i] <- "green"
  }else{
    delta_payment_color[i] <- "red"
  }
}

delta_payment_percent_vector <- abs(delta_payment_vector/payment_vector_historic * 100)
delta_payment_percent_vector[5] <- delta_payment_vector[5]/payment_vector_historic[5] * 100
delta_payment_old_latency <- (100 * as.numeric(payment_vector[5]))/(100 + delta_payment_percent_vector[5])
delta_payment_percent_vector[!is.finite(delta_payment_percent_vector)] <- 0
# delta_payment_percent_vector[1] <- abs(delta_payment_vector[1])
delta_payment_percent_vector[2] <- abs(delta_payment_vector[2])
delta_payment_percent_vector[3] <- abs(delta_payment_vector[3])
delta_payment_percent_vector[4] <- abs(delta_payment_vector[4])
delta_payment_final_vector <- vector(mode="double", length=7)
delta_payment_final_vector[1:4] <- paste(round(delta_payment_percent_vector[1:4],2),"%",sep = "")
delta_payment_final_vector[5] <- as.numeric(payment_vector[5]) - delta_payment_old_latency
delta_payment_final_vector[5] <- paste(seconds_to_period(round(abs(as.numeric(delta_payment_final_vector[5])),0)))
delta_payment_final_vector[6] <-  paste(round(delta_payment_percent_vector[6],2),"%",sep = "")
# delta_payment_final_vector[1:4] <- paste(round(delta_payment_percent_vector[1:5],2),"%",sep = "")
delta_payment_final_vector[7] <- paste(round(abs(delta_payment_percent_vector[7]),2),"%",sep = "")

payment_vector[1] <- shortNum(payment_vector[1])
payment_vector[2] <- paste(payment_vector[2],"%",sep = "")
payment_vector[3] <- paste(payment_vector[3],"%",sep = "")
payment_vector[4] <- paste(payment_vector[4],"%",sep = "")
payment_vector[5] <- paste(seconds_to_period(payment_vector[5]))
payment_vector[6] <- shortNum(as.numeric(payment_vector[6]))
payment_vector[7] <- shortNum(as.numeric(payment_vector[7]))


delta_refund <- refunds_table - refunds_table_historic
refund_vector_historic <- as.numeric(refunds_table_historic[1,])
refund_vector <- as.numeric(refunds_table[1,])
delta_refund_vector <- as.numeric(delta_refund[1,])
delta_refund_color <- c()
refund_reverse_vector <-   c("Pending Refunds",
                             "Conflicted Refunds",
                             "99th % Turn Around Time",
                             "Manual Review Refunds")
payments_reverse_vector <- c("Delayed Success Order Rate", "99th % Turn Around Time")
# for (i in 1:length(delta_refund_vector)) {
#   if (labels_refund[i] %in% refund_reverse_vector) {
#     if(delta_refund_vector[i] < 0){
#       delta_refund_color[i] <- "green"
#     }else{
#       delta_refund_color[i] <- "red"
#     }
#   }
#   else{
#     if(delta_refund_vector[i] >= 0){
#       delta_refund_color[i] <- "green"
#     }else{
#       delta_refund_color[i] <- "red"
#     }
# }
# }
delta_refund_percent_vector <- abs(delta_refund_vector/refund_vector_historic * 100)
delta_refund_percent_vector[5] <- delta_refund_vector[5]/refund_vector_historic[5] * 100
delta_refund_old_latency <- (100 * as.numeric(refund_vector[5]))/(100 + delta_refund_percent_vector[5])
delta_refund_percent_vector[!is.finite(delta_refund_percent_vector)] <- 0
delta_refund_percent_vector[2] <- abs(delta_refund_vector[2])
delta_refund_final_vector <- vector(mode="double", length=5)
delta_refund_final_vector[1:4] <- round(delta_refund_percent_vector[1:4],2)
delta_refund_final_vector[1:4] <- paste(delta_refund_final_vector[1:4],"%",sep = "")
# delta_refund_final_vector[5] <- paste(delta_refund_final_vector[5],"S",sep = "")
delta_refund_final_vector[5] <- as.numeric(refund_vector[5]) - as.numeric(delta_refund_old_latency)
delta_refund_final_vector[5] <- paste(seconds_to_period(round(abs(as.numeric(delta_refund_final_vector[5])),0)))
delta_refund_final_vector[6] <- paste(round(delta_refund_percent_vector[6],2),"%",sep = "")
delta_refund_final_vector[7] <-  paste(round(delta_refund_percent_vector[7],2),"%",sep = "")

refund_vector[1] <- shortNum(refund_vector[1])
refund_vector[3] <- shortNum(as.numeric(refund_vector[3]))
refund_vector[4] <- shortNum(refund_vector[4])
refund_vector[2] <- paste(refund_vector[2],"%",sep = "")
# refund_vector[5] <- paste(refund_vector[5],"S",sep = "")
refund_vector[5] <- paste(seconds_to_period(refund_vector[5]))
refund_vector[6] <- shortNum(as.numeric(refund_vector[6]))
refund_vector[7] <- shortNum(as.numeric(refund_vector[7]))
#### OTP data processing ####
otp_summarized <-
  otp_table %>% group_by(ec_merchant_id) %>% summarise(
    Volume = sum(volume),
    `OTP Detected` = sum(otp_detected),
    `OTP Populated` = sum(otp_populated),
    `Approve Auto Submit` = sum(approve_auto_submit),
    `Authentication Success` = sum(ASR)
  ) %>% na.omit()

otp_affected <-
  otp_table %>% filter(
    volume > 50 & (
      otp_detected == 0 |
        otp_populated == 0 |
        approve_auto_submit ==
        0 |
        authentication_success == 0
    )
  ) %>% rename(
    "OTP Detected" = otp_detected,
    "OTP Populated" = otp_populated,
    "Approve Auto Submit" = approve_auto_submit,
    "MID" = ec_merchant_id,
    "Authentication Success" = authentication_success,
    "Payment Type" = ec_card_issuer_bank_name,
    "Auth Method OTP" = auth_method_otp,
    "Volume" = volume
  )

#### PG Config Optimization ####

credit_data_all <-
  alterable_dimension(sr_results, payment_meth = c("CREDIT","DEBIT"), bin, card_type, Bank)
cred_col_names = c("bin", 'card_type', 'Bank', (sort(
  unique(credit_data_all$gateway)
)), "Potential Imp")
credit_low_data <-
  credit_data_all %>% filter(sr <= 5.00, vol > 50)
credit_date_data_all <-
  alterable_dimension(sr_results, payment_meth = c("CREDIT","DEBIT"), bin, date, card_type, Bank)
credit_data_all1 = credit_date_data_all%>% unite(col = "bin_date_card_type_Bank",
                                                 bin, date, card_type, Bank,
                                                 sep = "--")
credit_date_data_all = credit_date_data_all %>%
  filter(bin %in% credit_low_data$bin,
         gateway %in% credit_low_data$gateway) %>% filter(sr <= 5.00, vol > 50)
credit_data  <-
  credit_data_all1 [!is.na(credit_data_all1$gateway), ] %>%
  gather(variable, value, -(bin_date_card_type_Bank:gateway)) %>%
  unite(temp, gateway, variable) %>%
  spread(temp, value)

credit_data_cb_all <-
  alterable_dimension(sr_results, payment_meth = c("CREDIT","DEBIT"),  bin, card_type, Bank, card_brand)
cred_col_names_cb = c( "card_brand",(sort(      #"card_brand","card_type",
  unique(credit_data_cb_all$gateway)
)), "Potential Improvement Rate")
credit_low_data_cb <-
  credit_data_cb_all %>% filter(sr <= 5.00, vol > 50)  
credit_date_data_cb_all <-
  alterable_dimension(sr_results,payment_meth = c("CREDIT","DEBIT"), card_brand, card_type, bin, Bank) 
credit_data_cb_all1 = credit_date_data_cb_all%>% unite(col = "card_brand_card_type_bin_Bank",
                                                       card_brand, card_type, bin, Bank, sep = "--")
credit_date_data_cb_all = credit_date_data_cb_all %>%
  filter(card_brand %in% credit_low_data_cb$card_brand,
         gateway %in% credit_low_data_cb$gateway,
         bin %in% credit_low_data_cb$bin,
         card_type %in% credit_low_data_cb$card_type) %>% filter(sr <= 5.00, vol > 50)
credit_data_cb  <-
  credit_data_cb_all1 [!is.na(credit_data_cb_all1$gateway), ] %>%
  gather(variable, value, -(card_brand_card_type_bin_Bank:gateway)) %>%
  unite(temp, gateway, variable) %>%
  spread(temp, value)


cre_bins_cb = c()
if (nrow(credit_data_cb) > 0) {
  credit_alt_cb = potential_improvement_data(credit_data_cb)
  if (nrow(credit_alt_cb) > 0) {
    cre_bins_cb =  credit_alt_cb  %>% 
      separate(card_brand_card_type_bin_Bank, into = c("card_brand","card_type","bin", "Bank"), sep = "--") 
    cre_bins_cb = unique(cre_bins_cb[, 1])
    credit_alt_cb <-
      data.frame(credit_alt_cb[,-1],
                 row.names = credit_alt_cb[, 1])
    tst <- credit_alt_cb
    sr_indexes <- seq(1, length(tst) - 1, 2)
    vol_indexes <- seq(2, length(tst) - 1, 2)
    gateway_names <- names(tst[,sr_indexes])
    tst1 <- tst
    tst1$`Potential Gateway` <- apply(tst1[,sr_indexes], 1, function(x){paste(gateway_names[x == max(x)]," - ",max(x))})
    tst1$`Current Gateway` <- apply(tst1[,sr_indexes], 1, function(x){paste(gateway_names[x == min(x)]," - ",min(x))})
    tst1$overall_vol <- apply(tst1[,vol_indexes], 1, sum)
    tst1$`Potential Improvement Volume` <- mapply(function(x, y) floor((y*x)/100), tst1$potential_imp, tst1$overall_vol)
    
    credit_alt_cb = shortening_df(credit_alt_cb,
                                  cred_col_names_cb,
                                  "card_brand_card_type_bin_Bank") %>%
      separate(card_brand_card_type_bin_Bank, into = c("card_brand","card_type","bin", "Bank"), sep = "--")
    credit_alt_cb = (credit_alt_cb[, c(2, 1, 3:length(credit_alt_cb))])
    credit_alt_cb_merge <-  cbind(credit_alt_cb,tst1[,c(vol_indexes,8,9,10,11)]) 
    credit_alt_cb_merge <- credit_alt_cb_merge %>% filter(BILLDESK_vol > 30 & PAYTM_vol > 30 & PAYU_vol > 30) %>% arrange(desc(overall_vol)) %>% head(10)
    
    credit_alt_datatable <- credit_alt_cb_merge %>% select(card_type,card_brand,bin,Bank,`Current Gateway`,`Potential Gateway`,`Potential Improvement Rate`,`Potential Improvement Volume`)
    
  } else{
    credit_alt_datatable = NULL
  }
} else{
  credit_alt_datatable = NULL
}  
#  wallet plc
wallet_redirect_data_all <-
  sr_results %>% filter(
    merchants != "Industry",
    payment_type == "WALLET",
    source_object %in% c("REDIRECT_WALLET_DEBIT","DIRECT_WALLET_DEBIT")
  ) %>%
  group_by_function(Bank, gateway)

wal_re_col_names = c("Bank",
                     (sort(
                       unique(wallet_redirect_data_all$gateway)
                     )), "Potential Imp")

wallet_redirect_low_data = wallet_redirect_data_all %>% filter(sr <= 5.00, vol > 100)

wallet_redirect_date_data_all <-
  sr_results %>% filter(
    merchants != "Industry",
    payment_type == "WALLET",
    source_object %in% c("REDIRECT_WALLET_DEBIT","DIRECT_WALLET_DEBIT")
  ) %>%
  group_by_function(Bank, gateway)
wallet_redirect_data_all1 = wallet_redirect_date_data_all%>% unite(col = "Bank",
                                                                   Bank,
                                                                   sep = "--")
wallet_redirect_date_data_all= wallet_redirect_date_data_all %>%
  filter(
    Bank %in% wallet_redirect_low_data$Bank,
    gateway %in% wallet_redirect_low_data$gateway
  ) %>% filter(sr <= 5.00, vol > 100)

wallet_redirect_data <-
  wallet_redirect_data_all1[!is.na(wallet_redirect_data_all1$gateway), ] %>%
  gather(variable, value, -(Bank:gateway)) %>%
  unite(temp, gateway, variable) %>%
  spread(temp, value)



# wallet_redirect_alt is defined here
re_wallets = c()
if (nrow(wallet_redirect_data) > 0) {
  wallet_redirect_alt = potential_improvement_data(wallet_redirect_data)
  if (nrow(wallet_redirect_alt) > 0) {
    re_wallets = wallet_redirect_alt %>%
      separate(Bank, into = c("Bank"), sep = "--")
    re_wallets = unique(re_wallets[,1])
    wallet_redirect_alt = data.frame(wallet_redirect_alt[,-1],
                                     row.names = wallet_redirect_alt[, 1])
    wallet_redirect_alt = shortening_df(wallet_redirect_alt,
                                        wal_re_col_names,
                                        "Bank") %>%
      separate(Bank, into = c("Bank"), sep = "--")
    wallet_redirect_alt = (wallet_redirect_alt[, c(2, 1, 3:length(wallet_redirect_alt))])
    
  } else{
    wallet_redirect_alt = NULL
  }
}else{
  wallet_redirect_alt = NULL
}

card_emi_data <- alterable_dimension(sr_results, payment_meth = c("CREDIT","DEBIT"), emi) %>% select(-c(suc)) %>%
  filter(emi >0) %>% mutate(emi = ifelse(emi == 0, "NO", "Yes"))

card_auth_data <- alterable_dimension(sr_results, payment_meth = c("CREDIT","DEBIT"), auth_type) %>% select(-c(suc)) %>%
  filter(sr < 5.00, vol > 50)



nb_data_all = alterable_dimension(sr_results, payment_meth = "NB", Bank)
nb_col_names = c("Bank", (sort(
  unique(nb_data_all$gateway)
)), "Potential Imp")

nb_low_data <-
  nb_data_all %>% filter(sr <= 5.00, vol > 50)

nb_date_data_all <-
  alterable_dimension(sr_results, payment_meth = "NB", Bank, date)

nb_data_all1 = nb_date_data_all%>% unite(col = "Bank_date",
                                         Bank, date,
                                         sep = "--")
nb_date_data_all = nb_date_data_all %>%
  filter(Bank %in% nb_low_data$Bank,
         gateway %in% nb_low_data$gateway) %>%
  filter(sr <= 5.00, vol > 50)
if(nrow(nb_date_data_all) < 1)
{
  nb_date_data_all <- NULL
}
nb_data <-
  nb_data_all1[!is.na(nb_data_all1$gateway), ] %>%
  gather(variable, value, -(Bank_date:gateway)) %>%
  unite(temp, gateway, variable) %>%
  spread(temp, value)


wallet_redirect_data_all <-
  sr_results %>% filter(
    merchants != "Industry",
    payment_type == "WALLET",
    source_object == "REDIRECT_WALLET_DEBIT"
  ) %>%
  group_by_function(Bank, gateway)
wal_re_col_names = c("Bank",
                     (sort(
                       unique(wallet_redirect_data_all$gateway)
                     )), "Potential Imp")
wallet_redirect_low_data = wallet_redirect_data_all %>% filter(sr <= 5.00, vol > 100)

wallet_redirect_date_data_all <-
  sr_results %>% filter(
    merchants != "Industry",
    payment_type == "WALLET",
    source_object == "REDIRECT_WALLET_DEBIT"
  ) %>%
  group_by_function(Bank, date, gateway)

wallet_redirect_data_all1 = wallet_redirect_date_data_all%>% unite(col = "Bank_date",
                                                                   Bank, date,
                                                                   sep = "--")
wallet_redirect_date_data_all= wallet_redirect_date_data_all %>%
  filter(
    Bank %in% wallet_redirect_low_data$Bank,
    gateway %in% wallet_redirect_low_data$gateway
  ) %>% filter(sr <= 5.00, vol > 50)
wallet_redirect_data <-
  wallet_redirect_data_all1[!is.na(wallet_redirect_data_all1$gateway), ] %>%
  gather(variable, value, -(Bank_date:gateway)) %>%
  unite(temp, gateway, variable) %>%
  spread(temp, value)

wallet_direct_data_all <-
  sr_results %>% filter(
    merchants != "Industry",
    payment_type == "WALLET",
    source_object == "DIRECT_WALLET_DEBIT"
  ) %>%
  group_by_function(Bank, gateway)
wal_dir_col_names = c("Bank",
                      (sort(
                        unique(wallet_direct_data_all$gateway)
                      )), "Potential Imp")
wallet_direct_low_data <-
  wallet_direct_data_all %>% filter(sr <= 5.00, vol > 50)

wallet_direct_date_data_all <-
  sr_results %>% filter(
    merchants != "Industry",
    payment_type == "WALLET",
    source_object == "DIRECT_WALLET_DEBIT"
  ) %>% group_by_function(Bank, date, gateway)

wallet_direct_data_all1 = wallet_direct_date_data_all%>% unite(col = "Bank_date",
                                                               Bank, date,
                                                               sep = "--")

wallet_direct_date_data_all = wallet_direct_date_data_all %>%
  filter(
    Bank %in% wallet_direct_low_data$Bank,
    gateway %in% wallet_direct_low_data$gateway
  ) %>% filter(sr <= 5.00, vol > 50)
wallet_direct_data <-
  wallet_direct_data_all1[!is.na(wallet_direct_data_all1$gateway), ] %>%
  gather(variable, value, -(Bank_date:gateway)) %>%
  unite(temp, gateway, variable) %>%
  spread(temp, value)
#upi pay plc

upi_pay_data_all <-
  sr_results %>% filter(merchants != "Industry",
                        payment_type == "UPI",
                        source_object == "UPI_PAY") %>%
  group_by_function(payment_source, gateway)
upi_pay_col_names = c("payment_source", (sort(
  unique(upi_pay_data_all$gateway)
)), "Potential Imp")

upi_pay_low_data = upi_pay_data_all %>% filter(sr <= 5.00, vol > 50)
upi_pay_date_data <-
  sr_results %>% filter(merchants != "Industry",
                        payment_type == "UPI",
                        source_object == "UPI_PAY") %>%
  group_by_function(payment_source, date, gateway)
if(!is.null(upi_pay_date_data)){
  upi_pay_data_all1 = upi_pay_date_data%>% unite(col = "payment_source_date",
                                                 payment_source, date,
                                                 sep = "--")
}

upi_pay_date_data <-upi_pay_date_data %>%
  filter(
    payment_source %in% upi_pay_low_data$payment_source,
    gateway %in% upi_pay_low_data$gateway
  ) %>% filter(sr <= 5.00, vol > 50)
upi_pay_data <-
  upi_pay_data_all1[!is.na(upi_pay_data_all1$gateway), ] %>%
  gather(variable, value, -(payment_source_date:gateway)) %>%
  unite(temp, gateway, variable) %>%
  spread(temp, value)

upi_pay_data_all <-
  sr_results %>% filter(merchants != "Industry",
                        payment_type == "UPI",
                        source_object == "UPI_PAY") %>%
  group_by_function(payment_source, gateway)
upi_pay_col_names = c("payment_source", (sort(
  unique(upi_pay_data_all$gateway)
)), "Potential Improvement Rate")

upi_pay_low_data = upi_pay_data_all %>% filter(sr <= 5.00, vol > 100)

upi_pay_no_date_data <-
  sr_results %>% filter(merchants != "Industry",
                        payment_type == "UPI",
                        source_object == "UPI_PAY") %>%
  group_by_function(payment_source, gateway)
if(!is.null(upi_pay_no_date_data)){
  upi_pay_no_data_all1 = upi_pay_no_date_data%>% unite(col = "payment_source",
                                                       payment_source,
                                                       sep = "--")
}

upi_pay_no_date_data <-upi_pay_no_date_data %>%
  filter(
    payment_source %in% upi_pay_low_data$payment_source,
    gateway %in% upi_pay_low_data$gateway
  ) %>% filter(sr <= 5.00, vol > 100)

upi_no_pay_data <-
  upi_pay_no_data_all1[!is.na(upi_pay_no_data_all1$gateway), ] %>%
  gather(variable, value, -(payment_source:gateway)) %>%
  unite(temp, gateway, variable) %>%
  spread(temp, value)
#upi_pay_alt is defined here
upi_pay_apps = c()
if (nrow(upi_no_pay_data) > 0) {
  upi_pay_alt = potential_improvement_data(upi_no_pay_data %>% drop_na("payment_source"))
  if (nrow(upi_pay_alt) > 0) {
    upi_pay_apps = upi_pay_alt%>%
      separate(payment_source, into = c("payment_source"), sep = "--")
    upi_pay_apps = unique(upi_pay_apps[,1])
    upi_pay_alt = data.frame(upi_pay_alt[,-1],
                             row.names = upi_pay_alt[, 1])
    upi_imp <- upi_pay_alt
    sr_indexes <- seq(1, length(upi_imp) - 1, 2)
    vol_indexes <- seq(2, length(upi_imp) - 1, 2)
    gateway_names <- names(upi_imp[,sr_indexes])
    upi_imp_vol <- upi_imp
    upi_imp_vol$`Potential Gateway` <- apply(upi_imp_vol[,sr_indexes], 1, function(x){paste(gateway_names[x == max(x)]," - ",max(x))})
    upi_imp_vol$`Current Gateway` <- apply(upi_imp_vol[,sr_indexes], 1, function(x){paste(gateway_names[x == min(x)]," - ",min(x))})
    upi_imp_vol$overall_vol <- apply(upi_imp_vol[,vol_indexes], 1, sum)
    upi_imp_vol$`Potential Improvement Volume` <- mapply(function(x, y) floor((y*x)/100), upi_imp_vol$potential_imp, upi_imp_vol$overall_vol)
    upi_pay_alt = shortening_df(upi_pay_alt,
                                upi_pay_col_names,
                                "payment_source") %>%
      separate(payment_source, into = c("payment_source"), sep = "--")
    upi_pay_alt = (upi_pay_alt[, c(2, 1, 3:length(upi_pay_alt))])
    lst_four <- c(length(upi_imp_vol)-3,length(upi_imp_vol)-2,length(upi_imp_vol)-1,length(upi_imp_vol))
    upi_alt_merge <-  cbind(upi_pay_alt,upi_imp_vol[,c(vol_indexes,lst_four)])
    upi_alt_merge <- upi_alt_merge %>% filter(upi_imp_vol[,vol_indexes] > 30) %>% arrange(desc(overall_vol)) %>% head(10)
    upi_alt_datatable <- upi_alt_merge %>% select(payment_source,`Current Gateway`,`Potential Gateway`,`Potential Improvement Rate`,`Potential Improvement Volume`)
    
    
  } else{
    upi_alt_datatable = NULL
  }
} else{
  upi_alt_datatable = NULL
}
#upi collect plc
upi_collect_data_all <-
  sr_results %>% filter(merchants != "Industry",
                        payment_type == "UPI",
                        source_object == "UPI_COLLECT") %>%
  separate(
    payment_source,
    c("unique1", "handle"),
    "@",
    extra = "merge",
    fill = "left"
  ) %>% select(-unique1) %>% group_by_function(handle, gateway)

upi_collect_col_names = c("handle", (sort(
  unique(upi_collect_data_all$gateway)
)), "Potential Imp")
upi_collect_low_data <-
  upi_collect_data_all %>% filter(sr <= 5.00, vol > 50)

upi_collect_date_data <-
  sr_results %>% filter(merchants != "Industry",
                        payment_type == "UPI",
                        source_object == "UPI_COLLECT") %>%
  separate(
    payment_source,
    c("unique1", "handle"),
    "@",
    extra = "merge",
    fill = "left"
  ) %>% select(-unique1) %>% group_by_function(handle, date, gateway)

upi_collect_data_all <-
  sr_results %>% filter(merchants != "Industry",
                        payment_type == "UPI",
                        source_object == "UPI_COLLECT") %>%
  separate(
    payment_source,
    c("unique1", "handle"),
    "@",
    extra = "merge",
    fill = "left"
  ) %>% select(-unique1) %>% group_by_function(handle, gateway)

upi_collect_col_names = c( "handle",(sort(
  unique(upi_collect_data_all$gateway)
)), "Potential Improvement Rate")

upi_collect_low_data <-
  upi_collect_data_all %>% filter(sr <= 5.00, vol > 100)

upi_collect_no_date_data <-
  sr_results %>% filter(merchants != "Industry",
                        payment_type == "UPI",
                        source_object == "UPI_COLLECT") %>%
  separate(
    payment_source,
    c("unique1", "handle"),
    "@",
    extra = "merge",
    fill = "left"
  ) %>% select(-unique1) %>% group_by_function(handle, gateway) 

if (!is.null(upi_collect_no_date_data)){
  upi_collect_no_data_all1 = upi_collect_no_date_data %>% unite(col = "handle",
                                                                handle,
                                                                sep = "--")
}

upi_collect_no_date_data = upi_collect_no_date_data%>%
  filter(
    handle %in% upi_collect_low_data$handle,
    gateway %in% upi_collect_low_data$gateway
  ) %>% filter(sr <= 5.00, vol > 100)

upi_no_collect_data <-
  upi_collect_no_data_all1[!is.na(upi_collect_no_data_all1$gateway),] %>%
  gather(variable, value, -(handle:gateway)) %>%
  unite(temp, gateway, variable) %>%
  spread(temp, value)


# upi_collect_alt is defined here
upi_col_handles = c()
if (nrow(upi_no_collect_data) > 0) {
  upi_collect_alt = potential_improvement_data(upi_no_collect_data)
  if (nrow(upi_collect_alt) > 0) {
    upi_col_handles = upi_collect_alt %>% 
      separate(handle, into = c("handle"), sep = "--") 
    upi_col_handles = unique(upi_col_handles[,1])
    upi_collect_alt = data.frame(upi_collect_alt[,-1],
                                 row.names = upi_collect_alt[, 1])
    upi_col_imp <- upi_collect_alt
    sr_indexes <- seq(1, length(upi_col_imp) - 1, 2)
    vol_indexes <- seq(2, length(upi_col_imp) - 1, 2)
    gateway_names <- names(upi_col_imp[,sr_indexes])
    upi_col_imp_vol <- upi_col_imp
    upi_col_imp_vol$`Potential Gateway` <- apply(upi_col_imp_vol[,sr_indexes], 1, function(x){paste(gateway_names[x == max(x)]," - ",max(x))})
    upi_col_imp_vol$`Current Gateway` <- apply(upi_col_imp_vol[,sr_indexes], 1, function(x){paste(gateway_names[x == min(x)]," - ",min(x))})
    upi_col_imp_vol$overall_vol <- apply(upi_col_imp_vol[,vol_indexes], 1, sum)
    upi_col_imp_vol$`Potential Improvement Volume` <- mapply(function(x, y) floor((y*x)/100), upi_col_imp_vol$potential_imp, upi_col_imp_vol$overall_vol)
    upi_collect_alt = shortening_df(upi_collect_alt,
                                    upi_collect_col_names,
                                    "handle") %>%
      separate(handle, into = c("handle"), sep = "--")
    upi_collect_alt = (upi_collect_alt[, c(2, 1, 3:length(upi_collect_alt))])
    lst_four <- c(length(upi_col_imp_vol)-3,length(upi_col_imp_vol)-2,length(upi_col_imp_vol)-1,length(upi_col_imp_vol))
    upi_col_alt_merge <-  cbind(upi_collect_alt,upi_col_imp_vol[,c(vol_indexes,lst_four)])
    upi_col_alt_merge <- upi_col_alt_merge %>% filter(upi_col_imp_vol[,vol_indexes] > 30) %>% arrange(desc(overall_vol)) %>% head(10)
    upi_col_alt_datatable <- upi_col_alt_merge %>% select(handle,`Current Gateway`,`Potential Gateway`,`Potential Improvement Rate`,`Potential Improvement Volume`)
    
  } else{
    upi_col_alt_datatable = NULL
  }
}  else{
  upi_col_alt_datatable = NULL
}

if (!is.null(upi_collect_date_data)){
  upi_collect_data_all1 = upi_collect_date_data %>% unite(col = "handle_date",
                                                          handle, date,
                                                          sep = "--")
}
upi_collect_date_data = upi_collect_date_data%>%
  filter(
    handle %in% upi_collect_low_data$handle,
    gateway %in% upi_collect_low_data$gateway
  ) %>% filter(sr <= 5.00, vol >50)

colnames(upi_collect_date_data)
upi_collect_data <-
  upi_collect_data_all1[!is.na(upi_collect_data_all1$gateway),] %>%
  gather(variable, value, -(handle_date:gateway)) %>%
  unite(temp, gateway, variable) %>%
  spread(temp, value)


#### Industry Comparison Data Processing ####




card_brand_ind_data = grouping_query( flag = T, sr_results %>% filter(payment_type == "CARD"),
                                      c("gateway", "payment_type", "payment_method"), gateway, payment_type, payment_method) %>% head(10)





nb_ind_data =  grouping_query( flag = T, sr_results %>% filter(payment_type == "NB"),
                               c("gateway", "payment_type", "payment_method"), gateway, payment_type, payment_method) %>% head(10)



re_wal_ind_data = grouping_query(flag = T,(sr_results %>% filter(payment_type == "WALLET",
                                                                 source_object == "REDIRECT_WALLET_DEBIT")),
                                 c("gateway","payment_type", "payment_method", "Bank"), gateway,payment_type, payment_method, Bank) %>% head(10)


dir_wal_ind_data =  grouping_query(flag = T,(sr_results %>% filter(payment_type == "WALLET",
                                                                   source_object == "DIRECT_WALLET_DEBIT")),
                                   c("gateway","payment_type", "payment_method", "Bank"), gateway,payment_type, payment_method, Bank) %>% head(10)


upi_pay_ind_data = grouping_query(flag = T, (sr_results %>% filter(payment_type == "UPI",
                                                                   source_object == "UPI_PAY")),
                                  c( "gateway","payment_source"), gateway,payment_source )  %>% head(10)



upi_col_ind_data =  grouping_query( flag = T, sr_results %>% filter( merchants != "Industry",payment_type == "UPI",
                                                                     source_object == "UPI_COLLECT") %>%
                                      separate(payment_source, c("unique1", "handle"), "@", extra = "merge", fill = "left") %>%
                                      select(-unique1), c("gateway","handle"),
                                     gateway, handle)  %>% head(10)


# hide fallback heading if no data 
if(is.null(card_emi_data) && 
   is.null(card_auth_data)){
  heading_text_value_fallback <- ""
}

# hide dimensions with <5% SR heading
if(is.null(credit_date_data_cb_all) && 
   is.null(credit_date_data_all) &&
   is.null(nb_date_data_all) &&
   is.null(wallet_redirect_date_data_all) &&
   is.null(wallet_direct_date_data_all) &&
   is.null(upi_pay_date_data) &&
   is.null(upi_collect_date_data)){
  heading_text_value_dim_sr <- ""
}

# hide heading PG config if no data
if(   heading_text_value_dim_sr == ""){
  heading_text_pg_config <- ""
}

# hide Industry Comparison heading
if( is.null(card_brand_ind_data) &&
   is.null(nb_ind_data) &&
   is.null(re_wal_ind_data) &&
   is.null(dir_wal_ind_data) &&
   is.null(upi_pay_ind_data) &&
   is.null(upi_col_ind_data)){
  heading_text_industry_comparision <- ""
}






################ PLC NEW ##############

potential_improvemnt_query <- glue("SELECT
  *
FROM (
  SELECT
  merchant_id,
    payment_method_type,
    payment_method,
    auth_type,
    card_issuer_bank_name,
    card_isin,
    gateway,
    t_txns,
    LAST_VALUE(sr) OVER (PARTITION BY merchant_id,payment_method_type, payment_method,auth_type,card_issuer_bank_name,card_isin ORDER BY sr asc ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as potential_sr,
    sr,
    ROUND(LAST_VALUE(sr) OVER (PARTITION BY merchant_id,payment_method_type, payment_method,auth_type,card_issuer_bank_name,card_isin ORDER BY sr asc ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) - sr,2) AS potential_improvement,
    LAST_VALUE(gateway)
    OVER (PARTITION BY merchant_id,payment_method_type, payment_method, auth_type,card_issuer_bank_name ,card_isin ORDER BY sr asc
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS recommended_gateway,
      LAST_VALUE(t_txns)
    OVER (PARTITION BY merchant_id,payment_method_type, payment_method, auth_type,card_issuer_bank_name ,card_isin ORDER BY sr asc
          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS potential_pg_txns
  FROM (
    SELECT
      merchant_id,
      payment_method_type,
      payment_method,
      auth_type,
      card_issuer_bank_name,
      card_isin,
      gateway,
      COUNT(DISTINCT CASE WHEN status = 'CHARGED' THEN txn_id END) AS s_txns,
      COUNT(DISTINCT txn_id) AS t_txns,
      ROUND(COUNT(DISTINCT CASE WHEN status = 'CHARGED' THEN txn_id END) / COUNT(DISTINCT txn_id) *100,2) AS sr
    FROM
    `express_checkout_v2.express_checkout*`
 where _table_suffix between '{bq_start_date_suffix}' and '{bq_end_date_suffix}'
 and date_created >= '{bq_start_date} 18:30'
and date_created <= '{bq_end_date} 18:30'
    and
      gateway IS NOT NULL
    GROUP BY
      merchant_id,
      payment_method_type,
      payment_method,
      auth_type,
      card_issuer_bank_name,
      card_isin,
      gateway
    HAVING s_txns >= 30))
WHERE
  potential_improvement >= 3
  AND {merchant_clause}
ORDER BY
  t_txns DESC")


potential_improvemnt_bank <- glue("SELECT
  *
FROM (
  SELECT
  merchant_id,
    card_issuer_bank_name,
    gateway,
    t_txns,
    LAST_VALUE(sr) OVER (PARTITION BY merchant_id,card_issuer_bank_name ORDER BY sr asc ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as potential_sr,
    sr,
    ROUND(LAST_VALUE(sr) OVER (PARTITION BY merchant_id,card_issuer_bank_name ORDER BY sr asc ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) - sr,2) AS potential_improvement,
    LAST_VALUE(gateway)
    OVER (PARTITION BY merchant_id,card_issuer_bank_name ORDER BY sr asc
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS recommended_gateway,
      LAST_VALUE(t_txns)
    OVER (PARTITION BY merchant_id,card_issuer_bank_name ORDER BY sr asc
          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS potential_pg_txns
  FROM (
    SELECT
      merchant_id,
      card_issuer_bank_name,
      gateway,
      COUNT(DISTINCT CASE WHEN status = 'CHARGED' THEN txn_id END) AS s_txns,
      COUNT(DISTINCT txn_id) AS t_txns,
      ROUND(COUNT(DISTINCT CASE WHEN status = 'CHARGED' THEN txn_id END) / COUNT(DISTINCT txn_id) *100,2) AS sr
    FROM
    `express_checkout_v2.express_checkout*`
 where _table_suffix between '{bq_start_date_suffix}' and '{bq_end_date_suffix}'
 and date_created >= '{bq_start_date} 18:30'
and date_created <= '{bq_end_date} 18:30'
and payment_method_type = 'CARD'
    and
      gateway IS NOT NULL
    GROUP BY
      merchant_id,
      card_issuer_bank_name,
      gateway
    HAVING s_txns >= 30))
WHERE
  potential_improvement >= 3
  AND {merchant_clause}
ORDER BY
  t_txns DESC")

potential_improvemnt <- potential_improvemnt_query %>% glue() %>% execute_query()
# potential_improvemnt <- read.csv("cards.csv")
potential_improvemnt_cards <- potential_improvemnt %>% filter(payment_method_type	 == 'CARD') %>% top_n(n=10,t_txns)
potential_improvemnt_cards_filter <-
  potential_improvemnt_cards %>%
  mutate(
    CurrentGateway_SuccessRate = str_c(gateway, ", ", sr, ", ",potential_pg_txns ),
    PotentialGateway_SuccessRate = str_c(recommended_gateway, ", ", potential_sr,", ",potential_pg_txns)
  ) %>% select(
    payment_method,
    auth_type,
    card_issuer_bank_name,
    card_isin,
    CurrentGateway_SuccessRate,
    PotentialGateway_SuccessRate,
    potential_improvement,
    t_txns
  ) %>% rename(
    'Payment Method' = payment_method ,
    'Auth Type' = auth_type,
    'Bank' = card_issuer_bank_name,
    'Card BIN' = card_isin,
    'Current Gateway, SR, Volume' =  CurrentGateway_SuccessRate ,
    'Recommended Gateway, SR, Potential Volume'= PotentialGateway_SuccessRate,
    'Potential Improvement SR'   = potential_improvement,
    'Potential Volume' = t_txns
  ) 
potential_improvemnt_nb <- potential_improvemnt %>% filter(payment_method_type	 == 'NB') %>% top_n(n=10,t_txns)
potential_improvemnt_nb_filter <-
  potential_improvemnt_nb %>%
  mutate(
    CurrentGateway_SuccessRate = str_c(gateway, ", ", sr,", ",t_txns),
    PotentialGateway_SuccessRate = str_c(recommended_gateway, ", ", potential_sr,", ",potential_pg_txns),
    Potential_Volume = t_txns
  ) %>% select(
    card_issuer_bank_name,
    CurrentGateway_SuccessRate,
    PotentialGateway_SuccessRate,
    potential_improvement,
    t_txns
  ) %>% rename(
    'Bank' = card_issuer_bank_name,
    'Current Gateway, SR' =  CurrentGateway_SuccessRate ,
    'Recommended Gateway, SR'= PotentialGateway_SuccessRate,
    'Potential Improvement SR'   = potential_improvement,
    'Potential Volume' = t_txns
  ) 
# potential_improvemnt_bank <- read.csv("banks.csv")
potential_improvemnt_bank <- potential_improvemnt_bank %>% glue() %>% execute_query()
potential_improvemnt_bank <- potential_improvemnt_bank %>% top_n(n=10,t_txns)
potential_improvemnt_bank_filter <-
  potential_improvemnt_bank %>%
  mutate(
    CurrentGateway_SuccessRate = str_c(gateway, ", ", sr,", ",t_txns),
    PotentialGateway_SuccessRate = str_c(recommended_gateway, ", ", potential_sr,", ",potential_pg_txns)
    # Potential_Volume = round(t_txns/100*potential_improvement,0)
  ) %>% select(
    card_issuer_bank_name,
    CurrentGateway_SuccessRate,
    PotentialGateway_SuccessRate,
    potential_improvement,
    t_txns
  ) %>% rename(
    'Bank' = card_issuer_bank_name,
    'Current Gateway, SR, Volume' =  CurrentGateway_SuccessRate ,
    'Recommended Gateway, SR, Volume'= PotentialGateway_SuccessRate,
    'Potential Improvement SR'   = potential_improvement,
    'Potential Volume' = t_txns
  ) 

pi_upi_wallet <- glue("SELECT
*
  FROM (
    SELECT
    payment_method,source_object,payment_source,
    gateway,
    t_txns,
    LAST_VALUE(sr) OVER (PARTITION BY payment_method, source_object,payment_source ORDER BY sr asc ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as potential_sr,
    sr,
    ROUND(LAST_VALUE(sr) OVER (PARTITION BY  payment_method, source_object,payment_source ORDER BY sr asc ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) - sr,2) AS potential_improvement,
    LAST_VALUE(gateway)
    OVER (PARTITION BY payment_method, source_object,payment_source ORDER BY sr asc
          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS recommended_gateway,
    LAST_VALUE(t_txns)
    OVER (PARTITION BY payment_method, source_object,payment_source ORDER BY sr asc
          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS potential_pg_txns
    FROM (
      SELECT
      payment_method,source_object,payment_source,
      gateway,
      COUNT(DISTINCT CASE WHEN status = 'CHARGED' THEN txn_id END) AS s_txns,
      COUNT(DISTINCT txn_id) AS t_txns,
      ROUND(COUNT(DISTINCT CASE WHEN status = 'CHARGED' THEN txn_id END) / COUNT(DISTINCT txn_id) *100,2) AS sr
      FROM
      `express_checkout_v2.express_checkout*`
      where _table_suffix between '{bq_start_date_suffix}' and '{bq_end_date_suffix}'
      and date_created>= '{bq_start_date} 18:30'
      and date_created <='{bq_end_date} 18:30'
      AND  payment_method_type in ('WALLET', 'UPI')
      and {merchant_clause}
      GROUP BY
      payment_method,source_object,payment_source,
      gateway
      HAVING s_txns >= 30
    ))
WHERE
potential_improvement >= 3
ORDER BY t_txns DESC
")

blacklist <- "SELECT
  payment_source,
  COUNT(DISTINCT order_id) AS volume,
  ROUND(COUNT(DISTINCT  CASE  WHEN status = 'CHARGED' THEN order_id  END)/COUNT(DISTINCT order_id)*100,2) AS sr
FROM
  `godel-big-q.express_checkout_v2.express_checkout202106*`
where source_object = 'UPI_PAY'
and {merchant_clause}
group by payment_source
having sr < 5
and volume	 >10
order by volume desc
"
# blacklist <- read.csv("mplgaming_blacklist.csv")
blacklist <- blacklist %>% glue() %>% execute_query()
blacklist <- blacklist %>% top_n(n=10,volume)
colnames(blacklist) <- c("UPI App Selected",
                         "Volume",
                         "Success Rate")

verify_vpa <- "SELECT
regexp_extract(lower(payment_source), r'.*@([a-z]*)')as handle,
count   (distinct order_id) as volume,
ROUND(count(distinct case when status = 'CHARGED' then order_id end)/count(distinct order_id)*100, 2) as SR
from `express_checkout_v2.express_checkout202106*`
where source_object ='UPI_COLLECT'
and {merchant_clause}
GROUP BY
merchant_id,
payment_method,
handle
HAVING volume >= 100
and handle is not null
and sr < 5"
verify_vpa <- verify_vpa %>% glue() %>% execute_query()
# verify_vpa <- read.csv("handle.csv")
if(nrow(verify_vpa)>0){
verify_vpa <-  verify_vpa %>%top_n(n=10,volume) %>% select(handle, volume, SR)
colnames(verify_vpa) <-c("UPI Handle",
                           "Volume",
                           "Success Rate")
}
fallback_pgs <- glue("SELECT
  STRING_AGG(DISTINCT(gateway),',') AS payment_gateway,
  payment_method,
  COUNT(DISTINCT order_id) AS volume,
  COUNT(DISTINCT gateway) AS gateway_volume
FROM
  `express_checkout_v2.express_checkout*`
WHERE _table_suffix between '{bq_start_date_suffix}' and '{bq_end_date_suffix}'
and date_created>= '{bq_start_date} 18:30'
and date_created <='{bq_end_date} 18:30'
  AND card_type != 'WALLET'
  AND payment_method!= 'SODEXO'
  and {merchant_clause}
GROUP BY
  payment_method
HAVING
  gateway_volume = 1
  AND volume >100
ORDER BY
  volume DESC
")
fallback_pgs <- fallback_pgs %>% glue() %>% execute_query()
# fallback_pgs <- read.csv("fallback_pg.csv")
fallback_pgs <- fallback_pgs%>% top_n(n=10,volume) %>% select(payment_gateway,payment_method,volume)
colnames(fallback_pgs) <-c("Payment Gateway",
                           "Payment Method",
                           "Volume")


# pi_upi_wallet <- read.csv("wallet.csv")
pi_upi_wallet <- pi_upi_wallet %>% glue() %>% execute_query()
potential_improvemnt_wallets <- pi_upi_wallet %>% filter(source_object %like% 'WALLET') %>% top_n(n=10,t_txns)
potential_improvemnt_wallets_filter <-
  potential_improvemnt_wallets %>%
  mutate(
    CurrentGateway_SuccessRate = str_c(gateway, ", ", sr,", ", t_txns),
    PotentialGateway_SuccessRate = str_c(recommended_gateway, ", ", potential_sr,", ",potential_pg_txns)
    # Potential_Volume = round(t_txns/100*potential_improvement,0)
  ) %>% select(
    payment_method,
    source_object,
    CurrentGateway_SuccessRate,
    PotentialGateway_SuccessRate,
    potential_improvement,
    t_txns,
  ) %>% rename(
    'Payment Method' = payment_method ,
     'Flow Type' = source_object,
    'Current Gateway, SR, Volume' =  CurrentGateway_SuccessRate ,
    'Recommended Gateway, SR, Volume'= PotentialGateway_SuccessRate,
    'Potential Improvement SR'   = potential_improvement,
    'Potential Volume' = t_txns
  ) 

potential_improvemnt_upi <- pi_upi_wallet %>% filter(payment_method	 == 'UPI') %>% top_n(n=10,t_txns)
potential_improvemnt_upi_filter <-
  potential_improvemnt_upi %>%
  mutate(
    CurrentGateway_SuccessRate = str_c(gateway, ", ", sr, ", ", t_txns),
    PotentialGateway_SuccessRate = str_c(recommended_gateway, ", ", potential_sr, ", ",potential_pg_txns)
    # Potential_Volume = round(t_txns/100*potential_improvement,0)
  ) %>% select(
    payment_source,
    CurrentGateway_SuccessRate,
    PotentialGateway_SuccessRate,
    potential_improvement,
    t_txns
  ) %>% rename(
    'UPI App' = payment_source,
    'Current Gateway, SR, Volume' =  CurrentGateway_SuccessRate ,
    'Recommended Gateway, SR, Volume'= PotentialGateway_SuccessRate,
    'Potential Improvement SR'   = potential_improvement,
    'Potential Volume' = t_txns
  ) 

############# Dimensions Having SR less than 5% SR #########

dim5p_table <- dim5p_query %>%
  glue() %>%
  execute_query()
# dim5p_table <- read.csv("dim5_netmeds.csv")
if(all(is.na(dim5p_table))){
  dim5p_data <- data.frame()
}else{
dim5p_data <- dim5p_table %>% rename(`Payment Gateway` = gateway,`Payment Method Type`= payment_method_type,`Payment Method` = payment_method,`Auth Type` = auth_type ,`Txn Object Type` =txn_object_type,`Volume` = volume, `SR` = SR)
}

new <-"select count(distinct order_id) as orders,
from `express_checkout_v2.ec_new_orders*`
where _table_suffix between '{bq_start_date_suffix}' and '{bq_end_date_suffix}'
and date_created>= '{bq_start_date} 18:30'
and date_created <='{bq_end_date} 18:30'
and {merchant_clause}
"
all <-  "select count(distinct order_id) as orders,
from `express_checkout_v2.express_checkout*`
where _table_suffix between '{bq_start_date_suffix}' and '{bq_end_date_suffix}'
and date_created>= '{bq_start_date} 18:30'
and date_created <='{bq_end_date} 18:30'
and {merchant_clause}
"
new <- new %>%  glue() %>% execute_query()
all <- all %>% glue() %>% execute_query()
total <- sum(new$orders , all$orders)
new_orders <- new$orders
contribution <-  round((new_orders) / total * 100, 2)
overall <- "Overall"
new_final <- cbind(overall, new_orders, contribution)
colnames(new_final) <-
  c("Overall",
    "New Orders Volume",
    "New Orders Rate")


started <- "select payment_method_type,payment_method,
COUNT(DISTINCT case when  status ='STARTED' then txn_id end) as started_volume,
from `express_checkout_v2.express_checkout*`
where  _table_suffix between '{bq_start_date_suffix}' and '{bq_end_date_suffix}'
and date_created>= '{bq_start_date} 18:30'
and date_created <= '{bq_end_date} 18:30'
and {merchant_clause}
group by gateway,payment_method_type,payment_method
having started_volume > 10
order by started_volume desc
"
started <- started %>%  glue() %>% execute_query()
# started <- read.csv("started.csv")
colnames(started) <- c("Payment Method Type",
                       "Payment Method",
                       "Started Volume")


refunds_payments_insights <- "select txn_payment_method_type,gateway,
COUNT(DISTINCT case when  refund_status ='MANUAL_REVIEW' then refund_id end) as manual_review_volume,
COUNT(DISTINCT case when  refund_status ='PENDING' then refund_id end) as pending_volume
from `express_checkout_v2.ec_refund*`
where _table_suffix between '{bq_start_date_suffix}' and '{bq_end_date_suffix}'
and {merchant_clause}
and refund_date >=  '{bq_start_date} 18:30'
and  refund_date <= '{bq_end_date} 18:30'
group by txn_payment_method_type,gateway
"
refunds_payments_insights <- refunds_payments_insights %>%  glue() %>% execute_query()

manual_review_volume <- refunds_payments_insights %>% select( txn_payment_method_type,gateway,manual_review_volume) %>% filter(manual_review_volume > 0) %>% arrange(desc(manual_review_volume))
pending_volume<- refunds_payments_insights %>% select( txn_payment_method_type,gateway,pending_volume) %>% filter(pending_volume > 0)%>% arrange(desc(pending_volume))
colnames(manual_review_volume) <- c("Payment Method Type",
                              "Payment Gateway",
                              "Manual Review Volume")

colnames(pending_volume) <- c("Payment Method Type",
                                         "Payment Gateway",
                                         "Pending Volume")



