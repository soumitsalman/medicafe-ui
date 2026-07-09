<script setup>
import { formatDob } from '~/utils/duration'

const props = defineProps({
  caseItem: { type: Object, required: true }
})

const statusLabel = computed(() => {
  if (props.caseItem.status === 'cancelled') return 'Cancelled'
  if (props.caseItem.status === 'completed' && props.caseItem.missionCharity) return 'Completed — Charity/Mission'
  if (props.caseItem.status === 'completed') return 'Completed'
  return props.caseItem.status
})

const statusColor = computed(() => {
  if (props.caseItem.status === 'cancelled') return 'error'
  return 'primary'
})

const durationDisplay = computed(() => {
  const mins = props.caseItem.durationMinutes
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
      <span class="min-w-0 flex-1 truncate text-headline-md text-highlighted">{{ caseItem.patient.fullName }}</span>
      <span class="shrink-0 text-sm text-muted">{{ formatDob(caseItem.patient.dateOfBirth) }} ({{ caseItem.patient.ageYears }}y)</span>
    </div>

    <div class="mt-2 flex w-full items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="min-w-0 flex-1 truncate text-sm text-muted">{{ caseItem.diagnosis }}</span>
        <UBadge
          v-for="tag in caseItem.diagnosisModifierTags"
          :key="tag"
          :label="tag"
          color="secondary"
          variant="subtle"
          class="rounded px-1.5 py-0.5 text-xs"
        />
      </div>
      <span class="shrink-0 text-sm font-medium text-highlighted">{{ durationDisplay }}</span>
    </div>
  </UCard>
</template>
