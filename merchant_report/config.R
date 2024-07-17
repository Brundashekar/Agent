library(glue)
library(RCurl)
library(htmltools)

#setting variables for query
# project <- "juspay-sandbox"
project <- "godel-big-q"

#setting time variables for queries
time <- Sys.time()
date <- Sys.Date() - 1
bq_end_date <- lubridate::rollback(Sys.Date())
bq_start_date <- lubridate::rollback(bq_end_date)
bq_start_date_suffix <-
  paste0(substr(bq_start_date, 1, 4),
         substr(bq_start_date, 6, 7),
         substr(bq_start_date, 9, 10))
bq_end_date_suffix <-
  paste0(substr(bq_end_date, 1, 4),
         substr(bq_end_date, 6, 7),
         substr(bq_end_date, 9, 10))
bq_refund_date <- as_datetime(format(date - 5, "%Y-%m-%d 00:00:00"))
bq_previous_start_date <- bq_start_date - 30
bq_previous_end_date <- bq_start_date
bq_previous_start_date_suffix <-
  paste0(
    substr(bq_start_date - 30, 1, 4),
    substr(bq_start_date - 30, 6, 7),
    substr(bq_start_date - 30, 9, 10)
  )
bq_previous_end_date_suffix <-
  paste0(substr(bq_start_date, 1, 4),
         substr(bq_start_date, 6, 7),
         substr(bq_start_date, 9, 10))
bq_previous_refund_date <-
  as_datetime(format(bq_start_date - 5, "%Y-%m-%d 00:00:00"))
current_month <- months(date)
previous_month <- months(date %m+% months(-1))

# lines <- readLines("merchant.Rmd")
# header_line_nums <- which(lines == "---") + c(1,-1)
# header <- paste(lines[seq(header_line_nums[1],
#                           header_line_nums[2])],
#                 collapse = "\n")
# properties <- yaml.load(header)
# print(properties)
# Merchant and Industry settings
merchant_filter <- mid
merchant_filter_custom <- glue(sep = "", "'", merchant_filter, "'")

industry_mapper <- list(
  "Billpay" = c(
    "dreamplug_live",
    "cred_store",
    "cred_rentpay",
    "komparify",
    "talkcharge",
    "paydeck",
    "RL",
    "paytonic"
  ),
  "Classified" = c(
    "urbanclap",
    "Rentomojo_prod",
    "quikr",
    "com_shaadi",
    "housejoy",
    "bloombergquint",
    "nobroker",
    "bmatrimony",
    "cmatrimony",
    "libra"
  ),
  "E-pharma" = c(
    "pharmeasytech",
    "1mg",
    "medlife_prod",
    "netmeds",
    "DrLalPathLabs",
    "zoylo",
    "nestor"
  ),
  "E-retail" = c(
    "firstcry",
    "snapdeal",
    "TUL_TMP",
    "purplle.com",
    "zivame",
    "zoomin",
    "furlenco",
    "TheSouledStore",
    "floweraura",
    "starbucks",
    "hipbar",
    "flipkart",
    "flipktaddcybs",
    "firstcry_ae",
    "candere",
    "mirraw",
    "gozefo",
    "Craftsvilla",
    "devops_fynd",
    "voonikapp",
    "ninjacart"
  ),
  "Education" = c("unacademy", "vedantu", "onlinetyari", "mapprr"),
  "Gaming" = c(
    "dream11",
    "mplgaming",
    "myteam11",
    "gameskraft",
    "fanfight",
    "9stacks",
    "sachargaming",
    "faboom",
    "adda52",
    "ballebaazi",
    "khelfactory",
    "gamezy"
  ),
  "Hyperlocal" = c(
    "com.swiggy",
    "swiggy-go",
    "swiggy-liquor",
    "swiggy-wallet",
    "Grofers",
    "hungerbox",
    "milkbasket",
    "dailyninja",
    "swiggy-nf",
    "countrydelight",
    "Curefit",
    "bbinstant",
    "tendercuts",
    "dunzo",
    "winni",
    "freshmenu",
    "starquik",
    "cakezone",
    "swiggy-daily",
    "ccd_prod",
    "bigbasket",
    "highape",
    "goodbox",
    "CommonFloor",
    "Tonguestun",
    "dailyorders",
    "foodpanda"
  ),
  "Insurance" = c(
    "digit",
    "apollo_munich_prod",
    "icicipru",
    "acko_general",
    "religare",
    "acko_drive"
  ),
  "NBFC" = c(
    "getsimpl",
    "creditmantri",
    "epaylater",
    "zestmoney",
    "instamojo"
  ),
  "OTT" = c("gaana", "hoichoi"),
  "Telecom" = c(
    "MVA_PREPAID",
    "MVA_POSTPAID",
    "Vodafone_website_prepaid",
    "Vodafone_website_postpaid",
    "MVA_AMAZON",
    "NEO_PREPAID",
    "NEO_POSTPAID",
    "mva_vodafone",
    "ideaprod",
    "vodafone_web",
    "idea_app",
    "vodafone_app",
    "idea_web"
  ),
  "Ticketing" = c(
    "bms",
    "playo",
    "nspi",
    "justickets",
    "townscript",
    "ticketgoose",
    "hudle",
    "Ticketgenie",
    "justickets_userwallet_testing"
  ),
  "Travel/Stay" = c(
    "olacabs",
    "olacabs_main",
    "ixigoprod",
    "redbus_in",
    "bounce",
    "zinka_commerce",
    "oyorooms",
    "rikant",
    "railyatri",
    "abhibus",
    "drivezy",
    "zoomcar",
    "EMTINT",
    "travelyaari",
    "orixindia",
    "zostel",
    "savaari",
    "mylestech",
    "rapido"
  )
)
get_industry <- function(merchant_id) {
  industries <- names(industry_mapper)
  industry <-
    industries[sapply(industries, function(x)
      merchant_id %in% industry_mapper[[x]])][1]
  if (is.na(industry))
    "Others"
  else
    industry
}
industry <- get_industry(merchant_filter)
all_list = industry_mapper[[industry]]
ind_no_merch_list <- all_list[all_list != merchant_filter]
ind_no_merch_clause <-
  glue(sep = "",
       "merchant_id IN ('",
       paste(ind_no_merch_list, collapse = "','"),
       "')")
