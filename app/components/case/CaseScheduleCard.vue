<script setup>
import { debounce, formatDobWithAge } from '~/utils/duration'
import { deriveFromDx, dxOptions } from '~/utils/dxLookup'
import { isIssueStatus, statusDisplayFromCase } from '~/utils/caseSelectors'

const props = defineProps({
  caseItem: { type: Object, required: true }
})

const emit = defineEmits(['update', 'mission', 'cancel', 'undo', 'issue'])

const minutesInput = ref()
const dxValue = ref('')
const missionChecked = ref(false)
const noteInput = ref('')
const issueModalOpen = ref(false)

const dxItems = computed(() => dxOptions().map(dx => ({ value: dx, label: dx })))
const derivedCptEye = computed(() => deriveFromDx(dxValue.value))

const ISSUE_TYPE_LABELS = {
  identity_issue: 'Identity issue',
  needs_review: 'Needs review'
}

const isCancelled = computed(() => props.caseItem.status === 'cancelled')
const isIssue = computed(() => isIssueStatus(props.caseItem.status))
const statusDisplay = computed(() => statusDisplayFromCase(props.caseItem.status))

const issueSubStatusLabels = computed(() =>
  (props.caseItem.sub_status ?? []).map(type => ISSUE_TYPE_LABELS[type] ?? type)
)

const showCancel = computed(() =>
  (props.caseItem.minutes == null || props.caseItem.minutes > 0) && !isIssue.value
)
const showUndo = computed(() =>
  isCancelled.value || isIssue.value || props.caseItem.minutes === 0
)
const showReportIssue = computed(() =>
  !isCancelled.value && !isIssue.value
)
const showMission = computed(() =>
  !isCancelled.value && !isIssue.value
)
const showNoteRow = computed(() =>
  isIssue.value && (props.caseItem.note?.trim().length > 0)
)
const showMinutesConfirm = computed(() => {
  if (props.caseItem.status !== 'scheduled') return false
  const m = minutesInput.value ?? props.caseItem.minutes
  return Number.isInteger(m) && m > 0
})

const cardBorderClass = computed(() => {
  const { borderClass, opacityClass } = statusDisplay.value
  if (!borderClass) return {}
  return {
    'border-l-4': true,
    [borderClass]: true,
    [opacityClass]: !!opacityClass
  }
})

const cardUi = {
  body: 'px-3 py-2 flex flex-col gap-1',
  footer: 'px-3 py-2'
}

watch(
  () => props.caseItem,
  (c) => {
    minutesInput.value = c.minutes ?? undefined
    dxValue.value = c.dx
    missionChecked.value = c.mission ?? false
    noteInput.value = c.note ?? ''
  },
  { immediate: true, deep: true }
)

const debouncedUpdate = debounce((fields) => {
  emit('update', props.caseItem.case_id, fields)
}, 600)

function onMinutesChange(value) {
  if (value == null) {
    debouncedUpdate({ minutes: null })
  } else {
    debouncedUpdate({ minutes: value })
  }
}

function onConfirmBillable() {
  const minutes = minutesInput.value ?? props.caseItem.minutes
  if (!Number.isInteger(minutes) || minutes <= 0) return
  debouncedUpdate.cancel()
  emit('update', props.caseItem.case_id, { minutes })
}

function onDxChange(value) {
  dxValue.value = value
  debouncedUpdate({ dx: value })
}

function onMissionToggle(checked) {
  missionChecked.value = checked
  emit('mission', props.caseItem.case_id, checked)
}

function onNoteChange(value) {
  debouncedUpdate({ note: value ?? '' })
}

function onClearNote() {
  noteInput.value = ''
  debouncedUpdate({ note: '' })
}

function onCancel() {
  emit('cancel', props.caseItem.case_id)
}

function onUndo() {
  emit('undo', props.caseItem.case_id)
}

function onIssueClick() {
  issueModalOpen.value = true
}

function onIssueSubmit(payload) {
  emit('issue', props.caseItem.case_id, payload)
}
</script>

