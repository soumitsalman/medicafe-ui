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
    icon="i-lucide-rocket"
    title="Sent"
  >
    <template #body>
      <div class="flex flex-wrap gap-2 items-center justify-center text-sm">
        <UBadge
          v-if="summary.billableCount"
          color="primary"
        >
          {{ summary.billableCount }} billable
        </UBadge>
        <UBadge
          v-if="summary.missionCount"
          color="secondary"
        >
          {{ summary.missionCount }} mission
        </UBadge>
        <UBadge
          v-if="summary.cancelledCount"
          color="error"
        >
          {{ summary.cancelledCount }} cancelled
        </UBadge>
        <UBadge
          v-if="summary.issueCount"
          color="warning"
        >
          {{ summary.issueCount }} skipped
        </UBadge>
        <UBadge
          v-if="!summary.billableCount && !summary.missionCount && !summary.cancelledCount && !summary.issueCount"
          class="text-muted"
        >
          No cases were sent.
        </UBadge>
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
