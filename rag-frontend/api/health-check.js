// Health check endpoint - tests connectivity to backend
// Visit /api/health-check to verify the proxy can reach the backend

const BACKEND_URL = 'http://35.209.149.3:8000';

export default async function handler(req, res) {
  const results = {
    serverlessFunction: 'ok',
    backendUrl: BACKEND_URL,
    backendHealth: null,
    error: null,
  };

  try {
    const response = await fetch(`${BACKEND_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      results.backendHealth = await response.json();
    } else {
      results.backendHealth = 'error';
      results.error = `Backend returned status ${response.status}`;
    }
  } catch (error) {
    results.backendHealth = 'unreachable';
    results.error = error.message;
  }

  const status = results.backendHealth === 'unreachable' ? 502 : 200;
  res.status(status).json(results);
}
