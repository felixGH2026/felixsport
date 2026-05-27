# FelixSport APK 编译指南

## 方法一：使用 GitHub Actions（推荐，免费）

1. 在 GitHub 创建一个新仓库（如 felixsport）
2. 将 felixsport 目录下所有文件上传到仓库
3. 在仓库根目录创建 `.github/workflows/build.yml` 文件（内容见下方）
4. 推送代码后，GitHub Actions 会自动编译 APK
5. 编译完成后，在 Actions 页面下载 APK 文件

### .github/workflows/build.yml 内容：

```yaml
name: Build APK
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build with Buildozer
        uses: ArtemSBulgakov/buildozer-action@v1
        id: buildozer
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: FelixSport
          path: ${{ steps.buildozer.outputs.filename }}
```

## 方法二：使用 Google Colab（免费，无需安装）

1. 打开 https://colab.research.google.com/
2. 新建一个笔记本
3. 运行以下代码：

```python
!pip install buildozer
!pip install cython
# 上传项目文件
from google.colab import files
uploaded = files.upload()  # 上传 main.py 和 buildozer.spec
import os
os.makedirs('felixsport', exist_ok=True)
# 将上传的文件移动到项目目录
!buildozer android debug
# 下载 APK
from google.colab import files
files.download('bin/felixsport-1.0.0-arm64-v8a-debug.apk')
```

## 方法三：安装 WSL 后本地编译

1. 以管理员身份打开 PowerShell
2. 运行 `wsl --install`
3. 重启电脑
4. 进入 WSL Ubuntu
5. 运行以下命令：

```bash
sudo apt update
sudo apt install -y python3-pip openjdk-17-jdk
pip3 install buildozer cython
cd /mnt/c/Users/felix/felixsport
buildozer android debug
```

编译完成后 APK 文件在 `bin/` 目录下。
