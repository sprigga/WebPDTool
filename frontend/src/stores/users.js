import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getUsers, createUser, updateUser, deleteUser } from '@/api/users'

export const useUsersStore = defineStore('users', () => {
  const users = ref([])
  const loading = ref(false)

  async function fetchUsers(offset = 0, limit = 100) {
    try {
      loading.value = true
      const data = await getUsers(offset, limit)
      users.value = data
      return data
    } catch (error) {
      console.error('Failed to fetch users:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function addUser(userData) {
    try {
      loading.value = true
      await createUser(userData)
      await fetchUsers()
    } catch (error) {
      console.error('Failed to add user:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function modifyUser(userId, userData) {
    try {
      loading.value = true
      await updateUser(userId, userData)
      await fetchUsers()
    } catch (error) {
      console.error('Failed to modify user:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function removeUser(userId) {
    try {
      loading.value = true
      await deleteUser(userId)
      await fetchUsers()
    } catch (error) {
      console.error('Failed to remove user:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    users,
    loading,
    fetchUsers,
    addUser,
    modifyUser,
    removeUser
  }
})
