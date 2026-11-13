# 弹窗视觉小说 · 安卓版

把你电脑上的 `youxi.py`（剧情）+ `play.py`（战斗）做成了可以在安卓手机上玩的 APK 工程。

- 剧情 22 个场景原样保留（在 `game_data.py`，从 `youxi.py` 自动抽取）
- 战斗逻辑与 `play.py` 完全一致（防御/护盾/治疗三种随机能力）
- 界面从 tkinter 改成了 Kivy —— **因为安卓上没有 tkinter**，这是唯一能进 APK 的方式
- 中文字体内置（NotoSansSC.ttf），任何手机上都不会显示方框

## 文件说明

| 文件 | 作用 |
|---|---|
| `main.py` | Kivy 版游戏（剧情页 + 战斗页），手机和电脑通用 |
| `game_data.py` | 剧情数据（自动生成，别手改） |
| `sync_scenes.py` | 改完 `youxi.py` 的剧情后跑一下，重新生成 game_data.py |
| `buildozer.spec` | 安卓打包配置 |
| `.github/workflows/build-apk.yml` | 云端自动打包脚本 |
| `icon.png` | 应用图标 |
| `dev/` | 本地测试用的辅助脚本，可忽略 |

## 一、电脑上先试玩（可选，1 分钟）

```bat
"C:\Users\10384\AppData\Local\Programs\Python\Python311\python.exe" main.py
```

（Kivy 已装好；点正文跳过打字动画，1/2/3 选选项，Esc 退出）

## 二、打出 APK（云端构建，本机不需要装任何东西）

> 为什么不能在你电脑上直接打包？安卓打包工具链（Android SDK/NDK +
> python-for-android）只支持 Linux/macOS；你的电脑 WSL 被安全策略禁止运行，
> 微软的下载站 dl.google.com 也连不通。所以用 GitHub 的免费云端电脑来打包。

1. 注册 / 登录 [github.com](https://github.com)
2. 右上角 **+** → **New repository** → 随便起名（如 `popup-novel`）→ 勾 **Private** → Create
3. 仓库页面点 **uploading an existing file**，把本文件夹里**全部内容**拖进去
   （包括 `.github` 文件夹！它藏在文件夹里，记得打开"显示隐藏文件"或直接压缩成 zip 后在网页解压也可以）
   → **Commit changes**
4. 仓库顶部 **Actions** 标签 → 第一次会问是否启用 → 点 **I understand... enable**
5. 等 **20~40 分钟**（第一次最慢，要下载安卓 SDK；之后有缓存，10 分钟左右）
6. 点进那次运行 → 页面底部 **Artifacts** → 下载 **apk**
7. 解压出 `.apk` 传到手机（微信文件传输助手/QQ 均可），点开安装
   （手机会提示"未知来源应用"，允许即可）

以后每次改了剧情：本地跑 `sync_scenes.py` → 重新上传改动的文件 → Actions 自动出新 APK。

## 三、改剧情去哪里改

- **改 youxi.py 的 SCENES**（原桌面版），然后运行：
  ```bat
  "C:\Users\10384\AppData\Local\Programs\Python\Python311\python.exe" sync_scenes.py
  ```
- `pvp` 选项不用再写 `"pvp": "play.py"`，在手机版里只要选项带 `pvp` 键就会
  自动进入内置战斗页并按胜负跳 `win` / `lose` / `abort` 场景，写法完全兼容：
  ```python
  {"label": "认真打", "pvp": "play.py", "win": "win", "lose": "lose", "abort": "pvp"}
  ```

## 四、常见问题

- **APK 装不上**：确认手机是 Android 7.0+；`armeabi-v7a` 和 `arm64-v8a` 都已编译，主流手机都覆盖
- **Actions 构建失败**：进那次运行看红叉步骤的日志，最后 40 行已经截在日志里
- **想改应用名字/图标**：改 `buildozer.spec` 的 `title`，或替换 `icon.png`（512×512）
