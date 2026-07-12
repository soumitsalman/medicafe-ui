<script setup>
import { queueCases, canSendToOffice } from '~/utils/caseSelectors'
import { formatMaxShiftDate } from '~/utils/duration'

const {
  cases,
  loadQueue,
  updateCase,
  setMission,
  cancelCase,
  undoCase,
  reportIssue,
  sendToOffice
} = useCaseQueue()

const loading = ref(true)
const summaryOpen = ref(false)
const sendSummary = ref({
  billableCount: 0,
  billableMinutes: 0,
  missionCount: 0,
  missionMinutes: 0,
  cancelledCount: 0,
  issueCount: 0
})

async function loadCases() {
  loading.value = true
  await loadQueue()
  loading.value = false
}

await loadCases()

// TODO: remove this.
// #region agent log
watch([cases, loading], ([c, isLoading]) => {
  const q = queueCases(c)
  fetch('http://127.0.0.1:7691/ingest/ceab04ba-7a84-4b90-b033-dde09e0fe1c6',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c1863d'},body:JSON.stringify({sessionId:'c1863d',location:'ScheduleQueueView.vue:watch',message:'cases/loading changed',data:{casesCount:c.length,queueCount:q.length,loading:isLoading,importMetaServer:import.meta.server,importMetaClient:import.meta.client},timestamp:Date.now(),hypothesisId:'C,D'})}).catch(()=>{})
}, { immediate: true, deep: true })
// #endregion

const queue = computed(() => queueCases(cases.value))
const canSend = computed(() => canSendToOffice(cases.value))
const queueDateLabel = computed(() =>
  formatMaxShiftDate(queue.value.map(c => c.service_date))
)

function onUpdate(caseId, fields) {
  updateCase(caseId, fields)
}

function onMission(caseId, checked) {
  setMission(caseId, checked)
}

function onCancel(caseId) {
  cancelCase(caseId)
}

function onUndo(caseId) {
  undoCase(caseId)
}

function onIssue(caseId, payload) {
  reportIssue(caseId, payload)
}

async function onSendToOffice() {
  if (!canSend.value) return
  try {
    const result = await sendToOffice()
    sendSummary.value = result.summary
    summaryOpen.value = true
    await loadCases()
  } catch (err) {
    console.error('Send to office failed', err)
  }
}
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-headline-lg-mobile text-highlighted">
        {{ queueDateLabel ?? 'Schedule' }}
      </h1>
      <p class="mt-1 text-sm text-muted">
        {{ queue.length }} {{ queue.length === 1 ? 'case' : 'cases' }} in queue
      </p>
    </div>

    <div
      v-if="loading"
      class="space-y-4"
    >
      <USkeleton class="h-32 w-full rounded-[16px]" />
      <USkeleton class="h-32 w-full rounded-[16px]" />
      <USkeleton class="h-32 w-full rounded-[16px]" />
    </div>

    <template v-else>
      <div class="space-y-4">
        <CaseScheduleCard
          v-for="c in queue"
          :key="c.case_id"
          :case-item="c"
          @update="onUpdate"
          @mission="onMission"
          @cancel="onCancel"
          @undo="onUndo"
          @issue="onIssue"
        />
      </div>

      <div
        v-if="!queue.length"
        class="mt-16 flex flex-col items-center justify-center text-center opacity-60"
      >
        <UIcon
          name="i-lucide-check-circle"
          class="mb-4 size-16 opacity-40"
        />
        <p class="max-w-xs text-base text-muted">
          No cases in the queue.
        </p>
      </div>
    </template>

    <div
      v-if="queue.length"
      class="mt-4 flex justify-center"
    >
      <UButton
        icon="i-lucide-send"
        label="Send to Office"
        color="primary"
        size="xl"
        class="rounded-full"
        :disabled="!canSend"
        @click="onSendToOffice"
      />
    </div>

    <SendSummaryModal
      v-model:open="summaryOpen"
      :summary="sendSummary"
    />
  </div>
</template>
