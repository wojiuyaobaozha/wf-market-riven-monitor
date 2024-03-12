# wf-market-riven-monitor
项目基于wf market api接口调用：https://warframe.market/zh-hans/api_docs
推送当日最新信息并录入到数据库进行推送

# 每3分钟检测一次

# 建议使用screen命令运行在自己的linux vps后台上，就可以愉快的接收了
linux服务器创建一个screen，在新窗口运行本项目, 成功后直接叉掉该窗口, 项目就会在后台一直运行了
screen -S warframe			
#查看创建的screen
screen -ls 		
#连接warframe后台screen，如果存在的话
screen -r warframe


# 使用帮助
`requirements.txt`  为python相关的依赖

`tools_list.yaml` 监控的工具列表，新添加按照已有的格式写

`translation_dict.txt`翻译的文本

`config.yaml` 推送dingding 设置
建立机器人，之后在`config.yaml`中配置，将webhook和秘钥secretKey填入对应的字段，`enable`设置为`1`表示使用该通知
