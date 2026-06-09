# DID / event-study template
# Replace field names and paths before use.

library(data.table)
library(fixest)
# library(did)

DT <- fread("examples/data/demo_panel.csv")

# Baseline TWFE. Use as benchmark; not as final answer for staggered adoption.
fit_twfe <- feols(pm25 ~ treatment + weather_index | city + month, data = DT, cluster = "city")
print(summary(fit_twfe))

# Event-study style with fixest if event_time is meaningful for treated units.
DT[, event_time_clean := fifelse(treated_ever == 1, event_time, NA_integer_)]
fit_event <- feols(pm25 ~ i(event_time_clean, treated_ever, ref = -1) + weather_index | city + month, data = DT, cluster = "city")
print(summary(fit_event))

# For staggered adoption, prefer group-time ATT estimators from did or equivalent.
# att <- att_gt(yname = "pm25", tname = "month", idname = "city", gname = "first_treat_month", data = DT)
