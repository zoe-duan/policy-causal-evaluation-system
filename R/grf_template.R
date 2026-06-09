# Causal forest / GRF template
# Requires: install.packages("grf")

library(data.table)
library(grf)

DT <- fread("examples/data/demo_panel.csv")
Y <- DT$pm25
W <- DT$treatment
X <- as.matrix(DT[, .(weather_index, month, treated_ever)])

cf <- causal_forest(X, Y, W, num.trees = 1000, honesty = TRUE)
ate <- average_treatment_effect(cf)
print(ate)

# Heterogeneity diagnostics
pred <- predict(cf)$predictions
DT[, cate_hat := pred]
print(DT[, .(mean_cate = mean(cate_hat)), by = treated_ever])
