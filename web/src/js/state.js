// state.js
export const API_BASE_URL = 'http://localhost:8000';

export const state = {
    token: localStorage.getItem('token') || null,
    currentUser: null,
    currentKGId: null,
    currentSessionId: null,
    files: [],
    knowledgeGraphs: [],
    currentPage: 1,
    pageSize: 20,
    dbConnections: {},
    currentConnection: null,
    latestHealthData: null,
    healthChart: null,
    currentAgentSessionId: null,
    healthData: [],
    emergencyContacts: []
};