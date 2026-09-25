# 开发文档规范与项目模板

本仓库集中维护团队的文档规范、Copier 项目模板和文档检查工具。项目仓库记录自己的业务与技术事实，通过固定版本链接引用这里的规则。

## 使用方式

1. 阅读 [文档规范](./guidelines/documentation.md)，按需查看 [Diátaxis](./guidelines/diataxis.md)、[架构文档](./guidelines/architecture.md)、[ADR](./guidelines/adr.md) 和[单篇文档模板](./document-templates/README.md)。
2. 新项目使用 Copier 生成文档骨架：

   ```bash
   copier copy --vcs-ref v1.2.0 gh:hyfull/dev-docs-standards my-new-project
   ```

3. 在生成的项目中填写真实信息；将 `.copier-answers.yml` 与项目文件一起提交。
4. 生成项目的 GitHub Actions 会调用中央检查器。本地检查时，在本规范仓库运行 `python scripts/check_docs.py --root <项目目录> --standard-version v1.2.0`。
5. 模板发布新版本后，在**干净的项目工作区**运行 `copier update`，审阅差异和可能的冲突，再提交项目变更。

模板配置使用 `_subdirectory: template`，因此 Copier 只向项目输出 `template/` 下的文件；规范正文和工具源码不会作为项目文档复制过去。项目的 CI 通过本仓库的可复用 Action 调用中央检查器。

## 维护与版本

规范或模板变更通过 PR 评审，并发布固定的 Git 标签。项目引用已发布版本；规范升级需要项目主动更新引用并通过检查。项目内若有专属规则，只写在该项目的文档中。

本仓库不包含任何具体项目的凭据、业务数据或运行事实。
