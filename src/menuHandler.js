let selectedMenuItemIndex = 0;
let currentMenuItems = []; // To store menu items for navigation
let menuJustActivated = false;
let currentMenuType = 'main'; // 'main', 'options', 'font_size', or 'font_color'
let gameData = {}; // To store the parsed game data
let isGoingBack = false; // New flag to indicate if navigation is a "back" action

import { getUserName, setUserName } from './gameState.js';
import { saveGameState, loadGameState, pushStoryToHistory, goBackInHistory, canGoBack, clearStoryHistory, getSerializableGameState } from './gameState.js';
import { getInventoryManager } from './inventoryManager.js';
import { handleCommand } from './commandHandler.js';
import { addNewPromptLine, displayGameIntro, setFontSize, setFontColor, resetTerminalStyles } from './terminal.js';
import { askUserName } from './userInput.js';

// Options menu items
const optionsMenuItems = [
    'Font Size',
    'Font Color',
    'Back'
];

// Font Size menu items
const fontSizeMenuItems = [
    '12px',
    '14px',
    '16px (Default)',
    '18px',
    '20px',
    'Back'
];

// Font Color menu items (ROYGBIV + others for 10 total)
const fontColorMenuItems = [
    'Red',
    'Orange',
    'Yellow',
    'Green',
    'Blue',
    'Indigo',
    'Violet',
    'White (Default)',
    
    'Cyan',
    'Back'
];

// Function to render interactive menu items
const renderMenuItems = (terminal) => {
    // Remove existing menu items if any, to prevent duplicates on re-render
    const existingMenuItems = terminal.querySelectorAll('.menu-item');
    existingMenuItems.forEach(item => item.remove());

    currentMenuItems.forEach((item, index) => {
        const menuItemSpan = document.createElement('span');
        menuItemSpan.className = 'menu-item'; // Add a class for easy selection
        
        // Add selected class for enhanced styling
        if (index === selectedMenuItemIndex) {
            menuItemSpan.classList.add('selected');
        }
        
        menuItemSpan.textContent = `${index === selectedMenuItemIndex ? '> ' : '  '}- ${item}\n`;
        if (index === selectedMenuItemIndex) {
            menuItemSpan.style.color = 'yellow'; // Highlight selected item
        } else {
            menuItemSpan.style.color = 'white';
        }
        terminal.appendChild(menuItemSpan);
    });
    terminal.scrollTop = terminal.scrollHeight;
};

// Function to display the main menu
const displayMainMenu = (terminal, data) => {
    gameData = data; // Store the full game data
    
    // Add fade out transition before clearing
    terminal.classList.add('fade-out');
    
    setTimeout(() => {
        terminal.innerHTML = ''; // Clear terminal before displaying menu
        terminal.classList.remove('fade-out');
        terminal.setAttribute('contenteditable', 'false'); // Disable editing while menu is active
        clearStoryHistory(); // Clear history when starting a new game or returning to main menu
        currentMenuItems = gameData.mainMenuItems; // Set main menu items
        currentMenuType = 'main'; // Set menu type to main
        selectedMenuItemIndex = 0; // Reset selection

        const menuTitleSpan = document.createElement('span');
        menuTitleSpan.textContent = `Main Menu:\n`;
        menuTitleSpan.className = 'menu-slide-up';
        terminal.appendChild(menuTitleSpan);

        // Add animation delay to menu items
        setTimeout(() => {
            renderMenuItems(terminal); // Call the new function to render interactive menu
        }, 100);

        terminal.scrollTop = terminal.scrollHeight;
        terminal.focus(); // Ensure terminal is focused for keyboard input
    }, 150);
};

