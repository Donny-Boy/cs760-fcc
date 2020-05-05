rm(list = ls())
gc(reset = T)

source("D:/UW/Courses/Spring 2020/760/project/r/ann.R")

indir<-"D:/UW/Courses/Spring 2020/760/project/extract-bow/v5/cv/"
outdir<-"D:/UW/Courses/Spring 2020/760/project/r/"
dataset<-"0"
fold<-"7"
ncomps<-"PCA"
nfolds<-10
indir<-paste(indir,dataset,"/",ncomps,"/",sep="")

ann(indir,outdir,dataset,fold,ncomps,nfolds)
