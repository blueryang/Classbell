# ClassBell

基于 [ServerChan](https://sct.ftqq.com) 的课表微信提醒工具：每天晚上自动把**第二天**的课程推送到微信，再也不用临睡前翻教务系统查课表。

推送内容只包含三项：上课节次、课程名称、教室。没有课的日子会推送一条“明日无课”。

## 功能

- 按学期第一天自动推算教学周，支持每门课单独设置上课周次（如单双周、只上前 8 周）
- 消息标题即包含全部课程信息（ServerChan 免费版在微信里只展示卡片标题，这样不用点开就能看全）
- 纯 Python 3 标准库，零依赖，Python 3.9+ 即可运行
- 两种部署方式：自己的服务器/VPS 用 cron，或 GitHub Actions 免费定时运行

## 快速开始

### 1. 准备 ServerChan SendKey

到 [ServerChan](https://sct.ftqq.com) 登录，在「发送消息」页面拿到你的 SendKey（形如 `SCTxxxxxxxx`）。

### 2. 填写课表

把示例课表复制为 `schedule.json`，按你的真实课表修改：

```bash
cp schedule.example.json schedule.json
```

课表格式说明：

| 字段 | 说明 |
| --- | --- |
| `semester_start` | 学期第一天（第一教学周的周一），`YYYY-MM-DD` |
| `max_week` | 本学期总周数 |
| `days` | 键是星期几：`"1"`=周一 … `"7"`=周日 |
| `course` | 课程名称 |
| `periods` | 节次文本，如 `第1-2节`，原样显示在消息里 |
| `room` | 教室 |
| `weeks` | 这门课实际上课的教学周列表 |

### 3. 运行

```bash
export SERVERCHAN_SENDKEY=你的SendKey
python3 classbell.py            # 推送明天的课
python3 classbell.py --dry-run  # 只打印消息，不发送（先用这个自测）
```

可选参数：`--schedule 路径` 指定课表文件，`--for-date YYYY-MM-DD` 把某天当作“今天”测试，`--tz 时区` 默认 `Asia/Shanghai`。

## 部署

### 方式一：服务器 cron

每个有课的晚上 20:00 推送次日课程（周日到周四晚运行即可，周五、周六晚可跳过）：

```cron
0 20 * * 0-4  cd /path/to/classbell && SERVERCHAN_SENDKEY=你的SendKey python3 classbell.py >> classbell.log 2>&1
```

### 方式二：GitHub Actions（免服务器）

1. 把本仓库 fork 或克隆到你自己的账号
2. 在仓库 Settings → Secrets and variables → Actions 里添加 Secret：`SERVERCHAN_SENDKEY`
3. 把你的课表提交为仓库里的 `schedule.json`（注意：公开仓库里课表人人可见，在意隐私请用私有仓库）
4. 仓库自带的 [reminder workflow](.github/workflows/reminder.yml) 默认只开启了手动触发（workflow_dispatch）。想让它在北京时间每天 20:00（周日到周四）自动运行，把 workflow 里的 `on:` 改成：

```yaml
on:
  schedule:
    - cron: "0 12 * * 0-4"   # UTC 12:00 = 北京时间 20:00
  workflow_dispatch:
```

## 注意事项

- ServerChan 免费版每天有推送条数上限，课程提醒每天一条，足够用
- SendKey 是敏感信息：只通过环境变量或 GitHub Secrets 传入，不要写进代码或提交到仓库（`.gitignore` 已默认排除 `schedule.json` 与 `.env`，但 SendKey 请勿写进课表文件）
- 寒暑假或调休期间不想推送，停掉 cron / 禁用 workflow 即可

## 协议

[MIT](LICENSE)
