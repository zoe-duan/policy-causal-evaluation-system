# DoubleML template
# Requires: install.packages(c("DoubleML", "mlr3", "mlr3learners", "data.table"))

library(data.table)
library(DoubleML)
library(mlr3)
library(mlr3learners)

DT <- fread("examples/data/demo_panel.csv")
dml_data <- DoubleMLData$new(DT, y_col = "pm25", d_cols = "treatment", x_cols = c("weather_index", "month", "treated_ever"))
learner <- lrn("regr.ranger", num.trees = 300, min.node.size = 5)
obj <- DoubleMLPLR$new(dml_data, ml_l = learner, ml_m = learner, n_folds = 3)
obj$fit()
print(obj$summary())
