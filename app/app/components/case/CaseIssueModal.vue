<script setup>
/** @typedef {import('~/types/case').IssueType} IssueType */

const open = defineModel('open', { type: Boolean, default: false })

const props = defineProps({
  initialSubStatus: { type: Array, default: () => [] },
  initialNote: { type: String, default: '' }
})

const emit = defineEmits(['submit'])

/** @type {import('vue').Ref<IssueType[]>} */
const subStatus = ref([])
const note = ref('')

const issueOptions = [
  { value: 'identity_issue', label: 'Identity issue' },
  { value: 'needs_review', label: 'Needs review' }
]

const canSubmit = computed(() => subStatus.value.length > 0)

watch(open, (isOpen) => {
  if (isOpen) {
    subStatus.value = [...(props.initialSubStatus)]
    note.value = props.initialNote
  }
})

function onCancel() {
  open.value = false
}

function onSubmit() {
  if (!canSubmit.value) return
  emit('submit', {
    sub_status: [...subStatus.value],
    note: note.value.trim()
  })
  open.value = false
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Report issue"
  >
    <template #body>
      <div class="flex flex-col gap-4 w-full">
        <UCheckboxGroup
          v-model="subStatus"
          :items="issueOptions"
          color="warning"
          variant="table"
          orientation="horizontal"
          indicator="hidden"
          class="w-full"
          :ui="{ fieldset: 'w-full', item: 'flex-1' }"
        />

        <UTextarea
          v-model="note"
          placeholder="Notes"
          autoresize
          class="w-full"
        />
      </div>
    </template>

    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton
          label="Cancel"
          color="neutral"
          variant="outline"
          class="rounded-full"
          @click="onCancel"
        />
        <UButton
          label="Submit"
          color="primary"
          class="rounded-full"
          :disabled="!canSubmit"
          @click="onSubmit"
        />
      </div>
    </template>
  </UModal>
</template>
