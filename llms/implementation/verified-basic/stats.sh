awk '/total:/ {for (i=1; i<=NF; i++) if ($i ~ /total:/) total=$(i+1); else if ($i ~ /proved:/) proved=$(i+1)} END {printf "%.2f\n", (proved/total)*100}' $1
