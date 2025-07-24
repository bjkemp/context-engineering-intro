import { displayInfoWithDelay, setUserIpAddress } from './terminal.js';

// Function to get user's IP address
const getUserIpAddress = async () => {
    try {
        const response = await fetch('https://api.ipify.org?format=json');
        const data = await response.json();
        return data.ip;
    } catch (error) {
        console.error('Error fetching IP address:', error);
        return 'Unavailable';
    }
};

// Gather browser information and display
const displayBrowserInfo = async (terminal) => {
    const browserInfoMessages = [
        `Operating System: ${navigator.platform || navigator.userAgent}`,
        `Browser Name: ${navigator.appName}`,
        `User Agent: ${navigator.userAgent}`,
        `JavaScript Enabled: true`,
        `Cookies Enabled: ${navigator.cookieEnabled}`,
        `WebSockets Enabled: ${typeof WebSocket !== 'undefined'}`,
        `WebGL Enabled: ${(() => {
            try {
                const canvas = document.createElement('canvas');
                return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
            } catch (e) {
                return false;
            }
        })()}`,
        `Window Size: ${window.innerWidth}x${window.innerHeight}`,
        `Current Date and Time: ${new Date().toLocaleString()}`
    ];

    const userIp = await getUserIpAddress();
    setUserIpAddress(userIp); // Update the IP address in terminal.js
    const uniqueBrowserInfoMessages = Array.from(new Set(browserInfoMessages)); // Ensure unique messages
    uniqueBrowserInfoMessages.splice(5, 0, `IP Address: ${userIp}`); // Insert at a specific position
    displayInfoWithDelay(terminal, uniqueBrowserInfoMessages);
};

export { displayBrowserInfo, getUserIpAddress };