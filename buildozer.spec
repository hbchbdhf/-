[app]
# 应用名称（手机桌面上显示的名字）
title = 弹窗视觉小说

# 包名：装到手机上后的唯一标识，随意但别和别的应用冲突
package.name = PopupNovel
package.domain = org.liuxuanyu

source.dir = .
source.include_exts = py,png,ttf,otf

# 版本号，每次发新版记得 +1
version = 1.0.0

# 依赖：python-for-android 的 kivy 配方当前只认 2.3.1，不要乱改
requirements = python3,kivy==2.3.1

# 竖屏，不隐藏状态栏
orientation = portrait
fullscreen = 0

# 图标（打包时会自动缩放成各尺寸）
icon.filename = icon.png

#
# Android 配置
#
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

# 不需要任何权限（纯单机游戏）
# android.permissions =

# 构建时尽量精简
android.add_src =

[buildozer]
# 日志详细程度（云端构建看日志用）
log_level = 2
warn_on_root = 1

# 只构建 release 调试用 debug 包即可；apk 会出现在 bin/ 目录
# 构建命令： buildozer -v android debug
