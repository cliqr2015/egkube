#submit jobs:
for((i=6;i<=10;i+=1)); do ./submit.sh $i; done

#delete hide jobs:
for((i=65;i<=75;i+=2)); do curl -k -X DELETE -H "X-CLIQR-API-KEY-AUTH:true" -H "Content-Type:application/json" -u cliqradmin:E32CEF6F31909D81 https://172.16.40.59/v2/jobs/$i?hide=true; done 

or

for((i=230;i<=260;i+=4)); do curl -k -X DELETE -H "X-CLIQR-API-KEY-AUTH:true" -H "Content-Type:application/json" -u admin@cliqrtech.com,1:cliqr https://10.193.79.75/v2/jobs/$i?hide=true; echo -e "\n"; done
