rm(list = ls())
gc(reset = T)

source("D:/UW/Courses/Spring 2020/760/project/r/ann.R")

indir<-"D:/UW/Courses/Spring 2020/760/project/extract-bow/cv/"
outdir<-"D:/UW/Courses/Spring 2020/760/project/r/"
dataset<-"1"
fold<-"1"
nfolds<-10

ann(indir,outdir,dataset,fold,nfolds)
