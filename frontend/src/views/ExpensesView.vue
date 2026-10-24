<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, Search, Download, ReceiptText, Trash2, Pencil, Filter } from 'lucide-vue-next'
import { get, del, money } from '../services/api'
import ExpenseModal from '../components/ExpenseModal.vue'
const groups=ref([]), expenses=ref([]), loading=ref(true), error=ref(''), query=ref(''), groupFilter=ref('all'), categoryFilter=ref('all'), modal=ref(false), editing=ref(null)
const filtered=computed(()=>expenses.value.filter(e=>(groupFilter.value==='all'||String(e.group_id)===String(groupFilter.value))&&(categoryFilter.value==='all'||e.category===categoryFilter.value)&&(`${e.title} ${e.payer_name} ${e.category}`.toLowerCase().includes(query.value.toLowerCase()))))
async function load(){loading.value=true;try{[groups.value,expenses.value]=await Promise.all([get('/groups'),get('/expenses')]);error.value=''}catch(e){error.value=e.message}finally{loading.value=false}}
function edit(e){editing.value=e;modal.value=true}
async function remove(e){if(!confirm(`Delete "${e.title}"? Balances will be recalculated.`))return;try{await del(`/expenses/${e.id}`);await load()}catch(e){error.value=e.message}}
function exportCsv(){window.open(`${import.meta.env.VITE_API_BASE_URL||'http://127.0.0.1:8000/api'}/expenses/export.csv${groupFilter.value==='all'?'':`?group_id=${groupFilter.value}`}`,'_blank')}
onMounted(load)
</script>
<template>
  <div class="page-stack">
    <section class="page-intro"><div><div class="eyebrow">TRANSACTION LEDGER</div><h2>Every rupee, accounted for.</h2><p>One clear record of what was spent, who paid, and how it was shared.</p></div><button class="btn btn-primary" @click="editing=null;modal=true" :disabled="!groups.length"><Plus :size="17"/> Add expense</button></section>
    <p v-if="error" class="alert alert-error">{{ error }}. Check that the backend is running.</p>
    <section class="panel">
      <div class="toolbar"><div class="search-box"><Search :size="17"/><input v-model="query" placeholder="Search expenses, people, categories…"/></div><div class="filter-set"><select v-model="groupFilter"><option value="all">All groups</option><option v-for="g in groups" :key="g.id" :value="String(g.id)">{{ g.name }}</option></select><select v-model="categoryFilter"><option value="all">All categories</option><option v-for="c in ['food','travel','accommodation','groceries','entertainment','utilities','shopping','other']" :key="c">{{ c }}</option></select><button class="btn btn-secondary btn-small" @click="exportCsv"><Download :size="15"/> Export CSV</button></div></div>
      <div v-if="loading" class="empty-state">Loading expenses…</div>
      <div v-else-if="!filtered.length" class="empty-state"><div class="empty-icon"><ReceiptText :size="24"/></div><strong>{{ expenses.length?'No matching expenses':'Nothing on the ledger yet' }}</strong><p>{{ expenses.length?'Try adjusting your filters.':'Add an expense to begin tracking shared spending.' }}</p><button v-if="groups.length" class="btn btn-primary btn-small" @click="editing=null;modal=true"><Plus :size="15"/> Add expense</button><RouterLink v-else to="/groups" class="btn btn-primary btn-small">Create a group first</RouterLink></div>
      <div v-else class="ledger"><div class="ledger-head"><span>EXPENSE</span><span>GROUP / PAID BY</span><span>DATE</span><span>AMOUNT</span><span>ACTIONS</span></div><div v-for="e in filtered" :key="e.id" class="ledger-row"><div class="ledger-title"><span class="expense-symbol" :class="'cat-'+e.category"><ReceiptText :size="16"/></span><div><strong>{{ e.title }}</strong><span class="category-pill">{{ e.category }}</span></div></div><div class="ledger-group"><strong>{{ groups.find(g=>g.id===e.group_id)?.name || 'Group' }}</strong><span>{{ e.payer_name }} paid</span></div><div class="ledger-date">{{ e.expense_date }}</div><div class="ledger-amount">{{ money(e.amount) }}</div><div class="ledger-actions"><button class="icon-btn" @click="edit(e)" title="Edit"><Pencil :size="16"/></button><button class="icon-btn danger-hover" @click="remove(e)" title="Delete"><Trash2 :size="16"/></button></div></div></div>
      <div class="ledger-footer"><span>Showing <strong>{{ filtered.length }}</strong> of {{ expenses.length }} expenses</span><span>Total shown <strong>{{ money(filtered.reduce((s,e)=>s+e.amount,0)) }}</strong></span></div>
    </section>
    <ExpenseModal :open="modal" :groups="groups" :initial="editing" @close="modal=false;editing=null" @saved="load"/>
  </div>
</template>
