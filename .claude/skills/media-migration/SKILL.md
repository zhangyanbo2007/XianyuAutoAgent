---
name: media-migration
description: 跨机器照片/视频迁移技能 — 扫描、去重、传输、验证、清理全流程。支持 Linux↔Windows 跨平台传输，自动处理编码问题，传输前必须验证完整性。
---

# Media Migration — 跨机器照片/视频迁移

将个人照片/视频在多台机器间迁移，支持 Linux↔Windows 跨平台。

## 核心原则

1. **先扫后传** — 完整扫描源机器所有媒体目录，列出清单
2. **先传后删** — 所有传输验证完成后才删除源文件
3. **先验后删** — 删除前必须核对文件数量/大小完全匹配
4. **按源分目录** — 目标机器按来源机器建子目录，后续再按年月重组

## 流程

### Phase 1: 扫描

分别扫描每台机器的个人媒体目录，生成清单。

**Linux (home-computer-ubuntu):**
```bash
# 照片
find /home/xiaowangzi/ -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.bmp" -o -iname "*.gif" -o -iname "*.webp" -o -iname "*.heic" -o -iname "*.tif" -o -iname "*.tiff" \) -not -path "*/.git/*" -not -path "*/node_modules/*" -not -path "*/Program Files/*" 2>/dev/null | wc -l

# 视频
find /home/xiaowangzi/ -type f \( -iname "*.mp4" -o -iname "*.avi" -o -iname "*.mkv" -o -iname "*.mov" -o -iname "*.wmv" -o -iname "*.flv" -o -iname "*.3gp" -o -iname "*.webm" -o -iname "*.m4v" \) -not -path "*/.git/*" -not -path "*/node_modules/*" 2>/dev/null | wc -l
```

**Windows (mobile-computer):**
```powershell
# 照片
$exts = @("*.jpg","*.jpeg","*.png","*.bmp","*.gif","*.webp","*.heic","*.tif","*.tiff")
Get-ChildItem -Path "D:\","E:\" -Recurse -File -Include $exts -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count

# 视频
$exts = @("*.mp4","*.avi","*.mkv","*.mov","*.wmv","*.flv","*.3gp","*.webm","*.m4v")
Get-ChildItem -Path "D:\","E:\" -Recurse -File -Include $exts -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
```

**排除目录列表（按需调整）：**
- Program Files, Program Files (x86)
- .git, node_modules
- jre, JDK 等运行时目录
- 课程/教程视频（非个人媒体）
- 游戏资源目录

### Phase 2: 规划传输方向

| 机器角色 | 存储内容 | 目标目录 |
|---|---|---|
| 照片主机 | 所有照片 | D:\PhotosAll\ 或 /home/.../PhotosAll/ |
| 视频主机 | 所有视频 | VideosAll/ 或 D:\VideosAll\ |

**按来源建子目录：**
```
PhotosAll/
├── dcim_from_phone/        # 来自手机DCIM
├── wechat_from_hcu/        # 来自home-computer的微信
├── redmi_from_hcu/         # 来自home-computer的红米备份
└── ...
```

### Phase 3: 传输

#### 方案选择

| 场景 | 方法 | 适用 |
|---|---|---|
| Linux→Linux | rsync -avz | 首选，支持断点续传 |
| Linux→Windows | SCP (LC_ALL=en_US.UTF-8) | 文件名无冒号时 |
| Linux→Windows | Python zipfile → SCP → PowerShell Expand-Archive | 文件名有冒号或SCP卡住时 |
| Windows→Linux | SCP | 直接传 |

#### SCP 传输（推荐）

```bash
# Linux → Windows (通过局域网)
LC_ALL=en_US.UTF-8 sshpass -p <password> scp -o StrictHostKeyChecking=no \
  -o ServerAliveInterval=10 -o ServerAliveCountMax=5 \
  -r /path/to/source zhangyanbo@192.168.3.182:D:/PhotosAll/target_dir

# Windows → Linux
sshpass -p <password> scp -o StrictHostKeyChecking=no \
  -o ServerAliveInterval=10 -o ServerAliveCountMax=5 \
  -r zhangyanbo@192.168.3.182:D:/DCIM /path/to/target/
```

