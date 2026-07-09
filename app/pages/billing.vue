<script setup>
definePageMeta({ layout: 'default' })

const { getBillingSummaries } = useBillingApi()

const loading = ref(true)
const summaries = ref([])

async function loadSummaries() {
  loading.value = true
  summaries.value = await getBillingSummaries()
  loading.value = false
}

await loadSummaries()
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-headline-lg-mobile text-highlighted">
        Billing
      </h1>
      <p class="mt-1 text-sm text-muted">
        {{ summaries.length }} {{ summaries.length === 1 ? 'day' : 'days' }}
      </p>
    </div>

    <div
      v-if="loading"
      class="space-y-4"
    >
      <USkeleton class="h-24 w-full rounded-[16px]" />
      <USkeleton class="h-24 w-full rounded-[16px]" />
      <USkeleton class="h-24 w-full rounded-[16px]" />
    </div>

    <template v-else>
      <div
        v-if="!summaries.length"
        class="mt-16 flex flex-col items-center justify-center text-center opacity-60"
      >
        <UIcon
          name="i-lucide-receipt"
          class="mb-4 size-16 opacity-40"
        />
        <p class="max-w-xs text-base text-muted">
          No billing history yet.
        </p>
      </div>

      <div class="space-y-4">
        <BillingSummaryCard
          v-for="s in summaries"
          :key="s.date"
          :summary="s"
        />
      </div>
    </template>
  </div>
</template>
