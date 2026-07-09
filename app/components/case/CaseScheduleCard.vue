<script setup>
import { debounce, formatDobWithAge } from '~/utils/duration'
import { deriveFromDx, dxOptions } from '~/utils/dxLookup'
import { isIssueStatus, statusDisplayFromCase } from '~/utils/caseSelectors'

const props = defineProps({
  caseItem: { type: Object, required: true }
})

const emit = defineEmits(['patch', 'cancel', 'undo', 'issue'])

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

const issueSubStateLabels = computed(() =>
  (props.caseItem.subState ?? []).map(type => ISSUE_TYPE_LABELS[type] ?? type)
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

const cardBorderClass = computed(() => {
  const { borderClass, opacityClass } = statusDisplay.value
  if (!borderClass) return {}
  return {
    'border-l-4': true,
    [borderClass]: true,
    [opacityClass]: !!opacityClass
  }
})

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

const debouncedPatch = debounce((fields) => {
  emit('patch', props.caseItem.id, fields)
}, 600)

function onMinutesChange(value) {
  if (value == null) {
    debouncedPatch({ minutes: null })
  } else {
    debouncedPatch({ minutes: value })
  }
}

function onDxChange(value) {
  dxValue.value = value
  debouncedPatch({ dx: value })
}

function onMissionToggle() {
  missionChecked.value = !missionChecked.value
  debouncedPatch({ mission: missionChecked.value })
}

function onNoteChange(value) {
  debouncedPatch({ note: value ?? '' })
}

function onClearNote() {
  noteInput.value = ''
  debouncedPatch({ note: '' })
}

function onCancel() {
  emit('cancel', props.caseItem.id)
}

function onUndo() {
  emit('undo', props.caseItem.id)
}

function onIssueClick() {
  issueModalOpen.value = true
}

function onIssueSubmit(payload) {
  emit('issue', props.caseItem.id, payload)
}
</script>

<template>
  <UCard
    class="rounded-2xl bg-default pill-shadow"
    :class="cardBorderClass"
  >
    <div class="flex w-full items-center justify-between gap-2">
      <div class="flex min-w-0 flex-1 items-center gap-2">
        
        <UIcon
          v-if="statusDisplay.icon"
          :name="statusDisplay.icon"
          class="shrink-0 size-5"
          :class="statusDisplay.textClass"
        />
        <UBadge
          :label="caseItem.patientId"
          color="neutral"
          variant="subtle"
          class="shrink-0"
        />
        <span class="min-w-0 truncate text-headline-md">
          {{ caseItem.name }}
        </span>
        <span class="shrink-0 text-sm text-muted">
          {{ formatDobWithAge(caseItem.dob, caseItem.date) }}
        </span>
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <UInputNumber
          v-model.optional="minutesInput"
          placeholder="Min"
          :min="0"
          :max="59"          
          class="w-32"
          @update:model-value="onMinutesChange"
        />
        <span class="text-sm text-muted">mins</span>
      </div>
    </div>

    <div class="mt-3 flex w-full items-center gap-2">
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
      v-if="isIssue && issueSubStateLabels.length"
      class="mt-2 flex w-full flex-wrap gap-2"
    >
      <UBadge
        v-for="label in issueSubStateLabels"
        :key="label"
        :label="label"
        color="warning"
        variant="soft"
      />
    </div>

    <div
      v-if="showNoteRow"
      class="mt-3 flex w-full items-start gap-2"
    >
      <UTextarea
        v-model="noteInput"
        placeholder="Note"
        :rows="2"
        autoresize
        class="flex-1"
        @update:model-value="onNoteChange"
      />
      <UButton
        icon="i-lucide-x"
        color="neutral"
        variant="ghost"
        
        aria-label="Clear note"
        @click="onClearNote"
      />
    </div>

    <div class="mt-3 border-t border-default pt-3">
      <div
        class="flex w-full items-center"
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
    </div>

    <CaseIssueModal
      v-model:open="issueModalOpen"
      :initial-sub-state="caseItem.subState ?? []"
      :initial-note="caseItem.note ?? ''"
      @submit="onIssueSubmit"
    />
  </UCard>
</template>
