[app]

title = FelixSport
package.name = felixsport
package.domain = org.felix
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0
requirements = python3,kivy,requests
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.api = 33
android.minapi = 26
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
android.skip_update = False
p4a.branch = develop
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
