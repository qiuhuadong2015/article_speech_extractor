# article_speech_extractor

## 后端部署

### STEP-1 创建并进入conda环境

```
conda create -n article_speech_extractor python=3.6
source activate article_speech_extractor
```

### STEP-2 pip安装依赖

```
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple uwsgi flask simplejson pandas flask_cors
```

- uwsgi
- flask
- simplejson
- pandas
- flask_cors

### STEP-3 安装pyltp

#### mac版本（已测试）

从https://pan.baidu.com/s/1QUeBt6oIJEfmH3u5vHlUdw下载pyltp_mac.zip到任意位置

解压得到pyltp文件夹

```shell
cd pyltp
python setup.py install
```

#### windows版本（未测试）

pyltp-0.2.1-cp36-cp36m-win_amd64.whl 来自网友分享

```
cd ltp_installer/windows64
python install pyltp-0.2.1-cp36-cp36m-win_amd64.whl
```

#### docker版本（未测试）

Dockerfile来自https://github.com/HIT-SCIR/ltp

```shell
cd ltp_docker
docker build -t ltp/ltp .
```

启动

```shell
docker run -d -p 8080:12345 ltp/ltp /ltp_server --last-stage all
```

测试

```shell
curl -d "s=姑姑说：我好想过过过儿过过的生活。&f=xml&t=all" http://127.0.0.1:8080/ltp
```

### STEP-4 下载LTP模型

下载链接

```
http://ltp.ai/download.html
```

mac、linux选择`ltp_data_v3.4.0.zip`

windows64位选择`ltp-3.4.0-win-x64-Release.zip`

解压到任意位置，修改main.py开头的代码为解压后文件夹路径

```python
# 根据下载模型存放位置修改
LTP_DATA_PATH = '/Users/qiuhuadong/ltp_data_v3.4.0'
```

### STEP-5 uWSGI运行python web服务

修改`uwsgi.ini`中的项目路径

```
chdir = 【article_speech_extractor项目路径】/webapp
socket = 【article_speech_extractor项目路径】/webapp/myproject.sock
logto = 【article_speech_extractor项目路径】/webapp/myproject.log
pidfile = 【article_speech_extractor项目路径】/webapp/uwsgi.pid
```

运行

```shell
cd webapp
uwsgi --ini uwsgi.ini
```

### STEP-6 浏览器访问

```
localhost:5000/api
```

web服务启动成功则显示

> hello api

### STEP-7 curl测试

```shell
curl -X POST --header "Content-Type: application/json" --header "Accept: application/json" -d "{
  \"article\": \"小明说今天天气真好！\"
}" "http://localhost:5000/api/get"
```

程序运行正常则显示

```json
{
  "result": [
    {
      "object": "今天天气真好！",
      "predicate": "说",
      "subject": "小明"
    }
  ]
}
```

## 前后端集成部署

TODO