function Z = projectData(X, U, K)

Ureduce = U(:,1:K);
Z = X*Ureduce;

end
