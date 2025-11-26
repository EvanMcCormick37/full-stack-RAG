// Test endpoint - visit /api/test to verify serverless functions are working

export default function handler(req, res) {
  res.status(200).json({
    success: true,
    message: 'Serverless function is working!',
    timestamp: new Date().toISOString(),
    method: req.method,
    url: req.url,
  });
}
