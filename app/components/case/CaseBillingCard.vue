<script setup>
import { formatDob } from '~/utils/duration'

const props = defineProps({
  caseItem: { type: Object, required: true }
})

const statusLabel = computed(() => {
  if (props.caseItem.status === 'cancelled') return 'Cancelled'
  if (props.caseItem.status === 'mission') return 'Mission'
  if (props.caseItem.status === 'billable') return 'Billable'
  if (props.caseItem.status === 'issue') return 'Issue'
  return props.caseItem.status
})

const statusColor = computed(() => {
  if (props.caseItem.status === 'cancelled') return 'error'
  if (props.caseItem.status === 'mission') return 'secondary'
  if (props.caseItem.status === 'issue') return 'warning'
  return 'primary'
})

const minutesDisplay = computed(() => {
  const mins = props.caseItem.minutes
  if (mins == null || mins === 0) return '0 min'
  return `${mins} min`
})
</script>

<template>
  <UCard class="rounded-2xl bg-default pill-shadow">
    <div class="flex w-full">
      <UBadge
        :label="statusLabel"
        :color="statusColor"
        variant="subtle"
        class="rounded px-2 py-0.5 text-label-caps"
      />
    </div>

    <div class="mt-2 flex w-full items-center justify-between">
      <span
        v-if="caseItem.patient?.fullName ?? caseItem.patient_name"
        class="min-w-0 flex-1 truncate text-headline-md text-highlighted"
      >{{ caseItem.patient?.fullName ?? caseItem.patient_name }}</span>
      <span class="shrink-0 text-sm text-muted">
        <template v-if="caseItem.patient">
          {{ formatDob(caseItem.patient.dateOfBirth) }} ({{ caseItem.patient.ageYears }}y)
        </template>
        <template v-else-if="caseItem.patient_dob">
          {{ formatDob(caseItem.patient_dob) }}
        </template>
      </span>
    </div>

    <div class="mt-2 flex w-full items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="min-w-0 flex-1 truncate text-sm text-muted">{{ caseItem.diagnosis }}</span>
        <UBadge
          v-for="tag in (caseItem.diagnosisModifierTags ?? [])"
          :key="tag"
          :label="tag"
          color="secondary"
          variant="subtle"
          class="rounded px-1.5 py-0.5 text-xs"
        />
      </div>
      <span class="shrink-0 text-sm font-medium text-highlighted">{{ minutesDisplay }}</span>
    </div>
  </UCard>
</template>
