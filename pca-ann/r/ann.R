ann <- function(indir,outdir,suffix) {
  
rm(list=setdiff(ls(), c("indir","outdir","suffix","ann")))
gc(reset = T)

print(paste("Running",suffix))

library(h2o)

source(paste(outdir,"/metrics.R",sep=""))

X <- read.csv(paste(indir,"/pca",suffix,".csv",sep=""), header = FALSE)
y <- read.csv(paste(indir,"/y",suffix,".csv",sep=""), header = FALSE)
names(y) <- "y"
data <- cbind(y, X)
data <- data[data$y!=0,]
data$y <- as.factor(data$y)

data <- data[sample(nrow(data),1000),]

# Hyperparameters for ANN
#lambdas <- matrix(0, nrow=15, ncol=1)
#for(i in 1:length(lambdas)) {
#  lambdas[i] = 1e-6 * 2^(i-1)
#}
lambdas <- seq(0,1e-4,1e-6)
hyper_params <- list(activation=c("RectifierWithDropout","TanhWithDropout","MaxoutWithDropout"),
                     hidden=list(c(10),c(30),c(50),c(70)),
                     input_dropout_ratio=c(0,0.1,0.2),
                     l1=lambdas, 
                     l2=lambdas)

# Search criteria
search_criteria <- list(strategy = "RandomDiscrete", 
                        max_models = 100,  
                        #max_runtime_secs = 360, 
                        stopping_metric = "misclassification")

nfolds <- 10
#n <- nrow(data)
#sets <- split(data, (sample(rep(1:nfolds,ceiling(n/nfolds))))[1:n])
data0 <- data[data$y=="-1",]
data1 <- data[data$y=="1",]
n0 <- nrow(data0)
n1 <- nrow(data1)
sets0 <- split(data0, (sample(rep(1:nfolds,ceiling(n0/nfolds))))[1:n0])
sets1 <- split(data1, (sample(rep(1:nfolds,ceiling(n1/nfolds))))[1:n1])

# Store metrics
metcv <- matrix(0, nrow = nfolds, ncol = 7)
metval <- matrix(0, nrow = nfolds, ncol = 7)
colnames(metcv) <- c("Accuracy", "ERR", "Sensitivity", "Specificity", "PPV", "NPV", "CrossEntropy")
colnames(metval) <- c("Accuracy", "ERR", "Sensitivity", "Specificity", "PPV", "NPV", "CrossEntropy")


h2o.init(max_mem_size = "6G")

for(i in 1:nfolds) {
  
  print(paste("Test Set ",i,sep=""))
  
  h2o.removeAll()
  
  train <- rbind(do.call("rbind", sets0[(1:nfolds)[-i]]),
                 do.call("rbind", sets1[(1:nfolds)[-i]]))
  test <- rbind(sets0[[i]],
                sets1[[i]])
  
  predictors <- colnames(data)[-c(1)]
  response <- "y"

  # Grid search
  dl <- h2o.grid(x = predictors, 
                 y = response, 
                 training_frame = as.h2o(train),
                 nfolds = 5, 
                 fold_assignment = "Stratified",
                 algorithm = "deeplearning", 
                 grid_id = "deepmodel",
                 epochs = 30,
                 hyper_params = hyper_params, 
                 search_criteria = search_criteria,
                 standardize = T,
                 overwrite_with_best_model = T,
                 train_samples_per_iteration = -2,
                 keep_cross_validation_predictions = T,
                 loss = "CrossEntropy")
  
  # Get model best model
  grid <- h2o.getGrid("deepmodel", sort_by = "logloss", decreasing = FALSE)
  best <- h2o.getModel(grid@model_ids[[1]])
  
  # Metrics for the training set
  cvpred <- as.data.frame(h2o.cross_validation_holdout_predictions(best))
  cm_cv <- table(Predicted = cvpred$predict, Observed = train$y)
  if(nrow(cm_cv) == ncol(cm_cv)) {
    metcv[i,1:6] <- do.call("rbind", metrics(cm_cv))
  }
  y_hat <- cvpred$p1
  y_obs <- train$y == 1
  metcv[i,7] <- sum(-(y_obs*log(y_hat) + (1-y_obs)*log(1-y_hat)))/nrow(train)
  
  # Metrics for the testing set
  valpred <- as.data.frame(h2o.predict(best, newdata = as.h2o(test)))
  cm_val <- table(Predicted = valpred$predict, Observed = test$y)
  if(nrow(cm_val) == ncol(cm_val)) {
    metval[i,1:6] <- do.call("rbind", metrics(cm_val))
  }
  y_hat <- valpred$p1
  y_obs <- test$y == 1
  metval[i,7] <- sum(-(y_obs*log(y_hat) + (1-y_obs)*log(1-y_hat)))/nrow(test)
}

setwd(outdir)
savelist <- c("metcv", "metval")
save(list = savelist, file = paste("metrics",suffix,".rda", sep=""))


h2o.shutdown(prompt = F)


}