merchant_clause <-
  glue(sep = "", "merchant_id in (", merchant_filter_custom, ")")


# Heading Texts in Merchant Report Card
heading_text_1 <-
  text_spec(
    paste(
      "Report Generated for ",
      merchant_filter,
      bq_start_date + 1,
      "to",
      bq_end_date
    ) ,
    "html"
  )
heading_text_payments <- text_spec(
  "Payments" ,
  "html",
  extra_css = "
  font-family: Bebas Neue;
  font-style: normal;
  font-weight: normal;
  font-size: 36px;
  line-height: 43px;
  letter-spacing: 0.5px;
  color: #666F7D;
  margin-left: 29px;
  margin-top: 40px;
    "
)
heading_text_refunds <-
  text_spec(
    "Refunds" ,
    "html",
    extra_css = "font-family: Bebas Neue;
  font-style: normal;
  font-weight: normal;
  font-size: 36px;
  line-height: 43px;
  letter-spacing: 0.5px;
  color: #666F7D;
  margin-left: 29px;
  margin-top: 40px;
  "
  )
heading_text_product_performance <-
  text_spec("PRODUCT FEATURES PERFORMANCE" , "html", align = 'left')
#plc headings
plc_heading <- text_spec("POTENTIONAL IMPROVEMENT AREAS", "html")
explain_plc <- text_spec("Payment Gateway Wise SR Improvements")

heading_bank_pg <- text_spec("Cards Potential Improvement-Bank Wise" , "html")
heading_card_pg <- text_spec("Cards Potential Improvement- BIN Wise" , "html")
heading_nb_pg <-
  text_spec("Net Banking Potential Improvement" , "html")
heading_wallet_pg <-
  text_spec("Wallet Potential Improvement" , "html")
heading_upi_pay_pg <-
  text_spec("UPI Pay Potential Improvement" , "html")
heading_blacklist <- text_spec("Blacklist Poor Performing UPI Apps" , "html")
heading_text_validate_vpa <-
  text_spec(
    "Invalid VPA Contribution" ,
    "html"
  )
