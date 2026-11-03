const API_BASE = 'http://127.0.0.1:8000';

async function handleResponse(res) {
  if (!res.ok) {
    const errorText = await res.text();
    let detail = errorText;
    try {
      const parsed = JSON.parse(errorText);
      detail = parsed.detail || errorText;
    } catch (_) {}
    throw new Error(detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  async getUsers() {
    const res = await fetch(`${API_BASE}/users`);
    return handleResponse(res);
  },

  async createUser(name, email) {
    const res = await fetch(`${API_BASE}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email }),
    });
    return handleResponse(res);
  },

  async getCourses() {
    const res = await fetch(`${API_BASE}/courses`);
    return handleResponse(res);
  },

  async getCourseModules(courseId) {
    const res = await fetch(`${API_BASE}/courses/${courseId}/modules`);
    return handleResponse(res);
  },

  async getModuleTopics(moduleId) {
    const res = await fetch(`${API_BASE}/modules/${moduleId}/topics`);
    return handleResponse(res);
  },

  async getUserDashboard(userId) {
    const res = await fetch(`${API_BASE}/users/${userId}/dashboard`);
    return handleResponse(res);
  },

  async logLearningEvent(userId, topicId, timeSpentSeconds, selfReportedConfidence = 0.7) {
    const res = await fetch(`${API_BASE}/learning-events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        topic_id: topicId,
        time_spent_seconds: timeSpentSeconds,
        self_reported_confidence: selfReportedConfidence,
      }),
    });
    return handleResponse(res);
  },

  async logSelfCheckEvent(userId, topicId, isCorrect, timeSpentSeconds = 60, isUpcomingAssessmentPrep = false) {
    const res = await fetch(`${API_BASE}/self-check-events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        topic_id: topicId,
        is_correct: isCorrect,
        time_spent_seconds: timeSpentSeconds,
        is_upcoming_assessment_prep: isUpcomingAssessmentPrep,
      }),
    });
    return handleResponse(res);
  },
};
