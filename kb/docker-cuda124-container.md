---
title: CUDA124容器配置
date: 2026-05-21
last_updated: 2026-05-28
type: reference
tags: [Docker, CUDA, H800]
sources:
  - 自用服务器配置
related:
  - "[devices_inventory](devices_inventory.md)"
  - "[docker-commands](docker-commands.md)"
confidence: high
contested: false
---

## 当前启动命令

```bash
docker run -d \
--privileged \
--cap-add=ALL \
--ipc=host \
--network host \
--hostname zhangyanbo-cuda124 \
--name zhangyanbo_cuda124 \
-v /data/project/public:/data/project/public \
-v /data/project/zyb:/data/project/zyb \
-v /data/zyb/root/anaconda3:/root/anaconda3 \
-v /data/zyb/root/.bashrc:/root/.bashrc \
-v /data/zyb/root/.profile:/root/.profile \
-v /data/zyb/root/.cache:/root/.cache \
-v /data/zyb/code:/code \
-v /data/zyb/software:/software \
--runtime=nvidia \
-ti \
docker.dm-ai.cn/algorithm-research/lmsysorg/sglang:20250306
```

## 推荐下次启动命令（新增 xiaowangzi 挂载）

```bash
docker run -d \
--privileged \
--cap-add=ALL \
--ipc=host \
--network host \
--hostname zhangyanbo-cuda124 \
--name zhangyanbo_cuda124 \
-v /data/project/public:/data/project/public \
-v /data/project/zyb:/data/project/zyb \
-v /data/zyb/root/anaconda3:/root/anaconda3 \
-v /data/zyb/root/.bashrc:/root/.bashrc \
-v /data/zyb/root/.profile:/root/.profile \
-v /data/zyb/root/.cache:/root/.cache \
-v /data/zyb/code:/code \
-v /data/zyb/software:/software \
-v /data/zyb/xiaowangzi:/home/xiaowangzi \
--runtime=nvidia \
-ti \
docker.dm-ai.cn/algorithm-research/lmsysorg/sglang:20250306
```

**下次相比当前的变化:** 新增 `-v /data/zyb/xiaowangzi:/home/xiaowangzi`

**Key details:**
- 镜像: `docker.dm-ai.cn/algorithm-research/lmsysorg/sglang:20250306`
- 容器名: `zhangyanbo_cuda124`
- 主机名: `zhangyanbo-cuda124`
- GPU 支持: `--runtime=nvidia`
- 网络模式: host
- 特权模式: `--privileged --cap-add=ALL`
- 挂载卷: 项目目录、anaconda3、bashrc/profile、cache、code、software、xiaowangzi