<script setup>
const open = defineModel('open', { type: Boolean, default: false })

defineProps({
  summary: {
    type: Object,
    required: true
  }
})
</script>

<template>
  <UModal
    v-model:open="open"
    title="Send complete"
    description="Cases have been sent to the office."
  >
    <template #body>
      <div class="space-y-2 text-sm text-default">
        <p v-if="summary.billableCount">
          {{ summary.billableCount }} {{ summary.billableCount === 1 ? 'case' : 'cases' }} · {{ summary.billableMinutes }} billable minutes
        </p>
        <p v-if="summary.missionCount">
          {{ summary.missionCount }} mission {{ summary.missionCount === 1 ? 'case' : 'cases' }} · {{ summary.missionMinutes }} non-billable minutes
        </p>
        <p v-if="summary.cancelledCount">
          {{ summary.cancelledCount }} cancelled {{ summary.cancelledCount === 1 ? 'case' : 'cases' }}
        </p>
        <p v-if="summary.issueCount">
          {{ summary.issueCount }} {{ summary.issueCount === 1 ? 'case' : 'cases' }} with issues
        </p>
        <p
          v-if="!summary.billableCount && !summary.missionCount && !summary.cancelledCount && !summary.issueCount"
          class="text-muted"
        >
          No cases were sent.
        </p>
      </div>
    </template>

    <template #footer>
      <div class="flex w-full justify-end">
        <UButton
          label="Done"
          color="primary"
          class="rounded-full"
          @click="open = false"
        />
      </div>
    </template>
  </UModal>
</template>