// Function to display story content and choices for a given step
const displayStoryAndMenu = (terminal, stepKey) => {
    // Only push to history if we are not going back and there's a current step to push
    if (!isGoingBack && gameData.currentStep) {
        pushStoryToHistory(gameData.currentStep);
    }
    isGoingBack = false; // Reset the flag after handling

    gameData.currentStep = stepKey;
    
    // Add smooth transition
    terminal.classList.add('fade-out');
    
    setTimeout(() => {
        terminal.innerHTML = ''; // Clear terminal
        terminal.classList.remove('fade-out');
        terminal.setAttribute('contenteditable', 'false'); // Disable editing
    }, 150);
    
    const step = gameData.steps[stepKey];
    if (!step) {
        addNewPromptLine(terminal, `Error: Step ${stepKey} not found.`);
        return;
    }

    let narrative = step.narrative;
    if (getUserName()) {
        narrative = narrative.replace(/\[USER\]/g, getUserName());
    }

    const storySpan = document.createElement('span');
    storySpan.textContent = narrative + '\n\n';
    terminal.appendChild(storySpan);

    // Check if there are choices for this step
    if (step.choices && step.choices.length > 0) {
        currentMenuItems = step.choices.map(choice => {
            let description = choice.description;
            if (getUserName()) {
                description = description.replace(/\[USER\]/g, getUserName());
            }
            return `${choice.label}) ${description}`;
        });
        // Add "Return to the previous page" option if history exists
        if (canGoBack()) {
            const nextChoiceNumber = String.fromCharCode('a'.charCodeAt(0) + currentMenuItems.length);
            currentMenuItems.push(`${nextChoiceNumber}) Return to the previous page`);
        }
        currentMenuType = 'story_choices'; // New menu type for story choices
        selectedMenuItemIndex = 0; // Reset selection
        renderMenuItems(terminal);
    } else {
        // If no choices, it's likely an ending or a step that leads directly to an ending
        // In this case, we should re-enable the prompt line.
        addNewPromptLine(terminal);
        currentMenuItems = []; // Deactivate menu
        currentMenuType = ''; // Reset menu type
    }

    terminal.scrollTop = terminal.scrollHeight;
    terminal.focus();
};


// Function to display the options menu
const displayOptionsMenu = (terminal) => {
    terminal.innerHTML = ''; // Clear terminal
    terminal.setAttribute('contenteditable', 'false'); // Disable editing
    currentMenuItems = optionsMenuItems; // Set options menu items
    currentMenuType = 'options'; // Set menu type to options
    selectedMenuItemIndex = 0; // Reset selection

    const menuTitleSpan = document.createElement('span');
    menuTitleSpan.textContent = `Options Menu:\n`;
    terminal.appendChild(menuTitleSpan);

    renderMenuItems(terminal);
    terminal.scrollTop = terminal.scrollHeight;
    terminal.focus();
};

// Function to display the font size menu
const displayFontSizeMenu = (terminal) => {
    terminal.innerHTML = ''; // Clear terminal
    terminal.setAttribute('contenteditable', 'false'); // Disable editing
    currentMenuItems = fontSizeMenuItems; // Set font size menu items
    currentMenuType = 'font_size'; // Set menu type
    selectedMenuItemIndex = 0; // Reset selection

    const menuTitleSpan = document.createElement('span');
    menuTitleSpan.textContent = `Font Size:\n`;
    terminal.appendChild(menuTitleSpan);

    renderMenuItems(terminal);
    terminal.scrollTop = terminal.scrollHeight;
    terminal.focus();
};

// Function to display the font color menu
const displayFontColorMenu = (terminal) => {
    terminal.innerHTML = ''; // Clear terminal
    terminal.setAttribute('contenteditable', 'false'); // Disable editing
    currentMenuItems = fontColorMenuItems; // Set font color menu items
    currentMenuType = 'font_color'; // Set menu type
    selectedMenuItemIndex = 0; // Reset selection

    const menuTitleSpan = document.createElement('span');
    menuTitleSpan.textContent = `Font Color:\n`;
    terminal.appendChild(menuTitleSpan);

    renderMenuItems(terminal);
    terminal.scrollTop = terminal.scrollHeight;
    terminal.focus();
};