**关键参数：**
- `LC_ALL=en_US.UTF-8` — 解决中文目录名乱码
- `-o ServerAliveInterval=10` — 防止大文件传输超时断开
- `-o ServerAliveCountMax=5` — 允许5次心跳失败
- `-r` — 递归传输目录

#### ZIP 方案（备用）

当 SCP 因文件名含冒号(:)卡住时：

```bash
# 1. Linux 上创建 ZIP（只打包照片，排除视频）
python3 -c "
import zipfile, os
photo_exts = {'.jpg','.jpeg','.png','.bmp','.gif','.webp','.heic','.tif','.tiff'}
with zipfile.ZipFile('/tmp/photos.zip', 'w', zipfile.ZIP_STORED) as zf:
    for root, dirs, files in os.walk('/path/to/source'):
        for f in files:
            if os.path.splitext(f)[1].lower() in photo_exts and ':' not in f:
                zf.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), '/path/to/source'))
"

# 2. SCP ZIP 文件到目标机器
scp /tmp/photos.zip user@target:/tmp/

# 3. Windows 上解压
Expand-Archive -Path C:\tmp\photos.zip -DestinationPath D:\PhotosAll\target
```

#### 跳板机模式

当目标机器不在同一网段时，通过跳板机连接：

```bash
# 通过 walle 跳板机
ssh -J zhangyanbo@192.168.28.92 xiaowangzi@192.168.3.67

# 通过 walle + sshpass
sshpass -p <password> ssh -J zhangyanbo@192.168.28.92 xiaowangzi@100.106.111.110
```

### Phase 4: 验证

传输完成后，必须逐项核对：

```bash
# Linux 端验证
find /path/to/target -type f \( -iname "*.jpg" -o -iname "*.png" \) | wc -l

# Windows 端验证
powershell -Command "(Get-ChildItem -Path 'D:\PhotosAll' -Recurse -File -Include '*.jpg','*.png').Count"
```

**验证清单：**
- [ ] 源文件数量 = 目标文件数量（按类型分别统计）
- [ ] 无遗漏目录
- [ ] 无冒号文件名导致的传输失败
- [ ] 无编码乱码的目录名

### Phase 5: 清理

验证通过后删除源文件：

```bash
# Linux
rm -rf /path/to/source_dir

# Windows
Remove-Item -Path "D:\source_dir" -Recurse -Force
```

**删除前必须确认：**
1. 目标机器文件数量 = 源机器文件数量
2. 已排除程序资源目录（不是个人媒体）
3. 用户明确确认删除

## 常见问题

### SCP 中文目录名乱码
**原因：** Windows SSH 默认使用 GBK 编码
**解决：** 传输前设置 `LC_ALL=en_US.UTF-8`

### SCP 文件名含冒号(:)卡住
**原因：** 冒号在 Windows 文件系统中无效
**解决：** 用 ZIP 方案，打包时排除含冒号的文件

### 大文件传输超时
**原因：** 默认 SSH 心跳间隔太长
**解决：** 加 `-o ServerAliveInterval=10 -o ServerAliveCountMax=5`

### 并行 SCP 连接被拒绝
**原因：** 目标机器 SSH 限制并发连接数
**解决：** 串行传输，一次只跑一个 SCP

### Windows PowerShell 中文乱码
**原因：** PowerShell 默认编码不是 UTF-8
**解决：** 脚本开头加 `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`

## 实战案例

### 案例：两台家庭电脑媒体迁移

**环境：**
- home-computer-ubuntu (192.168.3.67 / Tailscale 100.106.111.110) — Linux
- mobile-computer (192.168.3.182 / Tailscale 100.87.67.119) — Windows
- 跳板机: walle (192.168.28.92)

**迁移结果：**
- 视频: 3040个 → home-computer-ubuntu (VideosAll/)
- 照片: 16,755张 → mobile-computer (D:\PhotosAll\)

**传输统计：**
| 目录 | 文件数 | 大小 | 方向 |
|---|---|---|---|
| 行车记录仪 | 1482 | 106GB | MC→HCU |
| DCIM视频 | 742 | 142GB | MC→HCU |
| 手机备份视频 | 376 | 173GB | MC→HCU |
| xwechat视频 | 818 | 15GB | MC→HCU |
| 旧桌面照片 | 708 | 7.4GB | HCU→MC |
| 照片目录 | 5836 | 9.6GB | HCU→MC |
| ... | ... | ... | ... |
