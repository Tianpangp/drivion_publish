# 设备发布管理系统

一个现代化的设备发布与管理平台，用于管理厂区、线体、工位，以及驱动包和 AutoUnit 包的上传与绑定。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **TypeScript** - JavaScript 的超集，提供类型安全
- **Tailwind CSS 4** - 实用优先的 CSS 框架
- **Ant Design Vue** - 企业级 UI 组件库
- **Vue Router** - 官方路由管理器
- **Pinia** - 新一代状态管理库
- **Vue i18n** - 国际化插件

## 功能特性

### 1. 用户认证
- 登录/登出功能
- 角色权限管理（管理员/普通用户）
- 会话持久化

### 2. 设施管理
- 厂区、线体、工位的层级结构管理
- 创建、编辑、删除操作
- 树形展示与搜索功能

### 3. 驱动包管理
- 支持 Java、Python、C++ 三种类型驱动
- 文件上传（.zip、.tar.gz、.dll）
- 驱动与工位绑定
- 版本管理

### 4. AutoUnit 包管理
- Python 包上传与管理
- 包结构自动校验
- 依赖项展示
- 工位关联

### 5. 界面管理
- 创建和管理界面
- 界面与工位绑定
- 预览功能
- 发布/草稿状态管理

### 6. 操作日志
- 完整的审计日志
- 操作筛选与搜索
- 详细的变更记录
- 日志导出功能

### 7. 国际化
- 中英文切换
- 完整的多语言支持

## 项目结构

```
publish-ui/
├── src/
│   ├── assets/          # 静态资源
│   ├── components/      # 可复用组件
│   ├── i18n/           # 国际化配置
│   │   ├── index.ts
│   │   └── locales/
│   │       ├── zh-CN.ts
│   │       └── en-US.ts
│   ├── layouts/        # 布局组件
│   │   └── MainLayout.vue
│   ├── router/         # 路由配置
│   │   └── index.ts
│   ├── stores/         # 状态管理
│   │   └── user.ts
│   ├── views/          # 页面组件
│   │   ├── Login.vue
│   │   ├── Facilities.vue
│   │   ├── Drivers.vue
│   │   ├── AutoUnit.vue
│   │   ├── Interfaces.vue
│   │   └── Logs.vue
│   ├── App.vue         # 根组件
│   ├── main.ts         # 入口文件
│   ├── main.css        # Tailwind CSS
│   └── style.css       # 全局样式
├── public/             # 公共资源
├── index.html          # HTML 模板
├── package.json        # 项目依赖
├── tsconfig.json       # TypeScript 配置
├── vite.config.ts      # Vite 配置
└── README.md          # 项目说明
```

## 快速开始

### 安装依赖

\`\`\`bash
npm install
\`\`\`

### 开发模式

\`\`\`bash
npm run dev
\`\`\`

访问 http://localhost:5173

### 构建生产版本

\`\`\`bash
npm run build
\`\`\`

### 预览生产版本

\`\`\`bash
npm run preview
\`\`\`

## 登录测试

系统提供以下测试账号：

- 管理员账号：`admin` / `admin`
- 普通用户：`user` / `user`

## 设计特点

### 1. 现代化 UI
- 简约的设计风格
- 流畅的动画效果
- 响应式布局，支持多种设备

### 2. 用户体验
- 直观的操作流程
- 清晰的视觉层级
- 友好的交互反馈

### 3. 功能完整
- 完整的 CRUD 操作
- 数据校验
- 错误处理
- 加载状态

### 4. 可扩展性
- 模块化设计
- 组件复用
- 类型安全
- 易于维护

## 开发说明

### 状态管理

使用 Pinia 进行状态管理，目前实现了用户状态管理：

\`\`\`typescript
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
userStore.login(username, password)
userStore.logout()
\`\`\`

### 路由守卫

路由已配置认证守卫，未登录用户会被重定向到登录页：

\`\`\`typescript
// src/router/index.ts
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  // 认证逻辑...
})
\`\`\`

### 国际化

使用 Vue i18n 实现多语言支持：

\`\`\`typescript
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
locale.value = 'zh-CN' // 或 'en-US'
\`\`\`

### API 集成

当前使用模拟数据，实际项目中需要：

1. 创建 API 服务层（如 `src/api/`）
2. 使用 axios 或 fetch 调用后端接口
3. 更新各页面组件中的数据获取逻辑

示例：

\`\`\`typescript
// src/api/facilities.ts
export async function getFacilities() {
  const response = await fetch('/api/facilities')
  return response.json()
}
\`\`\`

## 后续改进建议

1. **API 集成**
   - 连接实际后端 API
   - 实现数据持久化
   - 添加请求拦截器

2. **权限管理**
   - 细粒度权限控制
   - 按钮级权限
   - 数据权限

3. **性能优化**
   - 懒加载组件
   - 虚拟滚动
   - 缓存策略

4. **测试**
   - 单元测试
   - 集成测试
   - E2E 测试

5. **功能增强**
   - 文件预览
   - 批量操作
   - 高级搜索
   - 数据可视化

## 浏览器支持

- Chrome (推荐)
- Firefox
- Safari
- Edge

## License

MIT

## 联系方式

如有问题或建议，请联系开发团队。