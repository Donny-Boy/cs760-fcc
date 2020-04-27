  
metrics <- function(x) {
  if(nrow(x) != ncol(x)) {cat(" Error!\n")}
  if(nrow(x) == 1) {cat(" Error!")}
  
  if(nrow(x) == 2) {
    # Accuracy, Misclassification rate, Sensitive, Specificity, Positive Predicted and Negative Predicted Value
    tp <- x[1,1]
    fp <- sum(x[1,][-1])
    tn <- sum(x[-1,-1])
    fn <- sum(x[,1][-1])
    acc <- round((tp+tn)/(tp+tn+fp+fn),4)*100
    err <- 100 - acc
    sen <- round(tp/(tp+fn),4)*100
    spe <- round(tn/(tn+fp),4)*100
    ppv <- round(tp/(tp+fp),4)*100
    npv <- round(tn/(tn+fn),4)*100
    data.metric <- list(Accuracy = acc,
                        ERR = err,
                        Sensitive = sen,
                        Specificity = spe,
                        PPV = ppv,
                        NPV = npv)
    return(data.metric)
  }
  
  if(nrow(x) > 2) {
    # Overall accuracy
    ove_acc <- round(sum(diag(x))/sum(x), 2)
    err <- 1-ove_acc
      
    # Accuracy, Sensitive, Specificity, Positive Predicted and Negative Predicted Value
    met <- matrix(0, nrow = nrow(x), ncol = 5)
    colnames(met) <- c("Accuracy", "Sensitive", "Specificity", "PPV", "NPV")
    rownames(met) <- seq(1:nrow(met))
    for(i in 1:nrow(met)) {
      tp <- x[i,i]
      fp <- sum(x[i,][-i])
      tn <- sum(x[-i,-i])
      fn <- sum(x[,i][-i])
      met[i,1] <- round((tp+tn)/(tp+tn+fp+fn),4)*100
      met[i,2] <- round(tp/(tp+fn),4)*100
      met[i,3] <- round(tn/(tn+fp),4)*100
      met[i,4] <- round(tp/(tp+fp),4)*100
      met[i,5] <- round(tn/(tn+fn),4)*100
    }
    
    data.metric <- list(Accuracy = ove_acc,
                        ERR = err,
                        Matrics = met)
    return(data.metric)
  }
}
