<script setup>
defineProps({
  title: { type: String, default: 'Modern Workflow' },
  showClose: { type: Boolean, default: false }
})

defineEmits(['close'])
</script>

<template>
  <header class="sticky top-0 z-40 w-full border-b border-default bg-default">
    <div class="mx-auto flex h-14 max-w-[1024px] items-center justify-between px-4">
      <div class="flex items-center gap-3">
        <UButton
          v-if="showClose"
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          size="lg"
          aria-label="Close"
          @click="$emit('close')"
        />
        <h1 class="text-headline-md text-highlighted">
          {{ title }}
        </h1>
      </div>
    </div>
  </header>
</template>
