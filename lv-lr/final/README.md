Logistic Regression

## Configuration

	Python == 3.6.9
	Pandas == 1.0.3
	NumPy == 1.18.2
	SkLearn == 0.22.2.post1
	Csv == 1.0
	Matplotlib == 3.2.1

## Contents

### PreProcessDataBases.ipynb

Contains the extracion of the databases inside the 'db' folder. You have to download the 'dataset.csv' and 'PCANC' datasets to their correct locations before running

### LogisticRegressionCV.ipynb

Trains the logistic regression and saves ROC and the results, in their respective folders. It is saved all the models in pickle format on 'models' folder.

### PredictExample.ipynb

An exemple of utilization of the model. It is used the 'not_commenter=0.0' data, it is pre-processed and predicted.

The results were 3593 positive labeled and 119710 negative labeled, making an 0.97 ratio of negative comments.


