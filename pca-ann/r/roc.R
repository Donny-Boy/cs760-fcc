rm(list = ls())
gc(reset = T)
par(new=FALSE)

color_offset <- 1
dataset <- "2"
file.names <- dir("D:/UW/Courses/Spring 2020/760/project/r/valpred/", pattern =paste("valpred_",dataset,sep=""))

all_valpred <- c()
for(filename in file.names) {
  # Load valpred
  load(paste("D:/UW/Courses/Spring 2020/760/project/r/valpred/",filename,sep=""))
  all_valpred <- rbind(all_valpred, valpred)
}

# Plot ROC and calculate AUC
thresholds <- rev(seq(0,1,0.001))
TPR <- rep(0, length(thresholds))
FPR <- rep(0, length(thresholds))
y <- all_valpred[,ncol(all_valpred)]
auc <- rep(0, length(levels(y)))
for(c in 1:length(levels(y))) {
  for(t in 1:length(thresholds)) {
    pred <- all_valpred[,c+1] >= thresholds[t]
    obs <- as.numeric(y) == c
    tp <- sum(pred & obs)
    fp <- sum(pred & !obs)
    fn <- sum(!pred & obs)
    tn <- sum(!pred & !obs)
    TPR[t] <- tp/(tp+fn)
    FPR[t] <- (1 - (tn/(tn+fp)))
  }
  dTPR <- c(diff(TPR),0)
  dFPR <- c(diff(FPR),0)
  auc[c] <- sum(TPR * dFPR) + sum(dTPR * dFPR)/2
  
  if(c != 1) {
    par(new=TRUE)
  }
  plot(FPR, TPR, type="l", col=c+color_offset, lwd=3, xlim=c(0,1), ylim=c(0,1), xlab="FPR", ylab="TPR")
}

legend(0.55, 0.25, paste("class ",levels(y)," (area=",format(round(auc,2),nsmall=2),")",sep=""), col=1:length(levels(y))+color_offset, lty=1, lwd=3)


