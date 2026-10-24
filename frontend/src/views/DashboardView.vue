<script setup>
import { onMounted, ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { ArrowUpRight, ArrowDownLeft, Plus, Users, ReceiptText, ArrowRight, Sparkles, TrendingUp, CircleDollarSign } from 'lucide-vue-next'
import { get, money } from '../services/api'
import ExpenseModal from '../components/ExpenseModal.vue'
const data = ref({total_expenses:0,group_count:0,groups:[],recent_expenses:[],by_category:[]})
const loading = ref(true), error = ref(''), modal = ref(false)
const groups = computed(() => data.value.groups || [])
async function load(){ loading.value=true; try { data.value=await get('/dashboard'); error.value=''} catch(e){error.value=e.message} finally{loading.value=false} }
async function seed(){try{await (await import('../services/api')).post('/demo/seed',{});await load()}catch(e){error.value=e.message}}
onMounted(load)
</script>
<template>
  <div class="page-stack">
    <section class="welcome-banner"><div class="welcome-content"><div class="welcome-chip"><Sparkles :size="14" /> YOUR MONEY, IN SYNC</div><h2>Good spending starts<br/>with <span>good clarity.</span></h2><p>All your shared expenses, balances, and settlements — in one calm place.</p><div class="welcome-actions"><button class="btn btn-light" @click="modal=true"><Plus :size="17"/> Add an expense</button><RouterLink to="/groups" class="banner-link">Explore groups <ArrowRight :size="16"/></RouterLink></div></div><div class="banner-art"><div class="art-orbit orbit-one"></div><div class="art-orbit orbit-two"></div><div class="art-card"><div class="art-card-top"><span>GROUP SPENDING</span><CircleDollarSign :size="18"/></div><div class="art-amount">{{ money(data.total_expenses) }}</div><div class="art-change"><TrendingUp :size="14"/> Live from your groups</div><div class="art-bars"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div><div class="floating-pill"><span class="status-dot"></span> Every share accounted for</div></div></section>
    <p v-if="error" class="alert alert-error">{{ error }}. Make sure the FastAPI backend is running.</p>
    <div class="section-heading"><div><h2>Your overview</h2><p>A quick look at your shared spending.</p></div><span class="muted-label">ALL GROUPS</span></div>
    <div class="stats-grid">
      <article class="stat-card stat-main"><div class="stat-top"><span>Total expenses</span><span class="stat-icon green"><ReceiptText :size="18"/></span></div><div class="stat-value">{{ loading ? '—' : money(data.total_expenses) }}</div><div class="stat-foot"><span class="tiny-dot green-dot"></span> Across all your groups</div></article>
      <article class="stat-card"><div class="stat-top"><span>Active groups</span><span class="stat-icon blue"><Users :size="18"/></span></div><div class="stat-value">{{ loading ? '—' : data.group_count }}</div><div class="stat-foot">Shared spaces you manage</div></article>
      <article class="stat-card"><div class="stat-top"><span>Expenses logged</span><span class="stat-icon violet"><CircleDollarSign :size="18"/></span></div><div class="stat-value">{{ loading ? '—' : data.recent_expenses.length }}</div><div class="stat-foot">Recent transactions shown</div></article>
      <article class="stat-card"><div class="stat-top"><span>Balance engine</span><span class="stat-icon amber"><ArrowLeftRightIcon/></span></div><div class="stat-value stat-text">Ready to settle</div><div class="stat-foot"><RouterLink to="/balances">View repayment plan →</RouterLink></div></article>
    </div>
    <div class="content-grid">
      <section class="panel"><div class="panel-heading"><div><h3>Recent expenses</h3><p>Latest activity from your groups.</p></div><RouterLink class="text-link" to="/expenses">View all <ArrowUpRight :size="15"/></RouterLink></div>
        <div v-if="loading" class="empty-state">Loading your transactions…</div>
        <div v-else-if="!data.recent_expenses.length" class="empty-state"><div class="empty-icon"><ReceiptText :size="23"/></div><strong>No expenses yet</strong><p>Add your first shared expense to get started.</p><button class="btn btn-primary btn-small" @click="modal=true"><Plus :size="15"/> Add expense</button><button class="text-button" @click="seed">Or load a demo group</button></div>
        <div v-else class="expense-table"><div v-for="e in data.recent_expenses.slice(0,6)" :key="e.id" class="expense-row"><div class="expense-symbol" :class="'cat-'+e.category"><ReceiptText :size="17"/></div><div class="expense-info"><strong>{{ e.title }}</strong><span>{{ e.group_name }} · {{ e.payer_name }} paid</span></div><div class="expense-amount"><strong>{{ money(e.amount) }}</strong><span>{{ e.expense_date }}</span></div></div></div>
      </section>
      <section class="panel"><div class="panel-heading"><div><h3>Your groups</h3><p>Places where expenses come together.</p></div><RouterLink class="text-link" to="/groups">See all <ArrowUpRight :size="15"/></RouterLink></div>
        <div v-if="!groups.length && !loading" class="empty-state compact"><div class="empty-icon"><Users :size="23"/></div><strong>No groups created</strong><p>Create a group or load demo data.</p><RouterLink to="/groups" class="btn btn-primary btn-small">Create a group</RouterLink><button class="text-button" @click="seed">Load demo group</button></div>
        <div v-else class="group-list"><RouterLink v-for="(g,i) in groups.slice(0,4)" :key="g.id" to="/balances" class="group-row"><div class="group-avatar" :class="'avatar-'+(i%4)">{{ g.name.slice(0,1).toUpperCase() }}</div><div class="group-info"><strong>{{ g.name }}</strong><span>{{ g.members.length }} members · {{ g.expense_count }} expenses</span></div><div class="group-total"><strong>{{ money(g.total_expenses) }}</strong><span>total spend</span></div><ArrowRight :size="16" class="row-arrow"/></RouterLink></div>
        <RouterLink v-if="groups.length" to="/groups" class="panel-bottom-link">Manage groups <ArrowRight :size="15"/></RouterLink>
      </section>
    </div>
    <section class="insight-strip"><div class="insight-icon"><Sparkles :size="19"/></div><div><strong>Make every rupee make sense.</strong><p>SplitFlow calculates fair shares and turns complicated group debts into a simple settlement plan.</p></div><RouterLink to="/balances" class="btn btn-secondary btn-small">See how it works <ArrowRight :size="15"/></RouterLink></section>
    <ExpenseModal :open="modal" :groups="groups" @close="modal=false" @saved="load"/>
  </div>
</template>
<script>
import { ArrowLeftRight as ArrowLeftRightIcon } from 'lucide-vue-next'
export default { components: { ArrowLeftRightIcon } }
</script>
