rm(list = ls())
gc(reset = T)
par(new=FALSE)

source("D:/UW/Courses/Spring 2020/760/project/r/calc_roc.R")
color_offset <- 1
pred_dir <- "D:/UW/Courses/Spring 2020/760/project/r/v5/v2/grid/"
rocs_dir <- "D:/UW/Courses/Spring 2020/760/project/r/v5/v2/grid/ROCs/"


library(h2o)
h2o.init(max_mem_size = "4G")


results <- c()

for(ncomps in c("Orig","PCA")) {
  for(dataset in seq(0,4)) {
  
    model_name <- paste(ncomps,"_",dataset,sep="")
    file.names <- dir(pred_dir, pattern =paste("valpred_",model_name,sep=""))
    
    print(paste("Running",model_name))
    
    
    nfiles <- 0
    all_valpred <- c()
    valpreds <- list()
    for(filename in file.names) {
        # Load valpred
        load(paste(pred_dir,filename,sep=""))
        all_valpred <- rbind(all_valpred, valpred)
        valpreds[[nfiles+1]] <- valpred
        nfiles <- nfiles+1
    }
    
    # Save ROC and calculate AUC
    val_auc <- calc_roc(paste(rocs_dir,"ROC_",model_name,"_val.png",sep=""), paste("Validation",model_name), all_valpred)
    
    # Calculate Accuracy
    accuracies <- c()
    max_accuracy <- 0
    best_fold <- 0
    current_fold <- 1
    for(valpred in valpreds) {
      current_accuracy <- mean(valpred$predict==valpred$`test$y`)
      accuracies <- rbind(accuracies, current_accuracy)
      if(current_accuracy > max_accuracy) {
        max_accuracy <- current_accuracy
        best_fold <- current_fold
      }
      current_fold <- current_fold + 1
    }
    
    # Test
    indir<-"D:/UW/Courses/Spring 2020/760/project/extract-bow/v5/cv/"
    indir<-paste(indir,dataset,"/",ncomps,"/",sep="")
    X <- read.csv(paste(indir,"X_test_",model_name,".csv",sep=""), header = FALSE)
    y <- read.csv(paste(indir,"y_test_",dataset,".csv",sep=""), header = FALSE)
    names(y) <- "y"
    data <- cbind(y, X)
    data$y <- as.factor(data$y)
    h2o.removeAll()
    predictors <- colnames(data)[-c(1)]
    response <- "y"
    model_file.names <- dir(pred_dir, pattern =paste("v2_deepmodel_",model_name,"_",best_fold,"_model_",sep=""))
    
    if(length(model_file.names) > 0) {
      model <- h2o.loadModel(paste(pred_dir,model_file.names[1],sep=""))
      #model <- h2o.loadModel(paste(pred_dir,"model_",model_name,"_",best_fold,sep=""))
      valpred <- as.data.frame(h2o.predict(model, newdata = as.h2o(X)))
      valpred <- cbind(valpred, data$y)
      
      
      # Save ROC and calculate AUC
      test_auc <- calc_roc(paste(rocs_dir,"ROC_",model_name,"_test.png",sep=""), paste("Test",model_name), valpred)
      val_acc <- mean(accuracies)
      test_acc <- mean(valpred$predict==valpred$`data$y`)
      results <- rbind(results, c(model_name,nfiles,val_auc,val_acc,test_auc,test_acc))
    }

  }
}

colnames(results) <- c("Model","nFiles","ValAUC","ValAccuracy","TestAUC","TestACC")

savelist <- c("results")
save(list = savelist, file = paste(rocs_dir,"results.rda", sep=""))

h2o.shutdown(prompt = F)
