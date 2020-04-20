function [U, S] = pca(X)

[m, n] = size(X);

Sigma = 1/m*(X'*X);
[U,S,V] = svd(Sigma);

end
