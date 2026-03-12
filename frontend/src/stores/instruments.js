// frontend/src/stores/instruments.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getInstruments, createInstrument, updateInstrument, deleteInstrument } from '@/api/instruments'

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

  async function addInstrument(instrumentData) {
    try {
      loading.value = true
      await createInstrument(instrumentData)
      await fetchInstruments()
    } catch (error) {
      console.error('Failed to add instrument:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function modifyInstrument(instrumentId, instrumentData) {
    try {
      loading.value = true
      await updateInstrument(instrumentId, instrumentData)
      await fetchInstruments()
    } catch (error) {
      console.error('Failed to modify instrument:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function removeInstrument(instrumentId) {
    try {
      loading.value = true
      await deleteInstrument(instrumentId)
      await fetchInstruments()
    } catch (error) {
      console.error('Failed to remove instrument:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    instruments,
    loading,
    fetchInstruments,
    addInstrument,
    modifyInstrument,
    removeInstrument
  }
})
