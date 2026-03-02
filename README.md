# 汕头市澄海区溪南东社造纸厂开放学习平台

技术支持：南京市夜鹭云人工智能科技有限公司

## 项目简介

这是一个基于 Flask 框架开发的企业内部视频学习平台，支持视频分类管理、在线播放B站视频，以及完整的后台管理功能。

## 技术栈

- 后端：Python 3.x + Flask
- 数据库：SQLite
- 前端：HTML5 + Bootstrap 5 + Jinja2

## 项目结构

```
video_learning_platform/
├── app.py                          # 主程序文件
├── requirements.txt                # Python依赖包
├── learning_platform.db            # SQLite数据库（运行后自动生成）
└── templates/                      # 模板文件夹
    ├── base.html                   # 基础模板
    ├── index.html                  # 首页
    ├── category.html               # 分类页面
    ├── play.html                   # 视频播放页面
    ├── admin_login.html            # 管理员登录页面
    └── admin_dashboard.html        # 管理后台页面
```

## 功能特性

### 前台功能
- 首页展示所有学习分类
- 分类页面展示该分类下的所有视频（卡片布局）
- 视频播放页面（嵌入B站播放器）
- 响应式设计，支持移动端访问

### 后台管理
- 管理员登录验证
- 分类管理（添加、删除）
- 视频管理（添加、编辑、删除）
- 自动处理B站链接转换为嵌入式播放器

## 安装和运行

### 1. 安装依赖

```bash
cd video_learning_platform
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python app.py
```

程序会自动：
- 创建数据库和表结构
- 创建默认管理员账号

### 3. 访问系统

- 前台首页：http://localhost:5000
- 管理后台：http://localhost:5000/admin/login

### 默认管理员账号
- 用户名：`admin`
- 密码：`admin123`

## 使用说明

### 添加视频
1. 登录管理后台
2. 先添加分类（如：安全培训、技术学习等）
3. 点击"添加新视频"
4. 填写视频信息：
   - 标题：视频名称
   - 分类：选择所属分类
   - B站链接：支持以下格式
     - 完整链接：https://www.bilibili.com/video/BV1xx411c7mD
     - BV号：BV1xx411c7mD
     - av号：av12345678
   - 封面图片：输入图片URL（可选）
   - 视频介绍：详细描述（可选）

### B站视频链接说明
系统会自动将B站链接转换为嵌入式播放器，支持：
- 标准链接
- 短链接（b23.tv）
- BV号
- av号

## 注意事项

1. 本系统使用简单的密码存储方式，仅供演示使用
2. 生产环境建议：
   - 修改 `app.secret_key`
   - 使用密码加密（如 bcrypt）
   - 配置 HTTPS
   - 使用更强大的数据库（如 PostgreSQL）
3. 删除分类前需先删除该分类下的所有视频

## 开发者信息

技术开发：南京市夜鹭云人工智能科技有限公司
