[app]
title = AI Chatbot
package.name = aichatbot
package.domain = org.example
source.dir = .
source.main = main.py
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy==2.3.1,requests,certifi,urllib3,idna,charset_normalizer
orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
