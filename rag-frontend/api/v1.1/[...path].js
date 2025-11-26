// Vercel Serverless Function - Proxies requests to HTTP backend
// This solves the mixed-content issue (HTTPS frontend → HTTP backend)

const BACKEND_URL = 'http://35.209.149.3:8000';

export const config = {
  api: {
    bodyParser: false,
    responseLimit: false,
  },
};

export default async function handler(req, res) {
  const targetUrl = `${BACKEND_URL}${req.url}`;
  
  console.log(`[Proxy] ${req.method} ${req.url} -> ${targetUrl}`);

  try {
    // Collect raw body
    const chunks = [];
    for await (const chunk of req) {
      chunks.push(chunk);
    }
    const bodyBuffer = Buffer.concat(chunks);

    // Build headers to forward
    const headers = {};
    
    if (req.headers['content-type']) {
      headers['Content-Type'] = req.headers['content-type'];
    }
    
    if (req.headers['api-key']) {
      headers['API-Key'] = req.headers['api-key'];
    }
    
    if (req.headers['authorization']) {
      headers['Authorization'] = req.headers['authorization'];
    }

    // Build fetch options
    const fetchOptions = {
      method: req.method,
      headers,
    };

    if (['POST', 'PUT', 'PATCH'].includes(req.method) && bodyBuffer.length > 0) {
      fetchOptions.body = bodyBuffer;
    }

    // Make request to backend
    const backendResponse = await fetch(targetUrl, fetchOptions);

    // Forward response headers
    const contentType = backendResponse.headers.get('content-type');
    if (contentType) {
      res.setHeader('Content-Type', contentType);
    }

    // Forward CORS headers
    ['access-control-allow-origin', 'access-control-allow-methods', 'access-control-allow-headers', 'access-control-allow-credentials'].forEach(header => {
      const value = backendResponse.headers.get(header);
      if (value) res.setHeader(header, value);
    });

    // Get and send response
    const responseData = await backendResponse.arrayBuffer();
    res.status(backendResponse.status).send(Buffer.from(responseData));

  } catch (error) {
    console.error('[Proxy Error]', error);
    res.status(502).json({
      error: 'Bad Gateway',
      message: `Failed to reach backend: ${error.message}`,
      target: targetUrl,
    });
  }
}