heading_fallback <- text_spec("Payment Method Combination Without a Fallback Gateway")
heading_text_value_reord <-
  text_spec("Recommended Payment Method Type Order")


note_css = "font-family: IBM Plex Sans; font-style: normal; font-weight: 400;"


# pg configuration
heading_text_pg_config <-
  text_spec(
    "PG Configuration Optimisaition" ,
    "html",
    bold = TRUE,
    color = "#629FE5",
    font_size = 24
  )
heading_text_value_vpa <-
  text_spec(
    "VPA Errors" ,
    "html",
    bold = TRUE,
    color = "#629FE5",
    font_size = 18
  )
heading_text_value_fallback <-
  text_spec(
    "Payment Method's Without a fallback PG" ,
    "html",
    bold = TRUE,
    color = "#629FE5",
    font_size = 18
  )
heading_text_value_dim_sr <-
  text_spec("Dimensions Having Less Than 5% SR")
heading_text_card_emi <- text_spec("Card - EMI flow")
heading_text_card_auth <- text_spec("Card Flow - 3DS/DOTP")
heading_text_creditCB5p <- text_spec("Cards Card-brand Wise")
heading_text_credit5p <- text_spec("Cards Card-Bin Wise")
heading_text_nb5p <- text_spec("Netbanking Bank Wise")
heading_text_re_wal_5p <- text_spec("Redirect Wallet wise")
heading_text_dir_wal_5p <- text_spec("Direct Wallet wise")
heading_text_upi_pay_5p <- text_spec("UPI Pay Apps")
heading_text_upi_col_5p <- text_spec("UPI Collect Handles")

###industry Comparison
note_industy <-
  text_spec(
    "Note: If a Payment Type lacks data, it signifies that your Success Rate's are better when compared to Industry" ,
    "html",
    font_size = 14,
    note_css
  )
note_plc <-
  text_spec(
    "Note: The Above Represented Potential Improvements are only of Top Dimensions" ,
    "html",
    font_size = 14,
    extra_css = note_css
  )
note_delayed <-
  text_spec(
    "Note: Delayed Success transactions are termed as Conflicted Transactions. i.e. Any transaction getting successful beyond fulfillment window(default 10 mins)" ,
    "html",
    font_size = 18
  )
note_dimension <-
  text_spec(
    "Note: No records available with dimension less then 5% success rate" ,
    "html",
    font_size = 14,
    extra_css = note_css
  )
note_dimension_table <-
  text_spec(
    "Note: The Above Table Represented are of Top Dimensions Affected" ,
    "html",
    font_size = 14,
    extra_css = note_css
  )
note_blacklist <- text_spec("Note: We suggest you to disable UPI Apps which are performing poor and allow others through UPI Collect",
                             "html",
                             font_size = 14,
                             extra_css = note_css)
note_verify_vpa <- text_spec("Note: We suggest you to have Validation  of VPA",
                             "html",
                             font_size = 14,
                             extra_css = note_css)
note_fallback<- text_spec("Note: These Payment method combinations doesn't not have any fall back PG","html",
                          font_size = 14,
                          extra_css = note_css)

heading_text_industry_Comparison <-
  text_spec("INDUSTRY COMPARISION")
heading_text_payment_type_wise <-
  text_spec("Payment Type Wise Comparison" , "html")
heading_text_card_brand_ind <- text_spec("Cards Comparison")
heading_text_credit_debit_ind <- text_spec("Cards Comparison")
heading_text_nb_ind <- text_spec("Net Banking Comparison")
heading_text_re_wal_ind <-
  text_spec("Re-direct Wallets Comparison")
heading_text_dir_wal_ind <- text_spec("Direct Wallets Comparison")
heading_text_upi_pay_ind <- text_spec("UPI Pay Apps Comparison")
heading_text_upi_col_ind <-
  text_spec("UPI Collect Handles Comparison")
heading_chart_webhooks <-
  text_spec("TRANSACTIONS VS WEBHOOKS COUNT")
heading_text_value_otp <-
  text_spec("Juspay Safe Affected Dimensions", "html")
heading_text_payments_insights <-
  text_spec("PAYMENTS INSIGHTS" , "html", align = 'left')
