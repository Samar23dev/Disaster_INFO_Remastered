import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getStats = async () => {
  const response = await apiClient.get('/stats');
  return response.data;
};

export const getEvents = async (params = {}) => {
  const response = await apiClient.get('/events', { params });
  return response.data;
};

export const getEventById = async (id) => {
  const response = await apiClient.get(`/events/${id}`);
  return response.data;
};

export const getHeatmap = async () => {
  const response = await apiClient.get('/heatmap');
  return response.data;
};

export const getAlerts = async (limit = 10) => {
  const response = await apiClient.get('/alerts', { params: { limit } });
  return response.data;
};

export const getRiskByLocation = async (location) => {
  const response = await apiClient.get(`/risk/${location}`);
  return response.data;
};

export const triggerPipeline = async () => {
  const response = await apiClient.post('/pipeline/run');
  return response.data;
};

export default apiClient;
