---
title: Docker启动命令备忘
date: 2026-05-12
last_updated: 2026-05-21
type: cheatsheet
tags: [Docker, 运维, GPU容器, 百炼]
sources:
  - 自用服务器配置
related:
  - "[devices_inventory](devices_inventory.md)"
confidence: high
contested: false
---

# Docker启动命令备忘

## cuda124 (192.168.68.120)

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

## cuda124 (192.168.68.120)推荐版本（新增 xiaowangzi 挂载）

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

**差异说明:** 推荐版本新增 `-v /data/zyb/xiaowangzi:/home/xiaowangzi` 挂载点。

## node37 (192.168.68.98)

8x RTX 3090, NVIDIA驱动550.90.07, CUDA 12.1.1。SSH端口33，密码333333。

容器ID: `0b774e96a6569cd55a3b87b00b667dafcfa93cbef2495e4cef1a41c1a3e12a7a`

### docker run 命令

注意：NFS挂载是在容器启动后通过mount命令挂载的（privileged + host网络模式允许在容器内直接mount NFS），不是docker run的-v参数。

```bash
docker run -d \
--privileged \
--cap-add=ALL \
--ipc=host \
--network host \
--hostname node37.atp \
--name node37_zyb \
-v /data/zyb/software:/software \
--runtime=nvidia \
-ti \
nvcr.io/nvidia/cuda:12.1.1-devel-ubuntu22.04
```

### 容器内NFS挂载命令

```bash
# NAS 192.168.68.73 挂载
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/zyb/code /code
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/public /data/public
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/zyb/root/.bashrc /root/.bashrc
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/zyb/root/.cache /root/.cache
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/zyb/root/.profile /root/.profile
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/zyb/root/anaconda3 /root/anaconda3
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/zyb/user/anaconda3 /home/user/anaconda3
# 项目NFS 192.168.68.74 挂载
mount -t nfs4 192.168.68.74:/data/nfsshare/project /mnt/nfs_project
```

### SSH连接

```bash
sshpass -p '333333' ssh -o StrictHostKeyChecking=no -p 33 root@192.168.68.98
```

## node38 (192.168.68.99)

8x RTX 3090, NVIDIA驱动550.90.07, CUDA 12.1.1。SSH端口33，密码333333。另有InfiniBand接口ib0(172.16.68.99)。

容器ID: `6f951280249de1e5a74393914da49c2286273da538e91b52e979cf22ab25ed29`

### docker run 命令

注意：NFS挂载同node37，在容器启动后通过mount命令挂载。

```bash
docker run -d \
--privileged \
--cap-add=ALL \
--ipc=host \
--network host \
--hostname node38.atp \
--name node38_zyb \
-v /data/zyb/software:/software \
--runtime=nvidia \
-ti \
nvcr.io/nvidia/cuda:12.1.1-devel-ubuntu22.04
```

### 容器内NFS挂载命令

```bash
# NAS 192.168.68.73 挂载（比node37少了 /home/user/anaconda3 和 /mnt/nfs_project）
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/zyb/code /code
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/public /data/public
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/zyb/root/.bashrc /root/.bashrc
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/zyb/root/.cache /root/.cache
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/zyb/root/.profile /root/.profile
mount -t nfs4 192.168.68.73:/nas/dg_data/nlp/zyb/root/anaconda3 /root/anaconda3
```

### SSH连接

```bash
sshpass -p '333333' ssh -o StrictHostKeyChecking=no -p 33 root@192.168.68.99
```

## 说明

- **镜像名称** `nvcr.io/nvidia/cuda:12.1.1-devel-ubuntu22.04` 为推断值（基于容器内 CUDA 12.1.1 + Ubuntu 22.04.3 + devel包），实际镜像名称需在宿主机上通过 `docker inspect` 确认
- **容器名称** `node37_zyb` / `node38_zyb` 为推断值，实际名称需在宿主机确认
- node37 比 node38 多两个NFS挂载：`/home/user/anaconda3` 和 `/mnt/nfs_project`
- node38 有 InfiniBand 接口（ib0: 172.16.68.99），node37 无