<template>
  <UCard
    class="rounded-2xl bg-default pill-shadow"
    :class="cardBorderClass"
    :ui="cardUi"
  >
    <div class="flex w-full items-center gap-1">
      <UIcon
        v-if="statusDisplay.icon"
        :name="statusDisplay.icon"
        class="shrink-0 size-5"
        :class="statusDisplay.textClass"
      />
      <UBadge
        :label="caseItem.patient_id"
        color="neutral"
        variant="subtle"
        class="shrink-0"
      />
      <span
        class="min-w-0 truncate text-headline-md"
        :class="statusDisplay.textClass"
      >
        {{ caseItem.patient_name }}
      </span>
      <span class="shrink-0 text-sm text-muted">
        {{ formatDobWithAge(caseItem.patient_dob, caseItem.service_date) }}
      </span>
      <div class="ml-auto flex shrink-0 items-center gap-2">
        <UButton
          v-if="showMinutesConfirm"
          icon="i-lucide-check"
          color="primary"
          variant="outline"
          size="xs"
          class="shrink-0 rounded-full"
          aria-label="Confirm billable"
          @click="onConfirmBillable"
        />
        <UInputNumber
          v-model.optional="minutesInput"
          placeholder="Min"
          :min="0"
          :max="59"
          class="w-32 shrink-0"
          @update:model-value="onMinutesChange"
        />
      </div>
      <span class="shrink-0 text-sm text-muted">mins</span>
    </div>

    <div class="flex w-full items-center gap-1">
      <USelect
        :model-value="dxValue"
        :items="dxItems"
        class="w-32"
        @update:model-value="onDxChange"
      />
      <UBadge
        :label="derivedCptEye.cpt"
        color="secondary"
        variant="soft"
      />
      <UBadge
        :label="derivedCptEye.eye"
        color="secondary"
        variant="outline"
      />
    </div>

    <div
      v-if="isIssue && issueSubStatusLabels.length"
      class="flex w-full flex-wrap gap-1"
    >
      <UBadge
        v-for="label in issueSubStatusLabels"
        :key="label"
        :label="label"
        color="warning"
        variant="soft"
      />
    </div>

    <div
      v-if="showNoteRow"
      class="flex w-full items-start gap-1"
    >
      <UInput
        v-model="noteInput"
        placeholder="Note"
        class="flex-1"
        :ui="{ trailing: 'pe-1' }"
        @update:model-value="onNoteChange"
      >
        <template #trailing>
          <UButton
            color="neutral"
            variant="link"
            size="sm"
            icon="i-lucide-x"
            aria-label="Clear note"
            @click="onClearNote"
          />
        </template>
      </UInput>
    </div>

    <template #footer>
      <div
        class="flex w-full items-center gap-1"
        :class="showMission ? 'justify-between' : 'justify-end'"
      >
        <UCheckbox
          v-if="showMission"
          label="Mission"
          color="secondary"
          :model-value="missionChecked"
          @update:model-value="onMissionToggle"
        />
        <div class="flex shrink-0 gap-2">
          <UButton
            v-if="showReportIssue"
            label="Report Issue"
            icon="i-lucide-circle-alert"
            color="warning"
            variant="outline"
            class="rounded-full"
            @click="onIssueClick"
          />
          <UButton
            v-if="showCancel"
            label="Cancel"
            icon="i-lucide-x-circle"
            color="error"
            variant="solid"
            class="rounded-full"
            @click="onCancel"
          />
          <UButton
            v-if="showUndo"
            label="Undo"
            icon="i-lucide-undo-2"
            color="neutral"
            variant="outline"
            class="rounded-full"
            @click="onUndo"
          />
        </div>
      </div>
    </template>
  </UCard>

  <CaseIssueModal
    v-model:open="issueModalOpen"
    :initial-sub-status="caseItem.sub_status ?? []"
    :initial-note="caseItem.note ?? ''"
    @submit="onIssueSubmit"
  />
</template>
