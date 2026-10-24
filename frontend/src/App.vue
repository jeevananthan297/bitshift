<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { LayoutDashboard, Users, ReceiptText, ArrowLeftRight, ChartNoAxesCombined, Moon, Sun, Menu, X, WalletCards } from 'lucide-vue-next'
import { api } from './services/api'
const route = useRoute()
const dark = ref(false)
const mobileOpen = ref(false)
const apiOnline = ref(false)
const links = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/groups', label: 'My groups', icon: Users },
  { to: '/expenses', label: 'Expenses', icon: ReceiptText },
  { to: '/balances', label: 'Balances & settle', icon: ArrowLeftRight },
  { to: '/analytics', label: 'Insights', icon: ChartNoAxesCombined },
]
function toggleTheme() { dark.value = !dark.value; document.documentElement.dataset.theme = dark.value ? 'dark' : 'light' }
onMounted(async () => { try { await api('/health'); apiOnline.value = true } catch { apiOnline.value = false } })
</script>

<template>
  <div class="app-shell">
    <div class="mobile-top">
      <button class="icon-btn" @click="mobileOpen = !mobileOpen" :aria-label="mobileOpen ? 'Close menu' : 'Open menu'"><component :is="mobileOpen ? X : Menu" :size="20" /></button>
      <RouterLink to="/" class="brand"><span class="brand-mark"><WalletCards :size="21" /></span><span>split<span class="brand-accent">flow</span></span></RouterLink>
      <button class="icon-btn" @click="toggleTheme" aria-label="Toggle theme"><component :is="dark ? Sun : Moon" :size="18" /></button>
    </div>
    <aside class="sidebar" :class="{ 'mobile-open': mobileOpen }">
      <RouterLink to="/" class="brand side-brand"><span class="brand-mark"><WalletCards :size="21" /></span><span>split<span class="brand-accent">flow</span></span></RouterLink>
      <div class="workspace-label">WORKSPACE</div>
      <nav>
        <RouterLink v-for="item in links" :key="item.to" :to="item.to" class="nav-link" :class="{ active: route.path === item.to }" @click="mobileOpen = false">
          <component :is="item.icon" :size="18" :stroke-width="1.8" /><span>{{ item.label }}</span><span v-if="route.path === item.to" class="active-dot"></span>
        </RouterLink>
      </nav>
      <div class="sidebar-bottom">
        <div class="help-card"><div class="help-icon"><WalletCards :size="18" /></div><strong>Good spending starts here.</strong><p>Keep every shared expense clear and fair.</p><RouterLink to="/groups">Explore groups →</RouterLink></div>
        <div class="connection"><span class="status-dot" :class="{ offline: !apiOnline }"></span>{{ apiOnline ? 'API connected' : 'API unavailable' }}</div>
        <button class="theme-toggle" @click="toggleTheme"><component :is="dark ? Sun : Moon" :size="17" /><span>{{ dark ? 'Light appearance' : 'Dark appearance' }}</span></button>
      </div>
    </aside>
    <main class="main-area">
      <header class="topbar">
        <div><div class="eyebrow">PERSONAL FINANCE / SHARED SPENDING</div><h1>{{ links.find(l => l.to === route.path)?.label || 'Overview' }}</h1></div>
        <div class="top-actions"><span class="local-badge"><span class="status-dot"></span> Local workspace</span><button class="icon-btn desktop-theme" @click="toggleTheme" aria-label="Toggle theme"><component :is="dark ? Sun : Moon" :size="18" /></button><div class="avatar">SF</div></div>
      </header>
      <div class="page-content"><RouterView /></div>
      <footer class="footer"><span>© 2026 SplitFlow</span><span>Shared expenses, without the awkward math.</span></footer>
    </main>
    <button v-if="mobileOpen" class="mobile-scrim" @click="mobileOpen = false" aria-label="Close navigation"></button>
  </div>
</template>
