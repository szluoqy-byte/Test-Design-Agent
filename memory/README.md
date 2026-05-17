# Memory 使用说明

Memory 保存经人工确认、会影响后续测试用例设计的项目事实。未经用户明确确认，不要自动写入 memory。本文档中的路径均为仓库根目录下 `memory/` 目录内的相对路径。

## 文件

- `project-memory.md`：项目级事实、环境、角色、编号规则、输出偏好。
- `domains/*.md`：可选业务域约定，例如订单、权限、结算、库存；没有匹配文件时跳过。
- `testing-experience-memory.md`：历史缺陷、评审反馈、常见遗漏和回归重点。

## Domain metadata

`memory/domains/*.md` 可选使用文件头 metadata，帮助 `bin/build-memory-context.py` 做稳定匹配和入口冲突识别。

```markdown
---
title: 订单域
keywords: 订单, 下单, 商品详情页
aliases: Order, Checkout
entry_paths:
  - 首页 > 商品详情页 > 立即购买 > 订单确认页
---
```

支持字段：

- `title`：业务域标题。
- `keywords` / `aliases`：用于匹配当前输入的稳定关键词或别名，逗号分隔或列表均可。
- `entry_paths`：可用于入口补全和冲突检测的完整入口路径。

## 使用规则

- 运行时由 `memory-context-builder` 选择相关内容写入 `context-pack.md`。
- 不把单次运行的完整测试用例写入 memory。
- 不把未确认推断、猜测或临时占位写入 memory。
