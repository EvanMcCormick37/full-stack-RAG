export const sessionId = () => {
    let sessionId = localStorage.getItem('Session-Id');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        localStorage.setItem('Session-Id', sessionId)
    }
    return sessionId
};