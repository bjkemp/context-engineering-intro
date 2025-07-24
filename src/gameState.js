import { getInventoryManager, InventoryManager } from './inventoryManager.js';

const saveGameState = (gameName, slot, gameState) => {
    try {
        const savestateKey = `piGameSavestate_${gameName}_${slot}`;
        localStorage.setItem(savestateKey, JSON.stringify(gameState));
        console.log(`Game state for ${gameName} in slot ${slot} saved successfully.`);
        return true;
    } catch (error) {
        console.error('Error saving game state:', error);
        return false;
    }
};

// This function will now load state from localStorage for a given slot
const loadGameState = (gameName, slot) => {
    try {
        const savestateKey = `piGameSavestate_${gameName}_${slot}`;
        const savedStateJSON = localStorage.getItem(savestateKey);

        if (savedStateJSON) {
            const gameStateObject = JSON.parse(savedStateJSON);
            setUserName(gameStateObject.userName || '');
            storyHistory = gameStateObject.storyHistory || [];
            currentHistoryIndex = gameStateObject.currentHistoryIndex !== undefined ? gameStateObject.currentHistoryIndex : -1;
            gameStats = gameStateObject.gameStats || { playTime: 0, choicesMade: 0 };
            
            // Restore inventory if saved
            if (gameStateObject.inventory) {
                const inventoryManager = getInventoryManager();
                const restoredInventory = InventoryManager.deserialize(gameStateObject.inventory);
                Object.assign(inventoryManager, restoredInventory);
            }
            console.log(`Game state for ${gameName} from slot ${slot} loaded successfully.`);
            return gameStateObject; // Return the object for other modules to use (e.g., to get currentStep)
        } else {
            console.log(`No game state found for ${gameName} in slot ${slot}.`);
            return null;
        }
    } catch (error) {
        console.error('Error loading game state:', error);
        return null;
    }
};

const listSaveGames = (gameName) => {
    const saves = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith(`piGameSavestate_${gameName}_`)) {
            const slot = key.substring(key.lastIndexOf('_') + 1);
            saves.push(slot);
        }
    }
    return saves;
};

const incrementChoicesMade = () => {
    gameStats.choicesMade++;
};

const updatePlayTime = (time) => {
    gameStats.playTime += time;
};

let storyHistory = [];
let currentHistoryIndex = -1; // -1 indicates no history yet, or at the very beginning
let gameStats = { playTime: 0, choicesMade: 0 };

const pushStoryToHistory = (story) => {
    // If we've gone back in history and then move forward,
    // clear any "future" history before pushing a new story.
    if (currentHistoryIndex < storyHistory.length - 1) {
        storyHistory = storyHistory.slice(0, currentHistoryIndex + 1);
    }
    storyHistory.push(story);
    currentHistoryIndex = storyHistory.length - 1;
};

const goBackInHistory = () => {
    if (currentHistoryIndex > 0) {
        currentHistoryIndex--;
        return storyHistory[currentHistoryIndex];
    }
    return null;
};

const canGoBack = () => {
    return currentHistoryIndex > 0;
};

const clearStoryHistory = () => {
    storyHistory = [];
    currentHistoryIndex = -1;
};

let userName = '';

const setUserName = (name) => {
    userName = name;
};

const getUserName = () => {
    return userName;
};

// New function to get the current serializable game state
const getSerializableGameState = (currentStep) => {
    return {
        userName: userName,
        storyHistory: storyHistory,
        currentHistoryIndex: currentHistoryIndex,
        currentStep: currentStep, // Include currentStep from menuHandler's gameData
        gameStats: gameStats,
        inventory: getInventoryManager().serialize() // Include inventory state
    };
};

// New inventory-related functions
const getInventory = () => {
    return getInventoryManager().getInventoryList();
};

const getInventorySummary = () => {
    return getInventoryManager().getSummary();
};

const hasInventoryItem = (itemName, quantity = 1) => {
    return getInventoryManager().hasItem(itemName, quantity);
};

export { saveGameState, loadGameState, listSaveGames, storyHistory, pushStoryToHistory, goBackInHistory, canGoBack, clearStoryHistory, setUserName, getUserName, getSerializableGameState, incrementChoicesMade, updatePlayTime, getInventory, getInventorySummary, hasInventoryItem };
