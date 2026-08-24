# VinShop 电商商城

> 前后端分离的全栈电商系统。后端基于 Django REST Framework，前端基于 Vue 3 + Element Plus SPA，涵盖用户认证、商品管理、全文搜索、购物车、订单、支付、评价等完整业务链路，注重高并发场景下的数据一致性与系统可靠性。

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.2-green?logo=django)
![DRF](https://img.shields.io/badge/DRF-3.17-red)
![Redis](https://img.shields.io/badge/Redis-8.0-red?logo=redis)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-9.x-yellow?logo=elasticsearch)
![Celery](https://img.shields.io/badge/Celery-5.6-brightgreen?logo=celery)
![MySQL](https://img.shields.io/badge/MySQL-8.0-blue?logo=mysql)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![Vue.js](https://img.shields.io/badge/Vue-3.4-green?logo=vue.js)
![Vite](https://img.shields.io/badge/Vite-5.4-purple?logo=vite)
![Element Plus](https://img.shields.io/badge/ElementPlus-2.4-blue)
![Pinia](https://img.shields.io/badge/Pinia-2.2-yellow)

---

## 项目简介

VinShop 是一个独立设计并实现的电商后端系统，采用前后端分离架构。后端基于 **Django 5.2 + Django REST Framework**，使用 **JWT** 进行无状态认证，**Redis** 作为高速缓存与多种业务数据的存储引擎，**Elasticsearch** 提供中文全文搜索能力，**Celery + RabbitMQ** 处理异步任务与定时调度，**FastDFS** 实现分布式文件存储，**支付宝开放平台** 完成在线支付闭环。

项目重点解决电商场景下的几个核心后端问题：**高并发下单防超卖**（分布式锁 + 乐观锁）、**接口幂等性**（Redis SET NX）、**订单超时自动处理**（Redis ZSET + Celery）、**支付回调容错**（双通道 + 幂等退款）等。

---

## 技术架构

| 层级 | 技术选型 |
|------|---------|
| Web 框架 | Django 5.2 + Django REST Framework 3.17 |
| 认证方案 | JWT（SimpleJWT）双 Token 机制 |
| 数据库 | MySQL 8.0 |
| 缓存/存储 | Redis 8.0（6 个 DB 分库隔离） |
| 搜索引擎 | Elasticsearch 9.x + IK 中文分词 |
| 消息队列 | RabbitMQ + Celery 5.6 |
| 文件存储 | FastDFS 分布式文件系统 |
| 短信服务 | 容联云 SMS SDK |
| 支付 | 支付宝开放平台（沙箱环境） |
| 模板引擎 | Jinja2（静态页面预渲染） |
| 部署 | uWSGI + Nginx + Docker Compose |

前端详见下方「前端架构」章节。

---

## 前端架构

### 技术选型

| 层级 | 技术选型 |
|------|---------|
| 框架 | Vue 3.4（Composition API + `<script setup>`） |
| 构建工具 | Vite 5.4 |
| UI 组件库 | Element Plus 2.4 + @element-plus/icons-vue |
| 状态管理 | Pinia 2.2 |
| 路由 | Vue Router 4.4（History 模式） |
| HTTP 客户端 | Axios 1.7（JWT 拦截器 + 自动刷新） |

### 项目结构

```
frontend/
├── index.html                     # SPA 入口
├── package.json                   # 依赖管理
├── vite.config.js                 # Vite 配置 + /api 代理
├── scripts/sync-template.js       # 构建后同步 Jinja2 模板资源路径
├── src/
│   ├── main.js                    # Vue 应用初始化
│   ├── App.vue                    # 根组件（Header + RouterView + Footer）
│   ├── api/                       # API 层（7 个模块）
│   │   ├── request.js             # Axios 实例 + JWT 拦截器
│   │   ├── user.js                # 用户/认证/地址/区域
│   │   ├── goods.js               # 商品/分类/搜索
│   │   ├── cart.js                # 购物车 CRUD
│   │   ├── order.js               # 订单结算/提交/列表/详情
│   │   ├── browse.js              # 浏览记录
│   │   └── comment.js             # 评价上传/创建
│   ├── stores/                    # Pinia 状态管理
│   │   ├── user.js                # Token 管理 + 登录/注册/登出
│   │   └── cart.js                # 购物车数量徽标
│   ├── router/index.js            # 13 条路由 + 鉴权守卫
│   ├── components/                # 可复用组件
│   │   ├── AppHeader.vue          # 顶部导航栏
│   │   ├── AppFooter.vue          # 页脚
│   │   ├── GoodsCard.vue          # 商品卡片
│   │   └── ImageCarousel.vue      # 图片轮播 + 放大镜
│   └── views/                     # 页面视图（13 个）
│       ├── Home.vue               # 首页
│       ├── Search.vue             # 搜索结果页
│       ├── Login.vue              # 登录
│       ├── Register.vue           # 注册
│       ├── Detail.vue             # 商品详情
│       ├── Cart.vue               # 购物车
│       ├── Settlement.vue         # 订单结算
│       ├── OrderList.vue          # 订单列表
│       ├── OrderDetail.vue        # 订单详情
│       ├── Payment.vue            # 支付页
│       ├── PaymentResult.vue      # 支付结果
│       ├── Comment.vue            # 商品评价
│       └── UserCenter.vue         # 用户中心
```

### 核心架构设计

**JWT 双 Token 认证流程**

```
登录/注册 → 后端返回 Access Token (15min) + Refresh Token (1d)
          → localStorage 持久化
          → 请求拦截器自动注入 Authorization: Bearer <access_token>
          → 401 响应拦截器自动用 Refresh Token 换取新 Token
          → Token 失效 → 跳转登录页，携带回调路径
```

**请求拦截器链**

```
Axios 请求 → [请求拦截器] 注入 JWT Token
           → 后端处理
           → [响应拦截器] 成功: 直接返回
                       → 失败: 401 → 尝试 Token 刷新 → 重试原请求
                             → 非 401 → ElMessage.error 提示
```

**路由鉴权守卫**

```
路由跳转 → beforeEach 守卫
        → 检查 meta.requiresAuth
        → 需要登录但无 Token → 重定向到 /login?next=原路径
        → 允许通过
```

### API 层与后端接口映射

| API 模块 | 文件 | 对应后端模块 | 主要接口 |
|----------|------|-------------|---------|
| user.js | 用户 API | users, verifications, areas | 登录、注册、资料、地址 CRUD、短信验证、邮箱绑定、改密 |
| goods.js | 商品 API | goods, search | 首页分类、推荐商品、SKU 详情、ES 搜索 |
| cart.js | 购物车 API | carts | 获取/添加/修改/删除/全选/单品选中/批量删除 |
| order.js | 订单 API | orders, payment | 结算页、提交订单、订单列表/详情、确认收货、支付宝 URL |
| browse.js | 浏览记录 API | browse | 获取/添加/删除/清空浏览记录 |
| comment.js | 评价 API | comments | 文件上传、创建评价 |

### 路由体系

| 路径 | 页面 | 鉴权 | 功能 |
|------|------|------|------|
| `/` | Home | 否 | 首页：分类侧边栏 + 轮播图 + 推荐商品 |
| `/search` | Search | 否 | 搜索结果页：关键词高亮 + 排序 + 价格筛选 |
| `/login` | Login | 否 | 登录表单 |
| `/register` | Register | 否 | 注册表单（含图形/短信验证码） |
| `/detail/:id` | Detail | 否 | SKU 详情：图片轮播 + 规格选择 + 加入购物车 |
| `/cart` | Cart | 是 | 购物车管理：数量修改 + 选中切换 + 批量删除 |
| `/settlement` | Settlement | 是 | 订单结算：地址选择 + 商品确认 + 提交订单 |
| `/orders` | OrderList | 是 | 订单列表：状态筛选 + 分页 |
| `/orders/:id` | OrderDetail | 是 | 订单详情：状态时间线 + 物流信息 |
| `/comment/:orderId/:orderGoodsId` | Comment | 是 | 商品评价：评分 + 文字 + 图片/视频上传 |
| `/payment/:orderId` | Payment | 是 | 支付页：支付宝支付链接 + 状态轮询 |
| `/payment/result` | PaymentResult | 否 | 支付结果展示 |
| `/user` | UserCenter | 是 | 用户中心：资料编辑 + 地址管理 + 安全设置 |

### 可复用组件

| 组件 | 功能 | 使用场景 |
|------|------|---------|
| `AppHeader.vue` | 顶部导航栏：Logo、搜索框、购物车徽标、登录/注册/退出 | 全局布局 |
| `AppFooter.vue` | 页脚：版权信息 | 全局布局 |
| `GoodsCard.vue` | 商品卡片：图片、名称、价格、评论数、销量、搜索高亮 | 首页推荐、搜索结果 |
| `ImageCarousel.vue` | 图片轮播 + 放大镜效果 + 缩略图切换 | 商品详情页 |

### 状态管理（Pinia）

| Store | 状态 | 方法 | 说明 |
|-------|------|------|------|
| `useUserStore` | token, refreshToken, userInfo | login, register, fetchProfile, logout, setToken, clearToken | JWT Token 持久化 + 用户信息 |
| `useCartStore` | cartCount | fetchCartCount, setCount | 购物车数量徽标（全局 Header 展示） |

### 开发与构建

```bash
cd frontend
npm install          # 安装依赖
npm run dev          # 启动开发服务器 http://localhost:5173
npm run build        # 构建生产版本
npm run preview      # 预览构建结果
npm run sync         # 同步构建产物到 Jinja2 模板（自动 postbuild）
```

**Vite 开发代理**：`/api` 请求代理至 `http://127.0.0.1:8000`，前后端同域避免 CORS 问题。

**构建同步脚本**：`npm run build` 后自动执行 `scripts/sync-template.js`，从 `dist/index.html` 提取带 hash 的 CSS/JS 资源路径，更新 `VinShop/templates/index.jinja2` 中的引用，确保静态页预渲染使用最新的前端资源。

---

## 后端核心模块

### 1. 用户模块（users）

| 功能 | 实现方案 |
|------|---------|
| 用户注册 | 自定义 User 模型扩展手机号字段，事务内创建 User + UserProfile |
| JWT 登录 | SimpleJWT 返回 Access Token（15min）+ Refresh Token（1d） |
| 个人资料 | 头像上传至 FastDFS，昵称/性别/生日管理 |
| 地址管理 | 省市区三级联动（Area 自关联树），默认地址 FK，上限 20 条 |
| 敏感操作门控 | 手机换绑/邮箱绑定/改密前需通过短信验证，Redis 标记 `sms_passed_{user_id}`（10min TTL） |

### 2. 验证码模块（verifications）

- **图形验证码**：PIL 生成 120x40 像素图片，4 位随机字符（排除 O/I/0/1），干扰线 + 噪点，Base64 返回
- **短信验证码**：容联云 SDK 异步发送，Redis 存储（300s 有效期），60s 防刷限流
- **一次性消费**：验证码使用后立即从 Redis 删除，防止重放

### 3. 商品模块（goods）

- **三级分类体系**：GoodsCategory 自关联树（分类 → 频道 → 品牌）
- **SPU/SKU 模型**：SPU 定义抽象商品，SKU 为具体可购买规格组合（SPUSpec → SpecOption → SKUSpec）
- **首页频道与广告**：GoodsChannelGroup 管理导航频道，ContentCategory 管理轮播图/广告位
- **Django Signal 自动同步**：SKU/SPU 的 post_save/post_delete 信号触发 Celery 任务，异步更新 ES 索引和静态详情页

### 4. 搜索模块（search）

- **Elasticsearch 索引**：SKU 文档包含 name、spu_name、brand_name、category_1/2/3（ik_max_word 分词）、price、sales、comments
- **多字段检索**：multi_match 查询 6 个字段，支持关键词高亮
- **过滤与排序**：价格区间过滤（分转换为整数）、销量/评论数/价格排序
- **异步索引同步**：Celery 任务在 SKU 变更后立即更新 ES，refresh=True 保证实时性

### 5. 购物车模块（carts）

纯 Redis 存储，无数据库模型：

- **数据结构**：Hash `cart_{user_id}` 存储 `{sku_id: count}`，Set `cart_selected_{user_id}` 存储选中状态
- **Pipeline 原子操作**：添加/修改/删除均使用 Redis Pipeline 保证原子性
- **库存校验**：添加时校验已有数量 + 新增数量 ≤ SKU 库存
- **下单扣减**：订单创建成功后调用 `consume_cart()` 原子扣减已购商品

### 6. 订单模块（orders）

核心难点：高并发下的数据一致性。

| 机制 | 实现 |
|------|------|
| 分布式锁 | Redis 锁，按 SKU ID 排序获取（防死锁），30s TTL + 5s 阻塞等待 |
| 乐观锁 | `filter(stock__gte=count).update(stock=F('stock')-count)`，条件更新，库存不足自动失败 |
| 幂等性 | Redis `SET NX` + client_token（60s TTL），防止网络重试重复下单 |
| 运费计算 | 满 69 元免运费，否则 10 元 |
| 订单 ID | 时间戳 `YYYYMMDDHHMMSSffffff` + 9 位用户 ID |
| 超时取消 | Redis ZSET 存储过期时间，Celery Countdown 延迟取消 + Beat 每分钟扫描兜底 |

### 7. 支付模块（payment）

- **支付宝集成**：RSA2 签名，`alipay.trade.page.pay` 生成支付链接
- **双通道回调**：异步通知（notify）+ 主动查询（query）双通道保证支付状态同步
- **过期订单处理**：支付到达时订单已过期/已取消 → 自动调用 `alipay.trade.refund` 退款，幂等处理避免重复退款
- **Payment 模型**：记录支付宝交易号、退款状态、退款时间

### 8. 评价模块（comments）

- **媒体上传**：图片（JPEG/PNG/WebP，≤5MB）/ 视频（MP4，≤100MB）上传至 FastDFS
- **文件追踪**：Redis ZSET 存储已上传文件的过期时间戳，Celery Beat 每日凌晨 3:30 清理未认领的孤儿文件
- **事务安全**：创建评价时 `select_for_update()` 锁定 OrderInfo 和 OrderGoods，防止并发重复评价
- **订单状态推进**：当订单所有商品均已评价，自动将状态从"待评价"推进为"已完成"

### 9. 浏览记录模块（browse）

- Redis ZSET 存储，score 为时间戳，自动按时间倒序
- 7 天自动过期 + 单用户最多 200 条裁剪
- 按天分组返回前端

### 10. 首页静态化（static_index / static_detail）

- **首页**：Celery Beat 每 3 分钟生成 `static/pages/index.html`（Jinja2 渲染分类、频道、广告数据）
- **详情页**：SKU 变更时 Celery 异步生成 `static/pages/detail/{sku_id}.html`（预注入完整 SKU 数据）
- **SEO 优化**：服务端预渲染 HTML + 客户端 Vue Hydration，兼顾搜索引擎抓取和首屏性能

---

## 技术亮点与难点

### 1. Redis 多业务隔离

6 个 Redis DB 分离不同业务：

| DB | 用途 | 数据结构 |
|----|------|---------|
| 0 | 默认缓存 | String（省市区数据等） |
| 1 | 验证码 | String（图形码、短信码、防刷标记） |
| 2 | 浏览记录 | ZSET（score=时间戳） |
| 3 | 购物车 | Hash + Set |
| 4 | 订单 | ZSET（过期排序）+ String（分布式锁、幂等键） |
| 5 | 文件追踪 | ZSET（score=过期时间戳） |

### 2. 高并发下单防超卖

```
请求到达 → 幂等性校验（Redis SET NX）
         → 获取分布式锁（按 SKU ID 排序，防死锁）
         → 乐观锁扣减库存（stock__gte 条件更新）
         → 创建订单 + 扣减购物车
         → 释放锁
```

分布式锁 + 乐观锁双保险，即使锁失效，乐观锁的条件更新也能防止超卖。

### 3. 订单超时自动取消

```
下单成功 → Redis ZSET 记录 expire_ts
         → Celery.apply_async(countdown=1800) 延迟 30 分钟取消
         → Celery Beat 每分钟扫描 ZSET，兜底处理漏网订单
         → cancel_unpaid_order() 事务内回滚库存/销量
```

延迟任务 + 定时扫描双重保障，确保超时订单一定被处理。

### 4. 支付回调容错

```
支付宝异步通知 → 签名校验 → 检查订单状态
                                  ├─ 未过期未支付 → 创建 Payment，更新订单状态
                                  ├─ 已过期未支付 → 创建 Payment → 调用退款 API → 标记已退款
                                  ├─ 订单已取消   → 创建 Payment → 调用退款 API → 标记已退款
                                  └─ 未支付       → 返回 paid=false

主动查询（前端轮询兜底）→ 同上逻辑
```

异步通知 + 主动查询双通道，已退款订单跳过退款（幂等），避免重复退款。

### 5. JWT 双 Token + 敏感操作门控

```
登录/注册 → 返回 Access Token (15min) + Refresh Token (1d)
          → 前端 401 时自动用 Refresh Token 换新 Access Token

敏感操作（改手机/改密/绑邮箱）:
  Step 1: 发送短信验证码 → Redis sms_passed_{user_id} = 1（10min TTL）
  Step 2: 验证通过后才允许修改
```

### 6. Celery 异步任务体系

7 类异步任务，覆盖短信、邮件、搜索同步、订单超时、静态页生成、文件清理：

```python
# celery_tasks/config.py
CELERY_BEAT_SCHEDULE = {
    'check_expired_orders':   crontab(minute='*'),        # 每分钟扫描过期订单
    'clean_comment_file':     crontab(hour=3, minute=30), # 每日凌晨清理孤儿文件
    'generate_static_index':  crontab(minute='*/3'),      # 每3分钟刷新首页静态页
}
```

### 7. Elasticsearch 全文搜索

- IK 中文分词器（ik_max_word 索引 + ik_smart 搜索）
- 6 字段 `multi_match`：name、spu_name、brand_name、category_1/2/3
- Django Signal 驱动异步索引同步（post_save → Celery → ES）
- 价格存储为分（整数），查询时前端传元，后端 ×100 转换

### 8. FastDFS 文件管理

自定义 Django Storage 后端：

```python
class FastDFSStorage(Storage):
    def _save(self, name, content):
        # 上传至 FastDFS，返回 file_id
    def url(self, name):
        # 拼接 FDFS_BASE_URL + file_id
```

评价模块额外使用 Redis ZSET 追踪已上传但未被认领的文件，Celery Beat 定期清理。

---

## 项目结构

```
VinShop/
├── VinShop/                  # Django 项目配置
│   ├── settings.py           # 全局配置（Redis/ES/邮件/支付宝/JWT等）
│   ├── urls.py               # API 路由汇总（统一 /api/ 前缀）
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/                # 用户：注册/登录/JWT/资料/地址/手机换绑/邮箱绑定/改密
│   ├── verifications/        # 验证码：图形码 + 短信码（无模型，纯 Redis）
│   ├── areas/                # 省市区三级数据（自关联树，Redis 缓存 24h）
│   ├── goods/                # 商品：分类/品牌/SPU/SKU/规格/频道/广告/ES 搜索
│   │   └── management/commands/
│   │       ├── rebuild_index.py      # 重建 ES 索引
│   │       └── generate_sku_static.py # 批量生成详情静态页
│   ├── browse/               # 浏览记录（无模型，纯 Redis ZSET）
│   ├── carts/                # 购物车（无模型，Redis Hash + Set）
│   ├── orders/               # 订单：结算/下单/列表/详情/确认收货
│   ├── payment/              # 支付：支付宝 URL/状态查询/异步通知
│   │   └── keys/             # RSA 密钥文件
│   └── comments/             # 评价：文件上传/创建/列表/统计
├── celery_tasks/
│   ├── main.py               # Celery 实例，自动发现 7 个任务模块
│   ├── config.py             # Broker（RabbitMQ）+ Beat Schedule
│   ├── sms/tasks.py          # 短信发送（容联云 SDK）
│   ├── email/tasks.py        # 邮件发送（Django SMTP）
│   ├── search/tasks.py       # ES 索引同步（update/delete）
│   ├── order/tasks.py        # 订单超时取消 + Beat 扫描
│   ├── comments/tasks.py     # 孤立文件清理（Beat 每日 3:30）
│   ├── static_index/tasks.py # 首页静态化（Beat 每 3 分钟）
│   └── static_detail/tasks.py # 详情页静态化
├── utils/
│   ├── models.py             # BaseModel 抽象类（create_time/update_time）
│   ├── alipay.py             # 支付宝 SDK 初始化 + 退款
│   ├── carts.py              # 购物车 Redis 操作封装
│   ├── browse.py             # 浏览记录 Redis 操作封装
│   ├── order.py              # 订单 ID 生成 / 分布式锁 / 超时工具
│   ├── captcha.py            # PIL 图形验证码生成
│   ├── storage.py            # FastDFS 自定义 Storage 后端
│   ├── es_util.py            # Elasticsearch 客户端单例
│   ├── recommend.py          # 热门商品推荐
│   └── default_nickname.py   # 随机默认昵称生成
├── templates/                # Jinja2 模板（index/detail 静态页）
├── static/pages/             # 生成的静态页面输出目录
├── docker-compose.yml        # Elasticsearch + FastDFS 编排
├── uwsgi.ini                 # uWSGI 生产部署配置
├── requirements.txt          # Python 依赖
└── .env                      # 环境变量（不入版本控制）
```

---

## 快速开始

### 环境要求

- Python 3.10+
- MySQL 8.0
- Redis 7.0+
- RabbitMQ 3.x
- Elasticsearch 9.x（需安装 IK 分词插件）
- FastDFS（tracker + storage）
- Node.js 18+（前端开发）

### 后端启动

```bash
# 1. 进入后端目录
cd VinShop

# 2. 创建虚拟环境并安装依赖
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env   # 或手动创建 .env，填入以下内容

# 4. 数据库迁移
python manage.py migrate

# 5. 创建超级管理员
python manage.py createsuperuser

# 6. 导入省市区数据（如有初始数据）
python manage.py shell < load_areas.py

# 7. 重建 ES 索引
python manage.py rebuild_index

# 8. 启动后端服务
python manage.py runserver
```

### 启动 Celery Worker + Beat

```bash
# 终端 1：Celery Worker
celery -A celery_tasks.main worker -l info

# 终端 2：Celery Beat（定时任务调度）
celery -A celery_tasks.main beat -l info
```

### 启动 Docker 服务（ES + FastDFS）

```bash
docker compose up -d
```

### .env 环境变量清单

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL
MYSQL_PASSWORD=your-mysql-password

# 容联云短信
RONGLIAN_ACC_ID=your-acc-id
RONGLIAN_ACC_TOKEN=your-acc-token
RONGLIAN_APP_ID=your-app-id

# QQ 邮箱 SMTP
EMAIL_HOST_USER=your-email@qq.com
EMAIL_HOST_PASSWORD=your-smtp-auth-code

# 支付宝沙箱
ALIPAY_APP_ID=your-alipay-app-id
ALIPAY_RETURN_URL=http://localhost:8080/payment/result/
ALIPAY_NOTIFY_URL=http://localhost:8000/api/payment/alipay/notify/
```

### 前端启动

```bash
# 1. 进入前端目录
cd ../frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
# 开发服务器 http://localhost:5173
# /api 请求自动代理至后端 http://127.0.0.1:8000
```

### 构建与部署

```bash
# 构建生产版本
npm run build

# 构建产物输出到 dist/ 目录，同时自动同步到 Jinja2 模板
# 可通过 Nginx 配置反向代理提供 SPA 访问
```

---

## API 接口概览

### 用户与认证

| URL | 方法 | 说明 | 认证 |
|-----|------|------|------|
| `/api/register/` | POST | 用户注册 | 否 |
| `/api/login/` | POST | 用户登录 | 否 |
| `/api/token/refresh/` | POST | 刷新 Access Token | 否 |
| `/api/profile/` | GET/PATCH | 获取/修改个人资料 | JWT |
| `/api/address/` | GET/POST | 地址列表/创建 | JWT |
| `/api/address/{id}/` | GET/PUT/DELETE | 地址详情/修改/删除 | JWT |
| `/api/center/sms/` | POST/PATCH | 发送/验证身份短信 | JWT |
| `/api/center/sms/change/` | POST/PATCH | 发送/验证换绑手机短信 | JWT |
| `/api/center/email/` | POST/PATCH | 发送/验证邮箱验证码 | JWT |
| `/api/center/psw/` | PATCH | 修改密码 | JWT |

### 验证码

| URL | 方法 | 说明 | 认证 |
|-----|------|------|------|
| `/api/image_code/` | POST | 获取图形验证码 | 否 |
| `/api/sms_code/` | POST | 发送短信验证码 | 否 |

### 商品与搜索

| URL | 方法 | 说明 | 认证 |
|-----|------|------|------|
| `/api/category/` | GET | 首页分类/频道/广告数据 | 否 |
| `/api/goods/recommend/` | GET | 热门推荐商品 | 否 |
| `/api/goods/{sku_id}/` | GET | SKU 详情（含规格矩阵） | 否 |
| `/api/search/` | GET | Elasticsearch 商品搜索 | 否 |
| `/api/areas/` | GET | 省份列表 | 否 |
| `/api/areas/{id}/` | GET | 子区域列表 | 否 |

### 购物车

| URL | 方法 | 说明 | 认证 |
|-----|------|------|------|
| `/api/cart/` | GET/POST | 获取购物车/添加商品 | JWT |
| `/api/cart/{sku_id}/` | PUT/DELETE | 修改数量/删除商品 | JWT |
| `/api/cart/selection/` | PUT | 全选/取消全选 | JWT |
| `/api/cart/selection/{sku_id}/` | PUT | 单品选中切换 | JWT |
| `/api/cart/selection/delete/` | DELETE | 批量删除已选商品 | JWT |

### 订单

| URL | 方法 | 说明 | 认证 |
|-----|------|------|------|
| `/api/order/settlement/` | GET | 订单结算页 | JWT |
| `/api/order/commit/` | POST | 提交订单 | JWT |
| `/api/orders/` | GET | 订单列表（分页+状态筛选） | JWT |
| `/api/orders/{order_id}/` | GET | 订单详情 | JWT |
| `/api/orders/{order_id}/confirm/` | POST | 确认收货 | JWT |

### 支付

| URL | 方法 | 说明 | 认证 |
|-----|------|------|------|
| `/api/payment/alipay/` | GET | 生成支付宝支付链接 | JWT |
| `/api/payment/alipay/status/` | GET | 查询支付状态 | JWT |
| `/api/payment/alipay/notify/` | POST | 支付宝异步通知回调 | 否 |

### 评价

| URL | 方法 | 说明 | 认证 |
|-----|------|------|------|
| `/api/comments/upload/` | POST | 上传评价图片/视频 | JWT |
| `/api/comments/` | POST | 创建评价 | JWT |
| `/api/goods/{sku_id}/comments/` | GET | 商品评价列表（分页+筛选） | 否 |

### 浏览记录

| URL | 方法 | 说明 | 认证 |
|-----|------|------|------|
| `/api/browse/` | GET/POST | 获取/添加浏览记录 | JWT |
| `/api/browse/{sku_id}/` | DELETE | 删除单条记录 | JWT |
| `/api/browse/` | DELETE | 清空浏览记录 | JWT |

---

## 部署方案

### uWSGI 配置

```ini
# uwsgi.ini
module = VinShop.wsgi:application
socket = 127.0.0.1:8001
master = true
processes = 4
buffer-size = 32768
limit-post = 104857600   # 100MB，支持文件上传
```

### Docker Compose 服务

```yaml
services:
  elasticsearch:   # 全文搜索引擎，IK 分词插件
  tracker:         # FastDFS tracker
  storage:         # FastDFS storage
```

### 生产环境启动命令

```bash
# uWSGI
uwsgi --ini uwsgi.ini

# Celery Worker（4 并发）
celery -A celery_tasks.main worker -l info --concurrency=4

# Celery Beat（定时任务）
celery -A celery_tasks.main beat -l info
```

---

## 写在最后

本项目是一个全栈电商系统，后端从零开始独立设计与实现，前端全程使用 AI 工具辅助开发，独立锻炼 AI 辅助开发能力，完美适配后端 40+ 接口。通过这个项目实践了以下核心能力：

- **RESTful API 设计**：9 个应用、40+ 个接口，统一规范的 URL 设计与响应格式
- **高并发数据一致性**：分布式锁、乐观锁、幂等性等机制的实际应用
- **异步任务架构**：Celery 生产者-消费者模式，7 类任务的合理拆分与调度
- **搜索引擎集成**：Elasticsearch 索引设计、IK 分词配置、信号驱动的增量同步
- **分布式系统基础**：FastDFS 文件存储、Redis 多业务隔离、消息队列解耦
- **支付系统集成**：支付宝全流程（下单→支付→回调→退款），异步通知容错处理
- **前端 AI 辅助开发**：Vue 3 + Element Plus SPA 全流程 AI 辅助开发，完美适配后端 40+ 接口
