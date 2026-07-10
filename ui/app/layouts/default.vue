<template>
  <div class="flex min-h-dvh flex-col bg-default text-default">
    <AppTopNav />
    <AppPageContainer class="flex-1">
      <slot />
    </AppPageContainer>
    <AppBrandFooter />
  </div>
</template>