const handleMenuNavigation = async (e, terminal) => {
    if (currentMenuItems.length > 0) {
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedMenuItemIndex = (selectedMenuItemIndex - 1 + currentMenuItems.length) % currentMenuItems.length;
            renderMenuItems(terminal);
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedMenuItemIndex = (selectedMenuItemIndex + 1) % currentMenuItems.length;
            renderMenuItems(terminal);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            
            const selectedItem = currentMenuItems[selectedMenuItemIndex];
            
            // Removed: terminal.setAttribute('contenteditable', 'true'); // Re-enable editing

            if (currentMenuType === 'main') {
                switch (selectedItem) {
                    case 'Start New Game':
                        terminal.style.whiteSpace = 'pre-wrap'; // Ensure pre-wrap is set for story content
                        
                        
                        // Replace [USER] in the narrative of STEP_1
                        if (gameData.steps['1']) {
                            // This block was empty, no action needed here.
                        }
if (gameData.askForName) {
                            const userName = await askUserName(terminal);
                            setUserName(userName);
                        }
                        gameData.currentStep = '1'; // Set the current step to 1
                        
                        // Add a small delay to ensure the terminal is ready for the next display
                        setTimeout(() => {
                            displayStoryAndMenu(terminal, '1'); // Start game at STEP_1
                        }, 50); // 50ms delay
                        
                        return selectedItem; // Indicate menu exited
                    case 'Load Game':
                        const fileInput = document.createElement('input');
                        fileInput.type = 'file';
                        fileInput.accept = '.sadv';
                        fileInput.style.display = 'none';
                        document.body.appendChild(fileInput);
                        fileInput.click();

                        fileInput.addEventListener('change', async (event) => {
                            document.body.removeChild(fileInput);
                            const file = event.target.files[0];
                            if (file) {
                                const fileName = file.name;
                                const fileExtension = fileName.split('.').pop();
                                if (fileExtension === 'sadv') { // Changed from piSav to sadv
                                    // Logic to load game state from .sadv file
                                    const reader = new FileReader();
                                    reader.onload = async (e) => {
                                        const content = e.target.result;
                                        try {
                                            const gameState = JSON.parse(content);
                                            loadGameState(gameState); // Pass the object directly
                                            // After loading, display the current step from the loaded game state
                                            if (gameState.currentStep) {
                                                gameData.currentStep = gameState.currentStep; // Update gameData's currentStep
                                                displayStoryAndMenu(terminal, gameState.currentStep);
                                            } else {
                                                addNewPromptLine(terminal, `Loaded game state, but no current step found.`);
                                            }
                                            return selectedItem; // Indicate menu exited
                                        } catch (parseError) {
                                            addNewPromptLine(terminal, `Error parsing save file: ${parseError.message}`);
                                            return selectedItem; // Indicate menu exited
                                        }
                                    };
                                    reader.readAsText(file);
                                } else {
                                    addNewPromptLine(terminal, `Error: Incorrect file type. Please select a .sadv file.`);
                                    return selectedItem; // Indicate menu exited
                                }
                            } else {
                                addNewPromptLine(terminal); // Add prompt if no file selected
                                return selectedItem; // Indicate menu exited
                            }
                        });
                        break; // Break here to avoid fall-through after async operation
                    case 'Options':
                        displayOptionsMenu(terminal); // Show options menu
                        break;
                    case 'Exit':
                        terminal.innerHTML = ''; // Clear terminal
                        addNewPromptLine(terminal); // Add new prompt line
                        currentMenuItems = []; // Deactivate menu navigation
                        return selectedItem; // Indicate menu exited
                    default:
                        addNewPromptLine(terminal);
                        break;
                }
            } else if (currentMenuType === 'options') {
                switch (selectedItem) {
                    case 'Font Size':
                        displayFontSizeMenu(terminal);
                        break;
                    case 'Font Color':
                        displayFontColorMenu(terminal);
                        break;
                    case 'Back':
                        // If in options menu, return to command prompt
                        terminal.innerHTML = ''; // Clear terminal
                        addNewPromptLine(terminal); // Add new prompt line
                        currentMenuItems = []; // Deactivate menu navigation
                        break;
                    default:
                        addNewPromptLine(terminal);
                        break;
                }
            } else if (currentMenuType === 'font_size') {
                switch (selectedItem) {
                    case '12px':
                    case '14px':
                    case '16px (Default)':
                    case '18px':
                    case '20px':
                        setFontSize(terminal, selectedItem.replace(' (Default)', ''));
                        displayOptionsMenu(terminal); // Return to options menu
                        break;
                    case 'Back': // Changed from 'Back to Options'
                        displayOptionsMenu(terminal);
                        break;
                    default:
                        addNewPromptLine(terminal);
                        break;
                }
            } else if (currentMenuType === 'font_color') {
                switch (selectedItem) {
                    case 'Red':
                    case 'Orange':
                    case 'Yellow':
                    case 'Green':
                    case 'Blue':
                    case 'Indigo':
                    case 'Violet':
                    case 'White (Default)':
                    case 'Cyan': // Removed 'Black' as it's not in the menu items
                        setFontColor(terminal, selectedItem.replace(' (Default)', ''));
                        displayOptionsMenu(terminal); // Return to options menu
                        break;
                    case 'Back': // Changed from 'Back to Options'
                        displayOptionsMenu(terminal);
                        break;
                    default:
                        addNewPromptLine(terminal);
                        break;
                }
            } else if (currentMenuType === 'story_choices') {
                // Handle selection of story choices
                const choiceIndex = selectedMenuItemIndex;
                const currentStep = gameData.steps[gameData.currentStep]; // Assuming gameData.currentStep tracks the current step
                if (currentStep && currentStep.choices && currentStep.choices[choiceIndex]) {
                    const targetStep = currentStep.choices[choiceIndex].target.replace('STEP_', '');
                    
                    // Check for endings
                    if (targetStep.startsWith('ENDING_')) {
                        const endingType = targetStep.replace('ENDING_', '').toLowerCase();
                        const endingText = gameData.endings[endingType];
                        if (endingText) {

                            terminal.innerHTML = '';
                            const endingSpan = document.createElement('span');
                            endingSpan.textContent = endingText + '\n\n';
                            terminal.appendChild(endingSpan);

                            // Add the "Congratulations!" message
                            const congratsSpan = document.createElement('span');
                            congratsSpan.classList.add('congratulations-message');
                            congratsSpan.textContent = `Congratulations! You completed ${gameData.gameName}!\n\n`;
                            terminal.appendChild(congratsSpan);

                            // Set new menu items for ending options
                            currentMenuItems = ['Return to the previous page', 'Quit to the command prompt'];
                            currentMenuType = 'ending_options'; // New menu type for ending options
                            selectedMenuItemIndex = 0; // Reset selection
                            renderMenuItems(terminal);
                        } else {
                            addNewPromptLine(terminal, `Error: Ending ${endingType} not found.`);
                        }
                    } else {
                        // This is a forward navigation, so push the current step to history
                        // The pushStoryToHistory is now handled at the beginning of displayStoryAndMenu
                        gameData.currentStep = targetStep; // Update current step in gameData
                        displayStoryAndMenu(terminal, targetStep); // Display the next step
                    }
                } else if (selectedItem.includes('Return to the previous page')) {
                    isGoingBack = true; // Set flag for back navigation
                    const previousStep = goBackInHistory();
                    if (previousStep) {
                        displayStoryAndMenu(terminal, previousStep);
                    } else {
                        addNewPromptLine(terminal, `No previous page to return to.`);
                    }
                } else {
                    addNewPromptLine(terminal, `Invalid choice.`);
                }
            } else if (currentMenuType === 'ending_options') {
                switch (selectedItem) {
                    case 'Return to the previous Page':
                        isGoingBack = true; // Set flag for back navigation
                        // When returning from an ending, go back to the step that led to the ending
                        const previousStepFromHistory = goBackInHistory();
                        if (previousStepFromHistory) {
                            displayStoryAndMenu(terminal, previousStepFromHistory);
                        } else {
                            addNewPromptLine(terminal, `No previous page to return to.`);
                        }
                        break;
                    case 'Quit to command prompt':
                        terminal.innerHTML = ''; // Clear terminal
                        addNewPromptLine(terminal); // Add new prompt line
                        currentMenuItems = []; // Deactivate menu navigation
                        currentMenuType = ''; // Reset menu type
                        break;
                    default:
                        addNewPromptLine(terminal, `Invalid choice.`);
                        break;
                }
            }
        }
    }
    return null; // No item selected or menu not active
};

