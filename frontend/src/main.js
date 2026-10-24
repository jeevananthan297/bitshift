import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'
const routes = [
  { path: '/', component: () => import('./views/DashboardView.vue') },
  { path: '/groups', component: () => import('./views/GroupsView.vue') },
  { path: '/expenses', component: () => import('./views/ExpensesView.vue') },
  { path: '/balances', component: () => import('./views/BalancesView.vue') },
  { path: '/analytics', component: () => import('./views/AnalyticsView.vue') },
]
const router = createRouter({ history: createWebHistory(), routes })
createApp(App).use(router).mount('#app')
