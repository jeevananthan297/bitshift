<script setup>
import { computed, ref, watch } from 'vue'
import { X, ReceiptText } from 'lucide-vue-next'
import { get, post, put, money } from '../services/api'
const props = defineProps({ open: Boolean, groups: { type: Array, default: () => [] }, initial: { type: Object, default: null } })
const emit = defineEmits(['close','saved'])
const groupId = ref('')
const title = ref('')
const amount = ref('')
const category = ref('food')
const payerId = ref('')
const participantIds = ref([])
const method = ref('equal')
const values = ref({})
const expenseDate = ref(new Date().toISOString().slice(0,10))
const description = ref('')
const error = ref('')
const busy = ref(false)
const currentGroup = computed(() => props.groups.find(g => String(g.id) === String(groupId.value)))
const preview = computed(() => {
  const ids = participantIds.value
  const total = Math.round(Number(amount.value || 0) * 100)
  if (!ids.length || !Number.isFinite(total) || total < 0) return []
  let amounts = []
  if (method.value === 'exact') amounts = ids.map(id => Math.round(Number(values.value[id] || 0) * 100))
  else {
    const weights = ids.map(id => method.value === 'equal' ? 1 : Number(values.value[id] || 0))
    const sum = weights.reduce((a,b)=>a+b,0)
    amounts = sum > 0 ? weights.map(w => Math.floor(total * w / sum)) : ids.map(()=>0)
    let rem = total - amounts.reduce((a,b)=>a+b,0)
    for (let i=0; i<rem; i++) amounts[i % amounts.length]++
  }
  return ids.map((id,i)=>({id, name:currentGroup.value?.members.find(m=>m.id===id)?.name || 'Member', amount: amounts[i]/100}))
})
watch(() => props.open, async open => {
  if (!open) return
  error.value = ''
  const first = props.groups[0]
  groupId.value = props.initial?.group_id || first?.id || ''
  title.value = props.initial?.title || ''
  amount.value = props.initial?.amount || ''
  category.value = props.initial?.category || 'food'
  payerId.value = props.initial?.payer_id || first?.members?.[0]?.id || ''
  participantIds.value = props.initial?.shares?.map(s=>s.member_id) || first?.members?.map(m=>m.id) || []
  method.value = props.initial?.split_method || 'equal'
  values.value = {}
  if (props.initial?.shares) props.initial.shares.forEach(s=>values.value[s.member_id] = s.amount)
  expenseDate.value = props.initial?.expense_date || new Date().toISOString().slice(0,10)
  description.value = props.initial?.description || ''
})
watch(groupId, () => {
  const g = currentGroup.value
  if (g && !g.members.some(m=>String(m.id)===String(payerId.value))) payerId.value = g.members[0]?.id || ''
  if (g) participantIds.value = g.members.map(m=>m.id)
})
watch(method, () => { if (currentGroup.value) values.value = Object.fromEntries(currentGroup.value.members.map(m=>[m.id, method.value==='percentage' ? 100/currentGroup.value.members.length : method.value==='shares' ? 1 : 0])) })
async function submit() {
  error.value = ''
  if (!title.value.trim() || !Number(amount.value) || Number(amount.value) <= 0) { error.value = 'Enter an expense title and a positive amount.'; return }
  if (!participantIds.value.length) { error.value = 'Select at least one participant.'; return }
  let participants = participantIds.value.map(id=>({member_id:id, value: method.value==='equal' ? 1 : Number(values.value[id] || 0)}))
  if (method.value === 'exact' && Math.round(participants.reduce((s,p)=>s+p.value,0)*100) !== Math.round(Number(amount.value)*100)) { error.value = 'Exact shares must equal the total amount.'; return }
  if (method.value === 'percentage' && Math.abs(participants.reduce((s,p)=>s+p.value,0)-100) > 0.01) { error.value = 'Percentages must add up to 100%.'; return }
  busy.value = true
  try {
    const payload = { group_id:Number(groupId.value), title:title.value.trim(), amount:Number(amount.value), category:category.value, payer_id:Number(payerId.value), expense_date:expenseDate.value, description:description.value, split_method:method.value, participants }
    if (props.initial?.id) await put(`/expenses/${props.initial.id}`, payload)
    else await post('/expenses', payload)
    emit('saved'); emit('close')
  } catch(e) { error.value = e.message } finally { busy.value = false }
}
</script>
<template>
  <div v-if="open" class="modal-backdrop" @click.self="emit('close')">
    <section class="modal expense-modal">
      <div class="modal-head"><div class="modal-title-icon"><ReceiptText :size="20" /></div><div><h2>{{ initial ? 'Edit expense' : 'Add an expense' }}</h2><p>Record a shared cost and split it fairly.</p></div><button class="icon-btn" @click="emit('close')"><X :size="19" /></button></div>
      <form @submit.prevent="submit" class="modal-body">
        <label>Expense name<input v-model="title" required placeholder="e.g. Dinner at the beach" /></label>
        <div class="form-row"><label>Amount (₹)<input v-model="amount" type="number" min="0.01" step="0.01" required placeholder="0.00" /></label><label>Category<select v-model="category"><option v-for="c in ['food','travel','accommodation','groceries','entertainment','utilities','shopping','other']" :key="c">{{ c }}</option></select></label></div>
        <div class="form-row"><label>Group<select v-model="groupId" required><option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option></select></label><label>Paid by<select v-model="payerId" required><option v-for="m in currentGroup?.members || []" :key="m.id" :value="m.id">{{ m.name }}</option></select></label></div>
        <div class="form-row"><label>Date<input v-model="expenseDate" type="date" required /></label><label>Split method<select v-model="method"><option value="equal">Equal split</option><option value="exact">Exact amounts</option><option value="percentage">Percentages</option><option value="shares">Weighted shares</option></select></label></div>
        <div class="participant-heading"><div><strong>Who shared this?</strong><p>Choose the members included in this expense.</p></div><button type="button" class="text-button" @click="participantIds = participantIds.length === (currentGroup?.members.length || 0) ? [] : (currentGroup?.members || []).map(m=>m.id)">{{ participantIds.length === (currentGroup?.members.length || 0) ? 'Clear all' : 'Select all' }}</button></div>
        <div class="participant-list"><label v-for="m in currentGroup?.members || []" :key="m.id" class="participant-row"><input type="checkbox" :value="m.id" v-model="participantIds" /><span class="mini-avatar">{{ m.name.slice(0,1).toUpperCase() }}</span><span class="participant-name">{{ m.name }}</span><input v-if="method !== 'equal' && participantIds.includes(m.id)" class="share-input" type="number" min="0" :step="method === 'percentage' ? '0.01' : '0.01'" v-model.number="values[m.id]" :placeholder="method === 'percentage' ? '%' : method === 'shares' ? 'shares' : '₹'" /><span v-else-if="participantIds.includes(m.id)" class="share-value">{{ money(preview.find(p=>p.id===m.id)?.amount || 0) }}</span></label></div>
        <div class="split-summary"><span>Preview total</span><strong>{{ money(preview.reduce((s,p)=>s+p.amount,0)) }}</strong><small>{{ participantIds.length }} participant{{ participantIds.length===1?'':'s' }}</small></div>
        <label>Note (optional)<textarea v-model="description" rows="2" placeholder="Add context for your group…" /></label>
        <p v-if="error" class="form-error">{{ error }}</p>
        <div class="modal-actions"><button type="button" class="btn btn-secondary" @click="emit('close')">Cancel</button><button class="btn btn-primary" :disabled="busy">{{ busy ? 'Saving…' : initial ? 'Save changes' : 'Save expense' }}</button></div>
      </form>
    </section>
  </div>
</template>
