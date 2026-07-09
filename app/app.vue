<script setup>
useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' },
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600;6..72,700&family=DM+Sans:wght@400;500;700&display=swap'
    }
  ],
  htmlAttrs: { lang: 'en' }
})

useSeoMeta({
  title: 'Case Manager',
  description: 'Modern Workflow — Soft Medical companion for anesthesiologists'
})
</script>

<template>
  <UApp>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
