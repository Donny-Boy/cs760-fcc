ann <- function(indir,outdir,dataset,fold,ncomps,nfolds) {
  
  rm(list=setdiff(ls(), c("indir","outdir","dataset","fold","ncomps","nfolds","ann")))
  gc(reset = T)
  
  print(paste("Running ",dataset,"_",ncomps," (",fold," of ",nfolds,")",sep=""))
  
  library(h2o)
  
  train <- c()
  test <- c()
  for(f in 1:nfolds) {
    X <- read.csv(paste(indir,"X_",ncomps,"_",dataset,"_",f,".csv",sep=""), header = FALSE)
    y <- read.csv(paste(indir,"y_",dataset,"_",f,".csv",sep=""), header = FALSE)
    names(y) <- "y"
    data <- cbind(y, X)
    data$y <- as.factor(data$y)
    if(f == fold) {
      test <- rbind(test, data)
    } else {
      train <- rbind(train, data)
    }
  }
  
  nfeatures <- ncol(train) - 1
  hidden_sizes <- list(
    c(max(as.integer(0.10*nfeatures),1)),
    c(max(as.integer(0.25*nfeatures),1)),
    c(max(as.integer(0.50*nfeatures),1)),
    c(max(as.integer(0.75*nfeatures),1)),
    c(max(as.integer(1.00*nfeatures),1))
  )
  
  # Hyperparameters for ANN
  hyper_params <- list(activation=c("RectifierWithDropout","TanhWithDropout"),
                       hidden=hidden_sizes,
                       input_dropout_ratio=c(0,0.1,0.2),
                       l1=c(1e-6,1e-5,1e-4,1e-3), 
                       l2=c(1e-6,1e-5,1e-4,1e-3))
  
  # Search criteria
  search_criteria <- list(strategy = "RandomDiscrete", 
                          max_models = 100,  
                          #max_runtime_secs = 360, 
                          stopping_metric = "misclassification")
  
  possible_comps <- c("PCA","Orig")
  h2o.init(port = 44321+as.integer(dataset)*1000+as.integer(fold)*10+match(ncomps, possible_comps), max_mem_size = "16G")
  h2o.removeAll()
  
  predictors <- colnames(data)[-c(1)]
  response <- "y"
  
  grid_name <- paste("deepmodel","_",ncomps,"_",dataset,"_",f,sep="")
  # Grid search
  dl <- h2o.grid(x = predictors, 
                 y = response, 
                 training_frame = as.h2o(train),
                 nfolds = 5, 
                 fold_assignment = "Stratified",
                 algorithm = "deeplearning", 
                 grid_id = grid_name,
                 standardize = T,
                 overwrite_with_best_model = T,
                 export_weights_and_biases = T,
                 train_samples_per_iteration = -2,
                 keep_cross_validation_predictions = T,
                 epochs = 30,
                 loss = "CrossEntropy",
                 hyper_params = hyper_params, 
                 search_criteria = search_criteria)
  
  # Get model best model
  grid <- h2o.getGrid(grid_name, sort_by = "accuracy", decreasing = TRUE)
  best <- h2o.getModel(grid@model_ids[[1]])
  
  # Print best model parameters
  best_params <- paste( best@parameters$activation, best@parameters$hidden, best@parameters$input_dropout_ratio, best@parameters$l1, best@parameters$l2, sep=", ")
  best_params  
  
  # Train predictions
  cvpred <- as.data.frame(h2o.cross_validation_holdout_predictions(best))
  cvpred <- cbind(cvpred, train$y)
  
  # Test predictions
  valpred <- as.data.frame(h2o.predict(best, newdata = as.h2o(test)))
  valpred <- cbind(valpred, test$y)
  
  savelist <- c("valpred", "cvpred")
  save(list = savelist, file = paste(outdir,"grid_valpred_",ncomps,"_",dataset,"_",fold,".rda", sep=""))
  
  savelist <- c("best_params")
  save(list = savelist, file = paste(outdir,"grid_bestparams_",ncomps,"_",dataset,"_",fold,".rda", sep=""))
  
  h2o.saveModel(object=best,force=TRUE)
  
  
  h2o.shutdown(prompt = F)
  
  
}
