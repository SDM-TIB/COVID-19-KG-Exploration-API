# COVID-19-KG-Exploration-API



# 1) Get Interactions of a Drug

```
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{
   "Drug":[
  	"C0000970",
  	"C0028978",
  	"C0009214"
   ]
}' \
  http://localhost:5000/exploration?target=DDI&limit=10&page=0
```

# 2) Get all the interaction among the provided Drugs


```
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{
   "Drugs":[
  	"C0000970",
  	"C0028978",
  	"C0009214"
   ]
}' \
  http://localhost:5000/exploration?target=DDI&limit=10&page=0
```
