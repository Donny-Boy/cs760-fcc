%% Load dataset from csv
clear ; close all; clc
d = readtable('dataset.csv');
d = d(d.not_commenter ~= 0,:);

%% Export response variable as csv and remove from features table
csvwrite('y_ans.csv',d.not_commenter);
d = removevars(d, {'not_commenter'});

%% Replace city_state column with number of occurrences
city_state = categorical(d.city_state);
city_state_feature = grouptransform(city_state,city_state,@numel);
city_state_feature(city_state == 'EMPTY') = 0;

%% Replace email_hash column with number of occurrences
email_hash = categorical(d.email_hash);
email_hash_feature = grouptransform(email_hash,email_hash,@numel);

%% Keep only numeric values and convert to matrix
X = removevars(d, {'city_state','email_hash'}).Variables;

%% Add one-hot city_state and email_hash columns
X = [X city_state_feature email_hash_feature];

%% Clear unused variables
clear city_states city_state_feature email_hash email_hash_feature

%% Uncomment to sample only part of the data for testing
%X = X(randsample(size(X,1),100),:);

%% Normalize features
[X_norm, mu, sigma] = featureNormalize(X);

%% Run PCA
[U, S] = pca(X_norm);

%% Get number of components for desired retained variance
K = calculateNumberOfComponents(S, 0.99);

%% Project features to new components
Z = projectData(X_norm, U, K);

%% Recover data
X_rec  = recoverData(Z, U, K);
X_rec = (X_rec.*sigma) + mu;

%% Export data
csvwrite('pca_ans.csv',Z);
