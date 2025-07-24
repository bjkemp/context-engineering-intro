import { getUserIpAddress } from './browserInfo.js';
let currentPromptSpan; // To keep track of the current prompt span (now within a command-line div)
let staticPromptString = ''; // To store the static prompt text
let userIpAddress = '127.0.0.1'; // Default IP, will be updated

// Fetch IP address on load
(async () => {
    userIpAddress = await getUserIpAddress();
})();
// Function to update the IP address
const setUserIpAddress = (ip) => {
    userIpAddress = ip;
};


// Default styles for the terminal
const defaultFontSize = '16px';
const defaultFontColor = 'white';

const applyAnimation = (element, animationClass) => {
    element.classList.add(animationClass);
    element.addEventListener('animationend', () => {
        element.classList.remove(animationClass);
    }, { once: true });
};

const appendWithFadeIn = (terminal, element) => {
    applyAnimation(element, 'fade-in');
    terminal.appendChild(element);
};

// Function to add a new prompt line and place the cursor
const addNewPromptLine = (terminalElement) => {
    // Create a new div for the current command line
    const commandLineDiv = document.createElement('div');
    commandLineDiv.className = 'command-line'; // Add a class for styling if needed

    const promptSpan = document.createElement('span');
    promptSpan.className = 'prompt';
    const userSpan = document.createElement('span');
    userSpan.className = 'user';
    userSpan.textContent = 'root';
    promptSpan.appendChild(userSpan);
    const promptTextNode = document.createTextNode(`@${userIpAddress}: `);
    promptSpan.appendChild(promptTextNode);
    staticPromptString = promptSpan.textContent; // Capture the static prompt string
    
    // Add enhanced cursor with glow effect
    const cursor = document.createElement('span');
    cursor.className = 'cursor cursor-enhanced';
    promptSpan.appendChild(cursor);
    
    commandLineDiv.appendChild(promptSpan);

    // Append the commandLineDiv to the terminal with a fade-in effect
    appendWithFadeIn(terminal, commandLineDiv);

    // Place cursor at the end of the new commandLineDiv
    const newRange = document.createRange();
    const newSel = window.getSelection();
    newRange.selectNodeContents(commandLineDiv); // Select all contents of the new line div
    newRange.collapse(false); // Collapse to the end
    newSel.removeAllRanges();
    newSel.addRange(newRange);

    // Scroll to the bottom
    terminalElement.scrollTop = terminalElement.scrollHeight;

    // Update currentPromptSpan to refer to the prompt within the last command line div
    currentPromptSpan = promptSpan;
    terminalElement.setAttribute('contenteditable', 'true'); // Enable editing when a new prompt line is added
};

// Function to display information messages with a delay
const displayInfoWithDelay = (terminal, messages) => {
    let i = 0;
    const interval = setInterval(() => {
        if (i < messages.length) {
            const messageParts = messages[i].split(': ');
            const labelSpan = document.createElement('span');
            labelSpan.style.color = 'rgb(0,255,0)'; // Green color for label
            labelSpan.textContent = messageParts[0] + ': ';
            appendWithFadeIn(terminal, labelSpan);

            const valueSpan = document.createElement('span');
            valueSpan.style.color = 'white'; // White color for value
            valueSpan.textContent = messageParts.slice(1).join(': ');
            appendWithFadeIn(terminal, valueSpan);
            const br = document.createElement('br');
            appendWithFadeIn(terminal, br);
            terminal.scrollTop = terminal.scrollHeight; // Scroll to bottom
            i++;
        } else {
            clearInterval(interval);
terminal.appendChild(document.createElement('br')); // Blank line after browser info
            const asciiArt =
` ██████╗██╗   ██╗ ██████╗  █████╗    
██╔════╝╚██╗ ██╔╝██╔═══██╗██╔══██╗██╗
██║      ╚████╔╝ ██║   ██║███████║╚═╝
██║       ╚██╔╝  ██║   ██║██╔══██║██╗
╚██████╗   ██║   ╚██████╔╝██║  ██║╚═╝
 ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   
`;
            const asciiArtPre = document.createElement('pre');
            asciiArtPre.textContent = asciiArt;
            asciiArtPre.style.color = 'rgb(0,255,0)'; // Green color for ASCII art
            appendWithFadeIn(terminal, asciiArtPre);
            const br = document.createElement('br');
            appendWithFadeIn(terminal, br);
            addNewPromptLine(terminal); // Add a new prompt line after all info is displayed
        }
    }, 100); // Adjust delay as needed
};

const displayGameIntro = (terminal, gameName) => {
    return new Promise(resolve => {
        terminal.innerHTML = ''; // Clear terminal
        const gameTitleSpan = document.createElement('span');
        gameTitleSpan.className = 'game-title-intro'; // Use a specific class for centering
        gameTitleSpan.textContent = gameName;
        terminal.appendChild(gameTitleSpan);

        // Apply centering style to the terminal for the intro
        terminal.style.textAlign = 'center';

        setTimeout(() => {
            terminal.innerHTML = ''; // Clear after 1 second
            terminal.style.textAlign = 'left'; // Reset text alignment
            resolve();
        }, 1000);
    });
};

// Function to set font size
const setFontSize = (terminalElement, size) => {
    terminalElement.style.fontSize = size;
};

// Function to set font color
const setFontColor = (terminalElement, color) => {
    terminalElement.style.color = color;
};

// Function to reset terminal styles to default
const resetTerminalStyles = (terminalElement) => {
    terminalElement.style.fontSize = defaultFontSize;
    terminalElement.style.color = defaultFontColor;
};

export { addNewPromptLine, displayInfoWithDelay, displayGameIntro, setFontSize, setFontColor, resetTerminalStyles, setUserIpAddress, staticPromptString, applyAnimation };