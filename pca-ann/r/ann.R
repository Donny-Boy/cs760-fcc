ann <- function(indir,outdir,dataset,fold,nfolds) {
  
  rm(list=setdiff(ls(), c("indir","outdir","dataset","fold","nfolds","ann")))
  gc(reset = T)
  
  print(paste("Running ",dataset," (",fold," of ",nfolds,")",sep=""))
  
  library(h2o)
  
  train <- c()
  test <- c()
  for(f in 1:nfolds) {
    X <- read.csv(paste(indir,"X_",dataset,"_",f,".csv",sep=""), header = FALSE)
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
  
  
  h2o.init(max_mem_size = "4G")
  
  predictors <- colnames(data)[-c(1)]
  response <- "y"
  
  # Train model
  model <- h2o.deeplearning(x = predictors,
                            y = response,
                            training_frame = as.h2o(train),
                            standardize = T,
                            overwrite_with_best_model = T,
                            export_weights_and_biases = T,
                            train_samples_per_iteration = -2,
                            epochs = 50,
                            loss = "CrossEntropy",
                            activation = "TanhWithDropout",
                            hidden = c(50),
                            input_dropout_ratio = 0.1,
                            l1=1e-5,
                            l2=1e-4)
  
  # Test
  valpred <- as.data.frame(h2o.predict(model, newdata = as.h2o(test)))
  valpred <- cbind(valpred, test$y)
  
  savelist <- c("valpred")
  save(list = savelist, file = paste(outdir,"valpred_",dataset,"_",fold,".rda", sep=""))
  
  
  h2o.shutdown(prompt = F)
  
  
}
