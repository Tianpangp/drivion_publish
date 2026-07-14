<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from './stores/user'

const userStore = useUserStore()

onMounted(async () => {
  try {
    await userStore.loadAuthMode()
  } finally {
    await userStore.loadUser()
  }
})
</script>
