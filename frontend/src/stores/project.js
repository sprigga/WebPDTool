import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProjects, getProjectStations } from '@/api/projects'

export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const currentStation = ref(null)
  const stations = ref([])

  async function fetchProjects() {
    try {
      const data = await getProjects()
      projects.value = data
      return data
    } catch (error) {
      console.error('Failed to fetch projects:', error)
      throw error
    }
  }

  async function fetchProjectStations(projectId) {
    try {
      const data = await getProjectStations(projectId)
      stations.value = data
      return data
    } catch (error) {
      console.error('Failed to fetch stations:', error)
      throw error
    }
  }

  function setCurrentProject(project) {
    currentProject.value = project
    localStorage.setItem('currentProject', JSON.stringify(project))
  }

  function setCurrentStation(station) {
    currentStation.value = station
    localStorage.setItem('currentStation', JSON.stringify(station))
  }

  function loadFromStorage() {
    const savedProject = localStorage.getItem('currentProject')
    const savedStation = localStorage.getItem('currentStation')

    if (savedProject) {
      currentProject.value = JSON.parse(savedProject)
    }
    if (savedStation) {
      currentStation.value = JSON.parse(savedStation)
    }
  }

  return {
    projects,
    currentProject,
    currentStation,
    stations,
    fetchProjects,
    fetchProjectStations,
    setCurrentProject,
    setCurrentStation,
    loadFromStorage
  }
})