export { toggleOverlayMenu };
const toggleOverlayMenu = (terminal) => {
    const overlayMenu = document.getElementById('overlay-menu');
    const saveQuitButton = document.getElementById('save-quit-button');
    const returnButton = document.getElementById('return-button');

    if (overlayMenu.classList.contains('visible')) {
        // Hide menu
        overlayMenu.classList.remove('visible');
        terminal.setAttribute('contenteditable', 'true');
        terminal.focus();
        if (gameData.currentStep) {
            displayStoryAndMenu(terminal, gameData.currentStep);
        } else {
            addNewPromptLine(terminal);
        } // Reset currentStep when menu is hidden
    } else {
        // Show menu
        if (!gameData.currentStep) {
            // If not in a game, do not show the menu
            return;
        }
        overlayMenu.classList.add('visible');
        terminal.setAttribute('contenteditable', 'false');
        saveQuitButton.focus(); // Focus on the first button
    }

    saveQuitButton.onclick = () => {
        const gameState = getSerializableGameState(gameData.currentStep); // Get serializable state
        const fileName = `${gameData.gameName || 'adventure'}_${new Date().toISOString().slice(0, 10)}.sadv`;
        const blob = new Blob([JSON.stringify(gameState, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // After saving, hide the menu and return to the main menu or a default state
        toggleOverlayMenu(terminal); // Hide the overlay
        displayMainMenu(terminal, gameData); // Return to main menu
    };
const quitWithoutSavingButton = document.getElementById('quit-without-saving-button');

    returnButton.onclick = () => {
        toggleOverlayMenu(terminal); // Just hide the overlay
    };

    quitWithoutSavingButton.onclick = () => {
        toggleOverlayMenu(terminal); // Hide the overlay
        terminal.innerHTML = ''; // Clear terminal
        addNewPromptLine(terminal); // Add new prompt line
        currentMenuItems = []; // Deactivate menu navigation
        currentMenuType = ''; // Reset menu type
        clearStoryHistory(); // Clear story history
        gameData.currentStep = null; // Ensure game is no longer active
    };
};
export { displayMainMenu, displayStoryAndMenu, handleMenuNavigation, currentMenuItems, displayOptionsMenu };