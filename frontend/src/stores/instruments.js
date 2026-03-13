// frontend/src/stores/instruments.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getInstruments } from '@/api/instruments'

export const useInstrumentsStore = defineStore('instruments', () => {
  const instruments = ref([])
  const loading = ref(false)

  async function fetchInstruments(enabledOnly = false) {
    try {
      loading.value = true
      const data = await getInstruments(enabledOnly)
      instruments.value = data
      return data
    } catch (error) {
      console.error('Failed to fetch instruments:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    instruments,
    loading,
    fetchInstruments,
  }
})
