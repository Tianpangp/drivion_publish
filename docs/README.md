# Drivion Publish 对外接入文档

本目录描述发布系统与执行系统（Exe Runtime / DevKit）之间的稳定 HTTP 契约。管理界面使用的内部 API 不属于该契约。

## 文档导航

- [执行系统接入指南](./执行系统接入指南.md)：鉴权、拉取/提交流程、scope、状态处理和可运行示例。
- [对外 HTTP API](./对外HTTP_API.md)：逐个接口的参数、响应、错误和二进制下载头。
- [制品包规范](./制品包规范.md)：AutoUnit 与 HAL 压缩包的元数据和唯一性规则。
- [`examples/publish_client.py`](./examples/publish_client.py)：Exe/DevKit 可直接改造的 Python 客户端骨架。

## 契约边界

- 现场层级固定为：厂区（site） > 线体（line） > 工位（station） > 设备（equipment）。
- 每台设备最多绑定一个 AutoUnit 精确版本；同一 AutoUnit 版本可被多台设备绑定。
- HAL 不绑定设备。Exe 根据 AutoUnit 声明的 HAL `name + version` 精确拉取。
- Publish 只提供制品和绑定信息，不向设备下发启动、停止、复位或其他控制命令。
- 设备状态和执行日志不提交给 Publish。

## 版本策略

当前对外接口前缀为 `/publish/api/v1/exe`。`v1` 中已存在的字段不会改变语义；可能增加新的可选字段，客户端必须忽略不认识的字段。破坏性修改将使用新的 API 版本前缀。
