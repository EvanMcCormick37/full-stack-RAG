export const sessionId = () => {
    let sessionId = localStorage.getItem('Session-ID');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        localStorage.setItem('Session-ID', sessionId)
    }
    return sessionId
};