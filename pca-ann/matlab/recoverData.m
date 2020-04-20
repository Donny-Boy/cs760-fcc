function X_rec = recoverData(Z, U, K)

Ureduce = U(:,1:K);
X_rec = (Ureduce*Z')';

end
