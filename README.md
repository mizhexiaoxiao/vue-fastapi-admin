# vue-fastapi-admin
基于FastAPI + Vue3 + Naive UI的现代化前后端分离开发平台，融合了RBAC权限管理、动态路由和JWT鉴权，助力中小型应用快速搭建。

### 登录页

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/login.jpg)
### 工作台

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/workbench.jpg)

### 用户管理

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/user.jpg)
### 角色管理

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/role.jpg)

### 菜单管理

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/menu.jpg)

### API管理

![image](https://github.com/mizhexiaoxiao/vue-fastapi-admin/blob/main/deploy/sample-picture/api.jpg)

### 快速开始
#### 方法一：dockerhub拉取镜像

```sh
docker pull mizhexiaoxiao/vue-fastapi-admin:latest 
docker run -d --restart=always --name=vue-fastapi-admin -p 9999:80 mizhexiaoxiao/vue-fastapi-admin
```

#### 方法二：dockerfile构建镜像
##### docker安装(版本17.05+)

```sh
yum install -y docker-ce
systemctl start docker
```

##### 构建镜像

```sh
git clone https://github.com/mizhexiaoxiao/vue-fastapi-admin.git
cd vue-fastapi-admin
docker build --no-cache . -t vue-fastapi-admin
```

##### 启动容器

```sh
docker run -d --restart=always --name=vue-fastapi-admin -p 9999:80 vue-fastapi-admin
```

### 访问

浏览器打开http://localhost:9999

username：admin

password：123456