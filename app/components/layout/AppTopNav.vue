<script setup>
const route = useRoute()

const tabs = [
  { id: 'home', label: 'Home', icon: 'i-lucide-home', to: '/' },
  { id: 'settings', label: 'Settings', icon: 'i-lucide-settings', to: '/settings' }
]

const activeTab = computed(() => {
  if (route.path.startsWith('/settings')) return 'settings'
  return 'home'
})
</script>

<template>
  <nav class="sticky top-0 z-40 w-full border-b border-default bg-default">
    <div class="mx-auto flex h-14 max-w-[1024px] items-center justify-around px-4">
      <NuxtLink
        v-for="tab in tabs"
        :key="tab.id"
        :to="tab.to"
        class="flex flex-1 flex-col items-center justify-center gap-0.5 rounded-full py-1 transition-all active:scale-95"
        :class="activeTab === tab.id
          ? 'text-primary'
          : 'text-muted hover:text-highlighted'"
      >
        <span
          class="flex items-center justify-center rounded-full px-5 py-1.5"
          :class="activeTab === tab.id ? 'bg-primary/10' : ''"
        >
          <UIcon
            :name="tab.icon"
            class="size-5"
          />
        </span>
        <span
          v-if="tab.label"
          class="text-label-caps"
        >{{ tab.label }}</span>
      </NuxtLink>
    </div>
  </nav>
</template>
