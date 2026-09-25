# 团队文档规范

## 目标与边界

本规范说明文档如何分类、命名、标记状态与维护。每个项目的架构、接口、部署、业务口径和决策由该项目仓库维护。项目文档引用本规范的**固定发布版本**，不复制规范正文。

## 入口与类型

项目根目录 `README.md` 介绍项目和启动入口；`docs/README.md` 是文档导航；`docs/CONTRIBUTING.md` 只记录所用规范版本、链接和项目特例。新建单篇文档可取用[中央模板](../document-templates/README.md)。按实际需要创建下面的目录，不为填满目录而写空文档。

| 类型 | 用途 | 默认位置 |
| --- | --- | --- |
| `architecture` | 已核对的当前组件、边界、运行与部署关系 | `docs/architecture/` |
| `design` | 待评审或实施中的方案 | `docs/design/` |
| `decision` | 已选择的架构决策及后果 | `docs/decisions/` |
| `reference` | API、配置、数据口径和术语等可查询事实 | `docs/reference/` |
| `guide` | 完成具体任务的操作与排障步骤 | `docs/guides/` |
| `tutorial` | 以学习为目标、可跟随完成的练习 | `docs/tutorials/` |
| `explanation` | 帮助理解概念与原因的说明 | `docs/explanation/` |
| `record` | 一次迁移、实施或验收的历史记录 | `docs/records/` |
| `standard` | 本项目特有且当前有效的开发约束 | `docs/` |
| `governance` | 项目文档入口、版本引用和特例 | `docs/` |

教程、指南、参考和解释是 [Diátaxis](./diataxis.md) 的四种读者需求；架构、设计、决策与实施记录承担研发过程中的其他用途。目录服务于查找，不要求每个项目都有上述全部目录。

## 状态与依据

除 `docs/README.md` 和模板外，文档顶部使用 `doc_type`、`status`、`area`、`summary` 四个元数据字段：

```yaml
---
doc_type: architecture
status: current
area: platform
summary: 当前系统组件与部署边界
---
```

状态取值：`current`（当前已核对）、`proposed`（提案）、`review-needed`（待核验）、`historical`（历史记录）、`superseded`（已被替代）。`superseded` 另填 `superseded_by`，指向本项目 `docs/` 下的替代文件。

`architecture` 描述从代码、配置和运行环境核对的当前状态；部署文件只能证明仓库提供的编排，不能单独证明线上正在运行。提案不得作为已上线功能的依据。运行行为优先以代码、迁移和可验证接口契约为准。

## 文件名与链接

普通文档文件名采用简短、小写英文 `kebab-case`；正文标题和导航文本按读者语言书写。`README.md`、`CONTRIBUTING.md`、`AGENTS.md` 等约定入口保留固定名称。ADR 按四位编号命名，例如 `0001-use-postgresql.md`。

文档移动时更新所有相对链接和导航入口。外部链接指向规范的固定版本，不指向会移动的默认分支。项目的规范引用和 CI 检查器版本保持一致。

## 变更流程

1. 修改功能时，同一变更更新受影响的当前架构、参考或操作指南。
2. 重大方案先写 `design`；采纳关键选择时写 `decision`。实施后更新当前文档，保留方案和决策用于追溯。
3. 项目文档由该领域维护者评审；无法核实的旧内容标为 `review-needed`。
4. 提交前运行项目的文档检查；CI 至少检查元数据、路径、命名、目录可达性和本地链接。语义正确性仍由评审者核对。
