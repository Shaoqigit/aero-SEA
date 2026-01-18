import axios from 'axios'

const API_BASE = '/api'

const api = {
  // Projects
  async createProject(name: string, description?: string) {
    const response = await axios.post(`${API_BASE}/projects`, { name, description })
    return response.data
  },

  async getProject(projectId: string) {
    const response = await axios.get(`${API_BASE}/projects/${projectId}`)
    return response.data
  },

  async deleteProject(projectId: string) {
    const response = await axios.delete(`${API_BASE}/projects/${projectId}`)
    return response.data
  },

  // Materials
  async listMaterials() {
    const response = await axios.get(`${API_BASE}/materials`)
    return response.data
  },

  async addMaterial(projectId: string, material: any) {
    const response = await axios.post(`${API_BASE}/projects/${projectId}/materials`, material)
    return response.data
  },

  // Structures
  async addStructure(projectId: string, structure: any) {
    const response = await axios.post(`${API_BASE}/projects/${projectId}/structures`, structure)
    return response.data
  },

  // Acoustic Spaces
  async addAcousticSpace(projectId: string, space: any) {
    const response = await axios.post(`${API_BASE}/projects/${projectId}/acoustic-spaces`, space)
    return response.data
  },

  // Junctions
  async addJunction(projectId: string, junction: any) {
    const response = await axios.post(`${API_BASE}/projects/${projectId}/junctions`, junction)
    return response.data
  },

  // Loads
  async addLoad(projectId: string, load: any) {
    const response = await axios.post(`${API_BASE}/projects/${projectId}/loads`, load)
    return response.data
  },

  // Templates
  async listTemplates() {
    const response = await axios.get(`${API_BASE}/templates`)
    return response.data
  },

  async applyTemplate(projectId: string, templateName: string, params: any) {
    const response = await axios.post(`${API_BASE}/projects/${projectId}/apply-template?template_name=${templateName}`, params)
    return response.data
  },

  // Analysis
  async runAnalysis(projectId: string) {
    const response = await axios.post(`${API_BASE}/projects/${projectId}/analyze`)
    return response.data
  },

  // Geometry
  async getGeometry(projectId: string) {
    const response = await axios.get(`${API_BASE}/projects/${projectId}/geometry`)
    return response.data
  },

  // Results
  async getEnergy(projectId: string) {
    const response = await axios.get(`${API_BASE}/projects/${projectId}/energy`)
    return response.data
  },

  async getModalDensity(projectId: string) {
    const response = await axios.get(`${API_BASE}/projects/${projectId}/modal-density`)
    return response.data
  },

  async exportResults(projectId: string, units?: any) {
    const response = await axios.post(`${API_BASE}/projects/${projectId}/export-results`, units)
    return response.data
  }
}

export default api
