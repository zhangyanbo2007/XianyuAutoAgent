---
title: 隐私工程目录
date: 2026-05-26
last_updated: 2026-05-26
type: entity
tags: [隐私, 保险, 个人档案, 人物]
---

# 隐私工程

集中管理个人隐私相关文件，包括保险理赔、个人档案、人物档案、医疗诊断等敏感材料。

## 目录结构

| 子目录 | 内容 | 来源 |
|--------|------|------|
| `insurance/` | 电动车意外险理赔项目（HTML报告、研究笔记、索赔计划、理赔提交材料） | 原 `projects/insurance/` |
| `refs-insurance/` | 保险原始参考材料（保单PDF、事故原始照片、OCR结果） | 原 `refs/insurance/` |
| `profile/` | 个人档案（学术画像、职业轨迹、能力体系、互联网账号、创作作品） | 原 `kb/profile/` |
| `people/` | 重要他人档案（黄心娜、黄子晨、兰周婵、林凤珠、聂霞等） | 原 `kb/people/` |
| `medical/` | 医疗诊断证明照片 | 原 `refs/media/` 散落文件 |

## 关联

- 理赔进展记录：`~/.claude/projects/.../memory/insurance-claim-progress.md`
- 理赔报告链接：`~/.claude/projects/.../memory/insurance-claim-report.md`
- 理赔HTML更新流程：`kb/infra/insurance-html-update-pattern.md`
- 微信聊天提取技能：`.claude/skills/wechat-extract/SKILL.md`（输出到 `refs-people/`）
