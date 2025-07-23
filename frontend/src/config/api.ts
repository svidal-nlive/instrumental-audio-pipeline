// API Configuration

const ensureTrailingSlash = (url: string) => url.endsWith('/') ? url : url + '/';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8002';

export const apiConfig = {
  baseURL: ensureTrailingSlash(API_BASE_URL),
  endpoints: {
    system: `${API_BASE_URL}/api/v1/system/`,
    systemStats: `${API_BASE_URL}/api/v1/system/stats/`,
    systemServices: `${API_BASE_URL}/api/v1/system/services/`,
    systemStorage: `${API_BASE_URL}/api/v1/system/storage/`,
    jobs: `${API_BASE_URL}/api/v1/jobs/`,
    upload: `${API_BASE_URL}/api/v1/upload/`,
    queue: `${API_BASE_URL}/api/v1/queue/`,
  }
};

export default apiConfig;