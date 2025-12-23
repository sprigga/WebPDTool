import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProjects, getProjectStations } from '@/api/projects'

export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const currentProject = ref(JSON.parse(localStorage.getItem('currentProject') || 'null'))
  const currentStation = ref(JSON.parse(localStorage.getItem('currentStation') || 'null'))
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
    if (project) {
      localStorage.setItem('currentProject', JSON.stringify(project))
    } else {
      localStorage.removeItem('currentProject')
    }
  }

  function setCurrentStation(station) {
    currentStation.value = station
    if (station) {
      localStorage.setItem('currentStation', JSON.stringify(station))
    } else {
      localStorage.removeItem('currentStation')
    }
  }

  function clearCurrentSelection() {
    currentProject.value = null
    currentStation.value = null
    localStorage.removeItem('currentProject')
    localStorage.removeItem('currentStation')
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
    clearCurrentSelection
  }
})
