// Vercel Serverless Function - Proxies requests to HTTP backend

// Note: Replace with your actual backend IP
const BACKEND_URL = 'http://35.209.149.3:8000';

export const config = {
  api: {
    bodyParser: false, // Critical for file uploads
    responseLimit: false,
  },
};

export default async function handler(req, res) {
  // 1. RECOVER THE ORIGINAL URL
  // The 'routes' rule passed the original path in the '_path' query param.
  let targetPath = req.query._path;
  
  // Handle array or string cases for query params
  if (Array.isArray(targetPath)) {
    targetPath = targetPath.join('/');
  }
  
  // Safety fallback
  if (!targetPath) {
    targetPath = req.url; 
  }

  // 2. RECONSTRUCT QUERY PARAMETERS
  // Vercel merges the original query params (like ?confirm=true) into req.query.
  // We must rebuild the string but EXCLUDE our internal '_path' param.
  const queryParams = new URLSearchParams();
  Object.keys(req.query).forEach(key => {
    if (key !== '_path') {
      queryParams.append(key, req.query[key]);
    }
  });

  const queryString = queryParams.toString();
  const finalUrl = queryString 
    ? `${BACKEND_URL}${targetPath}?${queryString}` 
    : `${BACKEND_URL}${targetPath}`;

  console.log(`[Proxy] ${req.method} ${targetPath} -> ${finalUrl}`);

  try {
    // Collect raw body
    const chunks = [];
    for await (const chunk of req) {
      chunks.push(chunk);
    }
    const bodyBuffer = Buffer.concat(chunks);

    // Build headers
    const headers = {};
    const allowedHeaders = ['content-type', 'api-key', 'authorization', 'session-id'];
    
    allowedHeaders.forEach(header => {
        if (req.headers[header]) {
            headers[header] = req.headers[header];
        }
    });

    const fetchOptions = {
      method: req.method,
      headers,
    };

    if (['POST', 'PUT', 'PATCH'].includes(req.method) && bodyBuffer.length > 0) {
      fetchOptions.body = bodyBuffer;
    }

    // Make request to backend
    const backendResponse = await fetch(finalUrl, fetchOptions);

    // Forward response headers
    const contentType = backendResponse.headers.get('content-type');
    if (contentType) {
      res.setHeader('Content-Type', contentType);
    }

    // Get and send response
    const responseData = await backendResponse.arrayBuffer();
    res.status(backendResponse.status).send(Buffer.from(responseData));

  } catch (error) {
    console.error('[Proxy Error]', error);
    res.status(502).json({
      error: 'Bad Gateway',
      message: `Failed to reach backend: ${error.message}`,
      target: finalUrl,
    });
  }
}