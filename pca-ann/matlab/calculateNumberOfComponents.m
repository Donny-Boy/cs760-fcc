function K = calculateNumberOfComponents(S, desired_var)

K = 0;
total_s = sum(S,'all');
current_s = 0;
for k = 1:size(S, 1)
    current_s = current_s + S(k,k);
    var_retained =  current_s / total_s;
    if var_retained >= desired_var
        K = k;
        break
    end
end

end