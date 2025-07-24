import { addNewPromptLine, displayGameIntro, resetTerminalStyles, applyAnimation } from './terminal.js';
import { parseFile } from './fileParser.js';
import { getInventoryManager, initializeInventory } from './inventoryManager.js';

import { displayStoryAndMenu, currentMenuItems, displayOptionsMenu, displayMainMenu } from './menuHandler.js';
import { setUserName, getUserName, getInventorySummary } from './gameState.js';

const handleCommand = async (terminal, command) => {
    
    // Robustly clean the command string to handle various whitespace and invisible characters
    
    let cleanedCommand = String(command || '').normalize('NFC');
    cleanedCommand = cleanedCommand.replace(/[^\x20-\x7E]/g, ''); // Remove non-printable ASCII characters
    cleanedCommand = cleanedCommand.replace(/\s+/g, ' ').trim(); // Normalize whitespace and trim

    const parts = cleanedCommand.split(' ');
    const baseCommand = parts[0].toLowerCase();
    const args = parts.slice(1);
    if (baseCommand === 'load') {
        if (args.length > 0) {
            addNewPromptLine(terminal, `Direct file loading by path is not supported in the browser. Please use 'load' without arguments to open the file dialog.`);
            return;
        }
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.adv';
        fileInput.style.display = 'none';

        document.body.appendChild(fileInput);
        fileInput.click();

        fileInput.addEventListener('change', async (event) => {
terminal.setAttribute('contenteditable', 'true'); // Re-enable editing immediately
            document.body.removeChild(fileInput);

            const file = event.target.files[0];
            if (file) {
                const fileName = file.name;
                const fileExtension = fileName.split('.').pop();

                if (fileExtension === 'adv') {
                    const reader = new FileReader();
                    reader.onload = async (e) => {
                        const content = e.target.result;
                        // Show loading feedback
                        const loadingSpan = document.createElement('span');
                        loadingSpan.innerHTML = '<span class="loading-spinner"></span>Loading adventure...';
                        loadingSpan.className = 'command-loading';
                        terminal.appendChild(loadingSpan);
                        terminal.appendChild(document.createElement('br'));
                        
                        // Small delay to show loading animation
                        setTimeout(() => {
                            try {
                                const gameData = parseFile(content);
                                if (gameData) {
                                    // Remove loading indicator
                                    terminal.removeChild(loadingSpan);
                                    terminal.removeChild(terminal.lastChild); // Remove the <br>
                                    
                                    // Show success feedback
                                    const successSpan = document.createElement('span');
                                    successSpan.textContent = `✅ Successfully loaded: ${file.name}`;
                                    successSpan.className = 'command-success-enhanced';
                                    terminal.appendChild(successSpan);
                                    terminal.appendChild(document.createElement('br'));
                                    
                                    const gameName = gameData.gameName;
                                    const mainMenuItems = gameData.mainMenuItems;
                                    
                                    // Initialize inventory with game data
                                    initializeInventory(gameData);
                                    
                                    if (gameData.askForName) {
                                        // Handle name input if required
                                    }

                                    displayGameIntro(terminal, gameData.gameName);
                                    // Replace [USER] with the actual user name if it exists
                                    if (getUserName()) {
                                        gameData.mainMenuItems = gameData.mainMenuItems.map(item => item.replace(/\[USER\]/g, getUserName()));
                                    }
                                    displayMainMenu(terminal, gameData);
                            } else {
                                const errorSpan = document.createElement('span');
                                errorSpan.textContent = `Error: Could not parse .adv file content.\n`;
                                terminal.appendChild(errorSpan);
                                addNewPromptLine(terminal);
                            }
                        } catch (parseError) {
                            // Remove loading indicator
                            if (terminal.contains(loadingSpan)) {
                                terminal.removeChild(loadingSpan);
                                terminal.removeChild(terminal.lastChild); // Remove the <br>
                            }
                            
                            const errorSpan = document.createElement('span');
                            errorSpan.textContent = `❌ Error parsing .adv file: ${parseError.message}\n`;
                            errorSpan.className = 'command-error';
                            terminal.appendChild(errorSpan);
                            addNewPromptLine(terminal);
                        }
                        }, 800); // 800ms delay to show loading animation
                    };
                    reader.readAsText(file);
                } else {
                    const errorSpan = document.createElement('span');
                    errorSpan.textContent = `❌ Error: Incorrect file type. Please select a .adv file.\n`;
                    errorSpan.className = 'command-error';
                    terminal.appendChild(errorSpan);
                    addNewPromptLine(terminal);
                }
            } else {
                addNewPromptLine(terminal);
            }
        });
    } else if (baseCommand === 'quit' || baseCommand === 'exit') {
        resetTerminalStyles(terminal); // Reset styles before closing
        window.open('', '_self').close();
    } else if (baseCommand === 'options') {
        displayOptionsMenu(terminal);
    } else if (baseCommand === 'help') {
        const helpMessages = [
            `Available Commands:`,
            `  load - Load a .adv file`,
            `  inventory - Display current inventory`,
            `  options - Display options menu`,
            `  quit - Close the terminal window`,
            `  help - Display this help message`,
            `  clear - Clear the terminal`
        ];
        helpMessages.forEach(msg => {
            const helpSpan = document.createElement('span');
            const helpParts = msg.split(' - ');
            const commandSpan = document.createElement('span');
            commandSpan.style.color = 'rgb(255,255,0)'; // Yellow color for command
            commandSpan.textContent = helpParts[0];
            terminal.appendChild(commandSpan);

            if (helpParts.length > 1) {
                const descriptionSpan = document.createElement('span');
                descriptionSpan.style.color = 'white'; // White color for description
                descriptionSpan.textContent = ' - ' + helpParts.slice(1).join(' - ');
                terminal.appendChild(descriptionSpan);
            }
            terminal.appendChild(helpSpan);
            terminal.appendChild(document.createElement('br'));
        });
        addNewPromptLine(terminal);
    } else if (baseCommand === 'clear') {
        // Add fade out effect before clearing
        terminal.style.opacity = '0.5';
        setTimeout(() => {
            terminal.innerHTML = '';
            terminal.style.opacity = '1';
            addNewPromptLine(terminal);
        }, 200);
    } else if (baseCommand === 'inventory' || baseCommand === 'items') {
        const inventoryManager = getInventoryManager();
        
        if (inventoryManager.isEmpty()) {
            const emptySpan = document.createElement('span');
            emptySpan.textContent = '📦 Your inventory is empty.\n';
            emptySpan.style.color = '#888';
            terminal.appendChild(emptySpan);
        } else {
            const titleSpan = document.createElement('span');
            titleSpan.textContent = '📦 Current Inventory:\n';
            titleSpan.style.color = '#00ff00';
            titleSpan.style.fontWeight = 'bold';
            terminal.appendChild(titleSpan);
            
            const items = inventoryManager.getInventoryList();
            items.forEach(item => {
                const itemSpan = document.createElement('span');
                itemSpan.textContent = `  • ${item.displayName} (${item.quantity})\n`;
                itemSpan.style.color = 'white';
                terminal.appendChild(itemSpan);
            });
            
            const summarySpan = document.createElement('span');
            summarySpan.textContent = `\nTotal items: ${inventoryManager.getTotalItemCount()}\n`;
            summarySpan.style.color = '#888';
            terminal.appendChild(summarySpan);
        }
        
        addNewPromptLine(terminal);
    } else {
        const errorSpan = document.createElement('span');
        errorSpan.textContent = `❌ ${command}: command not found\n`;
        errorSpan.className = 'command-error';
        terminal.appendChild(errorSpan);
        addNewPromptLine(terminal);
    }
};

export { handleCommand };