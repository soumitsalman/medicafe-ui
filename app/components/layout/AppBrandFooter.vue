<script setup>
import medicafeIcon from '~/assets/medicafe.ico'
</script>

<template>
  <footer class="mt-auto border-t border-default/60 py-4">
    <div class="mx-auto flex w-full max-w-[1024px] items-center justify-center gap-2 px-3 sm:px-4 text-xs text-muted">
      <img
        :src="medicafeIcon"
        alt=""
        class="size-4 shrink-0 object-contain opacity-80"
      >
      <span>
        Medicafe ·
        <a
          href="https://cafecito.tech"
          target="_blank"
          rel="noopener noreferrer"
          class="underline-offset-2 hover:text-highlighted hover:underline"
        >Project Cafecito</a>
      </span>
    </div>
  </footer>
</template>
