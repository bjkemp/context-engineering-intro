/**
 * Core inventory management system for CYOA game engine
 * Agent 2: Game Engine & Logic
 */

class InventoryManager {
    constructor(initialInventory = {}) {
        this.inventory = { ...initialInventory };
    }

    /**
     * Add item(s) to inventory
     * @param {string} itemName - Name of the item
     * @param {number} quantity - Quantity to add (default: 1)
     */
    addItem(itemName, quantity = 1) {
        if (!itemName || quantity <= 0) return false;
        
        this.inventory[itemName] = (this.inventory[itemName] || 0) + quantity;
        console.log(`Added ${quantity}x ${itemName} to inventory`);
        return true;
    }

    /**
     * Remove item(s) from inventory
     * @param {string} itemName - Name of the item
     * @param {number} quantity - Quantity to remove (default: 1)
     * @returns {boolean} - Success/failure
     */
    removeItem(itemName, quantity = 1) {
        if (!itemName || quantity <= 0) return false;
        if (!this.hasItem(itemName, quantity)) return false;

        this.inventory[itemName] -= quantity;
        if (this.inventory[itemName] <= 0) {
            delete this.inventory[itemName];
        }
        
        console.log(`Removed ${quantity}x ${itemName} from inventory`);
        return true;
    }

    /**
     * Check if inventory contains item(s)
     * @param {string} itemName - Name of the item
     * @param {number} requiredQuantity - Required quantity (default: 1)
     * @returns {boolean} - Has item or not
     */
    hasItem(itemName, requiredQuantity = 1) {
        if (!itemName) return false;
        return (this.inventory[itemName] || 0) >= requiredQuantity;
    }

    /**
     * Get quantity of specific item
     * @param {string} itemName - Name of the item
     * @returns {number} - Quantity of item
     */
    getItemQuantity(itemName) {
        return this.inventory[itemName] || 0;
    }

    /**
     * Get list of all items with quantities
     * @returns {Array} - Array of {name, quantity} objects
     */
    getInventoryList() {
        return Object.entries(this.inventory).map(([name, quantity]) => ({
            name: name,
            quantity: quantity,
            displayName: this.formatItemName(name)
        }));
    }

    /**
     * Format item name for display (replace underscores with spaces, capitalize)
     * @param {string} itemName - Raw item name
     * @returns {string} - Formatted display name
     */
    formatItemName(itemName) {
        return itemName
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Check inventory condition from choice parsing
     * @param {string} condition - Condition string (e.g., "training_lightsaber:1")
     * @returns {boolean} - Condition met or not
     */
    checkInventoryCondition(condition) {
        if (!condition || typeof condition !== 'string') return true;
        
        // Handle different condition formats
        if (condition.includes(':')) {
            const [itemName, quantityStr] = condition.split(':').map(s => s.trim());
            const quantity = parseInt(quantityStr) || 1;
            return this.hasItem(itemName, quantity);
        } else {
            // Simple item name check (quantity = 1)
            return this.hasItem(condition.trim(), 1);
        }
    }

    /**
     * Apply inventory consequence from choice selection
     * @param {string} consequence - Consequence string (e.g., "USE training_lightsaber:1", "SET gold_coins:+5")
     * @returns {boolean} - Success/failure
     */
    applyInventoryConsequence(consequence) {
        if (!consequence || typeof consequence !== 'string') return false;

        const trimmed = consequence.trim();
        
        if (trimmed.startsWith('USE ')) {
            // Remove/consume item
            const itemSpec = trimmed.substring(4).trim();
            const [itemName, quantityStr] = itemSpec.includes(':') 
                ? itemSpec.split(':').map(s => s.trim())
                : [itemSpec, '1'];
            const quantity = parseInt(quantityStr) || 1;
            return this.removeItem(itemName, quantity);
            
        } else if (trimmed.startsWith('SET ') && trimmed.includes('inventory:')) {
            // Set inventory item
            const spec = trimmed.substring(4).trim();
            if (spec.startsWith('inventory:')) {
                const itemSpec = spec.substring(10);
                const [itemName, quantityStr] = itemSpec.split(':').map(s => s.trim());
                const quantity = parseInt(quantityStr) || 1;
                
                if (quantity > 0) {
                    return this.addItem(itemName, quantity);
                } else if (quantity < 0) {
                    return this.removeItem(itemName, Math.abs(quantity));
                }
            }
        }
        
        return false;
    }

    /**
     * Get total number of items in inventory
     * @returns {number} - Total item count
     */
    getTotalItemCount() {
        return Object.values(this.inventory).reduce((sum, quantity) => sum + quantity, 0);
    }

    /**
     * Check if inventory is empty
     * @returns {boolean} - Is empty or not
     */
    isEmpty() {
        return Object.keys(this.inventory).length === 0;
    }

    /**
     * Clear all items from inventory
     */
    clear() {
        this.inventory = {};
        console.log('Inventory cleared');
    }

    /**
     * Serialize inventory for save system
     * @returns {Object} - Serializable inventory data
     */
    serialize() {
        return {
            inventory: { ...this.inventory },
            totalItems: this.getTotalItemCount()
        };
    }

    /**
     * Deserialize inventory from save data
     * @param {Object} data - Saved inventory data
     * @returns {InventoryManager} - New inventory manager instance
     */
    static deserialize(data) {
        if (!data || !data.inventory) {
            return new InventoryManager();
        }
        return new InventoryManager(data.inventory);
    }

    /**
     * Get inventory summary for display
     * @returns {string} - Human-readable inventory summary
     */
    getSummary() {
        if (this.isEmpty()) {
            return 'Inventory is empty';
        }

        const items = this.getInventoryList();
        const summary = items.map(item => 
            `${item.displayName} (${item.quantity})`
        ).join(', ');
        
        return `Items: ${summary} [Total: ${this.getTotalItemCount()}]`;
    }
}

// Create global inventory manager instance
let globalInventoryManager = new InventoryManager();

/**
 * Get the global inventory manager instance
 * @returns {InventoryManager} - Global inventory manager
 */
const getInventoryManager = () => globalInventoryManager;

/**
 * Initialize inventory manager with game data
 * @param {Object} gameData - Parsed game data from .adv file
 */
const initializeInventory = (gameData) => {
    if (gameData && gameData.inventory) {
        globalInventoryManager = new InventoryManager(gameData.inventory);
        console.log('Inventory initialized with game data:', gameData.inventory);
    } else {
        globalInventoryManager = new InventoryManager();
        console.log('Inventory initialized empty');
    }
};

/**
 * Reset inventory manager (for new games)
 */
const resetInventory = () => {
    globalInventoryManager = new InventoryManager();
    console.log('Inventory reset for new game');
};

export { 
    InventoryManager, 
    getInventoryManager, 
    initializeInventory, 
    resetInventory 
};