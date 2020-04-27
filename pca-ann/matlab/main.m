%% Load dataset from csv
clear ; close all; clc
d = readtable('dataset.csv');
%d = d(d.not_commenter ~= 0,:);
%% Export response variable as csv and remove from features table
csvwrite('y_1.csv',d.not_commenter);
d = removevars(d, {'not_commenter', 'id_submission', 'bounced', 'send_failed', 'submissiontype_co'});

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
clear city_state city_state_feature email_hash email_hash_feature d

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
%X_rec  = recoverData(Z, U, K);
%X_rec = (X_rec.*sigma) + mu;

%% Export data
csvwrite('X_1.csv',Z);
%%
my_X = table2array(readtable('X_1.csv','ReadVariableNames',false));
my_y = table2array(readtable('y_1.csv','ReadVariableNames',false));
scatter(my_X(:,1),my_X(:,2),20,my_y(:,1));