heading_new_orders <- text_spec("New Orders Contribution", "html")
heading_started <- text_spec("Started Volume Contribution","html")
heading_manual_review <- text_spec("Manual Review Refunds Volume <> PMT, PG Wise","html")
heading_pending_refunds <- text_spec("Pending Refunds Volume <> PMT, PG Wise","html")

otp_3ds_text <- ""
reorder_text <- ""
# Convert Highchart to img
chartToImg <- function(plot,
                       width = 600,
                       height = 350) {
  htmlwidgets::saveWidget(widget = plot, file = "chart.html")
  webshot(
    url = "./chart.html",
    file = "chart.png",
    zoom = 1,
    vwidth = width,
    vheight = height
  )
  txt <-
    RCurl::base64Encode(readBin("chart.png", "raw", file.info("chart.png")[1, "size"]), "txt") # Convert graphic to encoded string
  chart_img_tag <-
    htmltools::HTML(sprintf('<img src="data:image/png;base64,%s">', txt))
  chart_div_element <- str_interp('
<div class = "chart_inner">
${chart_img_tag}
</div>')
  return(chart_div_element)
}

# Convert Highchart list of plots to img tags
chartlistToImg <-
  function(list_of_plots,
           width = 1300,
           height = 220) {
    chart_div_elements <- NULL
    
    for (i in 1:length(list_of_plots)) {
      plot <- list_of_plots[[i]]
      htmlwidgets::saveWidget(widget = plot, file = "chart.html")
      webshot(
        url = "./chart.html",
        file = "chart.png",
        zoom = 1,
        vwidth = width,
        vheight = height
      )
      txt <-
        RCurl::base64Encode(readBin("chart.png", "raw", file.info("chart.png")[1, "size"]), "txt") # Convert graphic to encoded string
      chart_img_tag <-
        htmltools::HTML(sprintf('<img src="data:image/png;base64,%s">', txt))
      chart_div_elements[[i]] <- str_interp('
<div class = "chart_inner">
${chart_img_tag}
</div>')
    }
    
    return(chart_div_elements)
  }

beautifyNum <-
  function(x)
    prettyNum(as.numeric(x), big.mark = ",", scientific = FALSE)


shortNum <-
  function(n,
           returnVector = FALSE,
           smallCase = FALSE,
           latency = FALSE) {
    number_format <-
      if (is.null(options()$number_format))
        "IND"
    else
      options()$number_format
    
    if (!(class(n) %in% c('numeric', 'integer'))) {
      if (returnVector) {
        return (c(n, ''))
      } else{
        return (n)
      }
    }
    
    short_num <- c()
    
    if (latency) {
      h <- floor(n / 3600)
      m <- floor(n %% 3600 / 60)
      s <- floor(n %% 3600 %% 60)
      
      h_disp <- if (h > 0)
        paste0(h, 'H ')
      m_disp <- if (m > 0)
        paste0(m, 'M ')
      s_disp <- if (s > 0)
        paste0(s, 'S')
      ms_disp <- if (n < 1 && n > 0)
        paste0(n * 1000, 'MS')
      
      short_num <- c(h_disp, m_disp, s_disp, ms_disp, "")
      
    } else {
      if (number_format == "IND") {
        if (n >= 1e7) {
          short_num <-
            c(beautifyNum(round(n / 1e7, 2)), ifelse(smallCase, "cr", "Cr"))
        } else if (n >= 1e5) {
          short_num <-
            c(beautifyNum(round(n / 1e5, 2)), ifelse(smallCase, "l", "L"))
        } else if (n >= 1e3) {
          short_num <-
            c(beautifyNum(round(n / 1e3, 2)), ifelse(smallCase, "k", "K"))
        } else{
          short_num <- c(beautifyNum(round(n, 2)), " ")
        }
      } else{
        if (n >= 1e9) {
          short_num <-
            c(beautifyNum(round(n / 1e9, 2)), ifelse(smallCase, "b", "B"))
        } else if (n >= 1e6) {
          short_num <-
            c(beautifyNum(round(n / 1e6, 2)), ifelse(smallCase, "m", "M"))
        } else if (n >= 1e3) {
          short_num <-
            c(beautifyNum(round(n / 1e3, 2)), ifelse(smallCase, "k", "K"))
        } else{
          short_num <- c(beautifyNum(round(n, 2)), " ")
        }
      }
      
    }
    
    if (!returnVector) {
      return(paste(short_num[1:2], collapse = ''))
    } else{
      return (short_num)
    }
  }



group_by_function <- function(data, ...) {
  result <- data %>%
    group_by(...) %>%
    summarise(
      vol = sum(txn_count),
      suc = sum(txn_success_count),
      sr = round(sum(txn_success_count) / sum(txn_count) * 100, 2)
    )
  return(result)
}



alterable_dimension <- function(sr_results, payment_meth, ...) {
  x = sr_results %>%
    filter(merchants != "Industry", card_type %in% payment_meth) %>%   #need to give  payment_method_type instead of payment_source
    group_by_function(..., gateway)
  return (x)
}

shortening_df_internal = function(mydf) {
  to = ncol(mydf) - 2
  indx <- seq(1, to, 2)
  for (j in seq_along(indx)) {
    set(
      mydf,
      i = NULL,
      j = j,
      value = paste0(mydf[[indx[j]]], " (",
                     mydf[[indx[j] + 1]], ")", sep =
                       '')
    )
    
  }
  mydf = mydf[, c(1:length(indx), ncol(mydf))]
  
  return(mydf)
}

shortening_df = function(df, col_names, index_label = "") {
  df_compressed <-
    data.frame(matrix(ncol = length(col_names), nrow = 0))
  colnames(df_compressed) <- col_names
  for (row in 1:nrow(df)) {
    x = shortening_df_internal(df[row,])
    colnames(x) = col_names[-1]
    x <- tibble::rownames_to_column(x, index_label)
    df_compressed = rbind(df_compressed, x)
  }
  return(df_compressed)
}

potential_improvement_data = function(data_gateway) {
  success_indexes <- seq(3, length(data_gateway), 3)
  vol_indexes <- seq(4, length(data_gateway), 3)
  data_gateway$tot_vol = rowSums(data_gateway[vol_indexes])
  data_gateway$succ_vol = rowSums(data_gateway[success_indexes])
  data_gateway$curr_sr =  ((data_gateway$succ_vol
                            / data_gateway$tot_vol) * 100)
  data_gateway = data_gateway %>% filter(!is.na(tot_vol) &
                                           !is.na(succ_vol))
  data_gateway = purrrlyr::by_row(data_gateway,
                                  estimating_sr,
                                  .collate = 'cols',
                                  .to = "potential_imp")
  if (nrow(data_gateway) > 0) {
    data_gateway <-
      as.data.frame(data_gateway) %>% select_at(vars(-contains("suc"))) %>% filter(potential_imp > 3) %>% select(-c(tot_vol, curr_sr))  ### 3
    return(data_gateway)
  } else{
    return(data_gateway)
  }
  
}

estimating_sr <- function(data_gateway) {
  sr_indexes <- seq(2, length(data_gateway) - 3, 3)
  data_gateway[is.na(data_gateway)] <- 0
  if (data_gateway$curr_sr < 85.00 && data_gateway$tot_vol > 100) {
    df = data_gateway[, sr_indexes]
    n = length(df)
    sr_list = t(apply(df, 1, sort))
    high_sr = (sr_list[, n])[[1]]
    res_high = as.data.frame(which(data_gateway == high_sr, arr.ind = TRUE))
    high_vol_col = min(res_high$col) + 2
    if (as.integer(data_gateway[, high_vol_col]) < 50) {
      n = n - 1
      high_sr = (sr_list[, n])[[1]]
    }
    low_sr = min(df)
    res_low = as.data.frame(which(data_gateway == low_sr, arr.ind = TRUE))
    low_vol_col = min(res_low$col) + 2
    low_vol = as.integer(data_gateway[, low_vol_col])
    if (low_vol > 50 &
        (as.double(data_gateway[, low_vol_col - 2])) < 75) {
      subractable_vol = as.integer(data_gateway[, low_vol_col - 1])
      estmated_succ = round((low_vol * high_sr) / 100, 0)
      estmated_SR <-
        ((
          as.integer(data_gateway$succ_vol) - subractable_vol + estmated_succ
        ) / as.integer(data_gateway$tot_vol)
        ) * 100
      potential_imp = round(estmated_SR -  data_gateway$curr_sr, 2)
      return(potential_imp)
    } else{
      return(0.00)
    }
  }
  else{
    return(0.00)
  }
}

datatable_ <-
  function(table,
           disp_text,
           do_plot = FALSE,
           plot_data = NULL) {
    ###copy
    if (!is.null(table)) {
      renderText(disp_text)
      DT::renderDataTable(table)
      if (do_plot == TRUE) {
        renderPlotly(plot_data)
      }
    }
  }

alterable_dimension <- function(sr_results, payment_meth, ...) {
  x = sr_results %>%
    filter(merchants != "Industry", payment_type %in% c(payment_meth)) %>%
    group_by_function(..., gateway)
  return (x)
}

zeroRows <- function (df) {
  if (nrow(df) == 0) {
    return(TRUE)
  } else{
    return(FALSE)
  }
}

grouping_query <- function(flag = TRUE, data, merge_list, ...) {
  group_indus <- data %>% filter(merchants == "Industry") %>%
    group_by_function(...) %>% rename(Ind_vol = vol, Ind_SR = sr) %>%
    select(-c(suc))
  
  group_merch <- data %>% filter(merchants != "Industry") %>%
    group_by_function(...) %>% drop_na() %>% select(-c(suc))
  
  merged_df <- merge(
    group_merch,
    group_indus,
    by.x = merge_list,
    by.y = merge_list,
    all.x = TRUE
  ) %>%
    arrange(desc(vol))
  
  if (flag  == TRUE) {
    merged_df <-
      merged_df %>% filter(sr < Ind_SR - 10, vol > 100, Ind_vol > 100)
  }
  
  return(merged_df)
}


setChartHeight <- function(x) {
  if (x <= 2) {
    chart_height <- 250
  } else{
    chart_height <- 250 + 50 * (x - 2)
  }
  
  if (chart_height >= 950) {
    chart_height <- 950
  }
  
  return(chart_height)
}


shortNum <-
  function(n,
           returnVector = FALSE,
           smallCase = FALSE,
           latency = FALSE) {
    number_format <-
      if (is.null(options()$number_format))
        "IND"
    else
      options()$number_format
    
    if (!(class(n) %in% c('numeric', 'integer'))) {
      if (returnVector) {
        return (c(n, ''))
      } else{
        return (n)
      }
    }
    
    short_num <- c()
    
    if (latency) {
      h <- floor(n / 3600)
      m <- floor(n %% 3600 / 60)
      s <- floor(n %% 3600 %% 60)
      
      h_disp <- if (h > 0)
        paste0(h, 'H ')
      m_disp <- if (m > 0)
        paste0(m, 'M ')
      s_disp <- if (s > 0)
        paste0(s, 'S')
      ms_disp <- if (n < 1 && n > 0)
        paste0(n * 1000, 'MS')
      
      short_num <- c(h_disp, m_disp, s_disp, ms_disp, "")
      
    } else {
      if (number_format == "IND") {
        if (n >= 1e7) {
          short_num <-
            c(beautifyNum(round(n / 1e7, 2)), ifelse(smallCase, "cr", "Cr"))
        } else if (n >= 1e5) {
          short_num <-
            c(beautifyNum(round(n / 1e5, 2)), ifelse(smallCase, "l", "L"))
        } else if (n >= 1e3) {
          short_num <-
            c(beautifyNum(round(n / 1e3, 2)), ifelse(smallCase, "k", "K"))
        } else{
          short_num <- c(beautifyNum(round(n, 2)), " ")
        }
      } else{
        if (n >= 1e9) {
          short_num <-
            c(beautifyNum(round(n / 1e9, 2)), ifelse(smallCase, "b", "B"))
        } else if (n >= 1e6) {
          short_num <-
            c(beautifyNum(round(n / 1e6, 2)), ifelse(smallCase, "m", "M"))
        } else if (n >= 1e3) {
          short_num <-
            c(beautifyNum(round(n / 1e3, 2)), ifelse(smallCase, "k", "K"))
        } else{
          short_num <- c(beautifyNum(round(n, 2)), " ")
        }
      }
      
    }
    
    if (!returnVector) {
      return(paste(short_num[1:2], collapse = ''))
    } else{
      return (short_num)
    }
  }
