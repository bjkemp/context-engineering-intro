import { addNewPromptLine, staticPromptString } from './terminal.js';
import { displayBrowserInfo } from './browserInfo.js';
import { handleCommand } from './commandHandler.js';
import { saveGameState, loadGameState } from './gameState.js';
import { askUserName } from './userInput.js';
import { setUserName, getUserName } from './gameState.js';
import { parseFile } from './fileParser.js';

import { handleMenuNavigation, currentMenuItems } from './menuHandler.js';
import { toggleOverlayMenu } from './menuHandler.js';

document.addEventListener('DOMContentLoaded', () => {
    const terminal = document.getElementById('terminal');

    // Immediately show terminal and make it editable
    terminal.style.display = 'block';
    
    terminal.innerHTML = ''; // Clear terminal to remove blank spaces and new lines before listing browser information.
    terminal.style.whiteSpace = 'pre-wrap';

    

    // Display browser information on load
    displayBrowserInfo(terminal);

document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            toggleOverlayMenu(terminal);
        }
    });
    const availableCommands = ['load', 'help', 'clear', 'quit', 'options', 'exit'];
    let lastTabPressTime = 0;
    let lastInputOnTab = '';
    // Handle keyboard input in the terminal
    terminal.addEventListener('keydown', async (e) => {
        if (e.key === 'Tab') {
            e.preventDefault();

            const lastCommandLineDiv = terminal.querySelector('.command-line:last-of-type');
            if (!lastCommandLineDiv) return;

            const promptSpan = lastCommandLineDiv.querySelector('.prompt');
            if (!promptSpan) return;

            const fullLineText = lastCommandLineDiv.textContent;
            const promptText = promptSpan.textContent;
            let currentInput = fullLineText.substring(promptText.length);

            if (currentInput.includes(' ')) return;

            const matches = availableCommands.filter(cmd => cmd.startsWith(currentInput));

            if (matches.length === 1) {
                lastCommandLineDiv.textContent = promptText + matches[0];
                const range = document.createRange();
                const sel = window.getSelection();
                range.selectNodeContents(lastCommandLineDiv);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
            } else if (matches.length > 1) {
                const currentTime = new Date().getTime();
                if (currentTime - lastTabPressTime < 500 && lastInputOnTab === currentInput) {
                    const br = document.createElement('br');
                    terminal.appendChild(br);
                    const completionsSpan = document.createElement('span');
                    completionsSpan.style.color = 'rgb(255, 255, 0)';
                    completionsSpan.textContent = matches.join('   ');
                    terminal.appendChild(completionsSpan);
                    addNewPromptLine(terminal);
                    const newLastLine = terminal.querySelector('.command-line:last-of-type');
                    const newPromptSpan = newLastLine.querySelector('.prompt');
                    newLastLine.textContent = newPromptSpan.textContent + currentInput;

                    const range = document.createRange();
                    const sel = window.getSelection();
                    range.selectNodeContents(newLastLine);
                    range.collapse(false);
                    sel.removeAllRanges();
                    sel.addRange(range);
                } else {
                    let commonPrefix = '';
                    if (matches.length > 0) {
                        const firstMatch = matches[0];
                        for (let i = 0; i < firstMatch.length; i++) {
                            const char = firstMatch[i];
                            if (matches.every(match => match[i] === char)) {
                                commonPrefix += char;
                            } else {
                                break;
                            }
                        }
                    }
                    if (commonPrefix) {
                        lastCommandLineDiv.textContent = promptText + commonPrefix;
                        const range = document.createRange();
                        const sel = window.getSelection();
                        range.selectNodeContents(lastCommandLineDiv);
                        range.collapse(false);
                        sel.removeAllRanges();
                        sel.addRange(range);
                    }
                }
                lastTabPressTime = currentTime;
                lastInputOnTab = currentInput;
            }
            return;
        }
        // If a menu is active, handle menu navigation
        if (currentMenuItems.length > 0) {
            const selectedItem = handleMenuNavigation(e, terminal);
            if (selectedItem) {
                // The menu handler now manages contenteditable state
            }
            return; // Prevent further processing if menu is active
        }

        // Prevent deletion of the prompt and previous output/commands
        if (e.key === 'Backspace' || e.key === 'Delete') {
            const selection = window.getSelection();
            const range = selection.getRangeAt(0);

            const currentCommandLineDiv = range.commonAncestorContainer.closest('.command-line');
            const lastCommandLineDiv = terminal.querySelector('.command-line:last-of-type');

            // Prevent deletion if the cursor is not in the last command line div
            if (!currentCommandLineDiv || currentCommandLineDiv !== lastCommandLineDiv) {
                e.preventDefault();
                return;
            }

            // If the cursor is in the last command line div, prevent deletion of the prompt area
            const promptSpan = currentCommandLineDiv.querySelector('.prompt');
            if (promptSpan && promptSpan.firstChild) { // Ensure promptSpan and its text node exist
                const promptRange = document.createRange();
                promptRange.setStart(promptSpan.firstChild, 0);
                promptRange.setEnd(promptSpan.firstChild, promptSpan.textContent.length);

                // If the selection starts before or within the prompt, prevent deletion
                if (range.compareBoundaryPoints(Range.START_TO_START, promptRange) <= 0) {
                    e.preventDefault();
                    return;
                }
            }
        }

        if (e.key === 'ArrowLeft') {
            const selection = window.getSelection();
            const range = selection.getRangeAt(0);

            const currentCommandLineDiv = range.commonAncestorContainer.closest('.command-line');

            if (currentCommandLineDiv) {
                const promptNode = currentCommandLineDiv.querySelector('.prompt');
                if (promptNode && range.commonAncestorContainer.isSameNode(promptNode.firstChild) && range.startOffset <= promptNode.textContent.length) {
                    e.preventDefault();
                    return;
                }
            }
        }

        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent default new line behavior for Enter key

            // Get the last command line div
            const lastCommandLineDiv = terminal.querySelector('.command-line:last-of-type');
            if (lastCommandLineDiv) {
                // Get the text content, excluding the prompt text
                const promptSpan = lastCommandLineDiv.querySelector('.prompt');
                let command = '';
                if (promptSpan) {
                    const fullLineText = lastCommandLineDiv.textContent.trim(); // Keep trimming fullLineText
                    // Use staticPromptString for comparison and replacement
                    if (fullLineText.startsWith(staticPromptString.trim())) {
                        const promptIndex = fullLineText.indexOf(staticPromptString);
                        if (promptIndex !== -1) {
                            command = fullLineText.substring(promptIndex + staticPromptString.length).trim();
                        } else {
                            command = fullLineText.trim(); // Fallback if prompt not found
                        }
                    } else {
                        // Fallback: if prompt not found or doesn't match exactly, treat the whole line as command
                        // This case should ideally not be hit if prompt handling is consistent
                        command = fullLineText.trim();
                    }
                } else {
                    // Fallback if no prompt span is found (shouldn't happen after initial prompt)
                    command = lastCommandLineDiv.textContent.trim();
                }

                // Process the command
                await handleCommand(terminal, command);
            } else {
                // Fallback if no command line div is found (shouldn't happen after initial prompt)
                addNewPromptLine(terminal);
            }
        }
    });
});