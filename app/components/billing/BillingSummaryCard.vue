<script setup>
import { format, parse } from 'date-fns'
import { formatDuration } from '~/utils/duration'

const props = defineProps({
  summary: { type: Object, required: true }
})

const formattedDate = computed(() => {
  const parsed = parse(props.summary.date, 'MM-dd-yyyy', new Date())
  return format(parsed, 'MM/dd/yyyy')
})

const billedDisplay = computed(() =>
  formatDuration(Math.round(props.summary.billedHours * 60))
)

const nonBilledDisplay = computed(() =>
  formatDuration(Math.round(props.summary.nonBilledHours * 60))
)

const cancelledLabel = computed(() => {
  const n = props.summary.cancelledCount
  return `${n} cancelled`
})

const issueLabel = computed(() => {
  const n = props.summary.issueCount
  return `${n} ${n === 1 ? 'issue' : 'issues'}`
})
</script>

<template>
  <UCard class="rounded-2xl bg-default pill-shadow">
    <div class="flex w-full items-center justify-between">
      <span class="text-headline-md text-highlighted">{{ formattedDate }}</span>
    </div>

    <div class="mt-3 flex w-full items-center justify-between">
      <span class="text-sm text-primary">Billed</span>
      <span class="text-sm font-medium text-highlighted">{{ billedDisplay }}</span>
    </div>

    <div class="mt-2 flex w-full items-center justify-between">
      <span class="text-sm text-secondary">Mission</span>
      <span class="text-sm font-medium text-highlighted">{{ nonBilledDisplay }}</span>
    </div>

    <div
      v-if="summary.cancelledCount"
      class="mt-2 flex w-full items-center justify-between"
    >
      <span class="text-sm text-error">Cancelled</span>
      <span class="text-sm font-medium text-highlighted">{{ cancelledLabel }}</span>
    </div>

    <div
      v-if="summary.issueCount"
      class="mt-2 flex w-full items-center justify-between"
    >
      <span class="text-sm text-warning">Issues</span>
      <span class="text-sm font-medium text-highlighted">{{ issueLabel }}</span>
    </div>
  </UCard>
</template>
