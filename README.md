# 使用说明

1. pip install -r requirement.txt
2. python async_parse.py data.json



## 注：本项目中有已爬好的数据 results.xls

由于存在两万多条数据，即便采用了协程的方式爬取（可以自行修改程序中的并发量，来提高速度），爬取时间依旧很长。

![](./time.jpg)



请感兴趣的同学，自行优化代码。