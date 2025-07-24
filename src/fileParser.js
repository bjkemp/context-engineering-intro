const parseFile = (content) => {
    const gameData = {
        gameName: '',
        mainMenuItems: [],
        inventory: {},
        stats: {},
        variables: {},
        steps: {},
        endings: {
            success: '',
            failure: '',
            neutral: ''
        },
        conditions: [],
        checkpoints: [],
        randomEvents: [],
        consequences: [],
        askForName: false,
        

    };

    const lines = content.split('\n');
    let currentSection = null; // e.g., GAME_NAME, STEP_1, INVENTORY
    let currentSubSection = null; // e.g., NARRATIVE, CHOICES (only within STEP_X)
    let currentContentBuffer = []; // Use a buffer to accumulate lines

    const processBuffer = () => {
        if (currentSubSection) {
            const stepKey = currentSection.replace('STEP_', '');
            if (!gameData.steps[stepKey]) {
                gameData.steps[stepKey] = { narrative: '', choices: [] };
            }
            if (currentSubSection === 'NARRATIVE') {
                gameData.steps[stepKey].narrative = currentContentBuffer.join('\n').trim();
            } else if (currentSubSection === 'CHOICES') {
                gameData.steps[stepKey].choices = parseChoices(currentContentBuffer);
            }
        } else if (currentSection) { // This handles top-level sections like GAME_NAME, MAIN_MENU, ENDING_SUCCESS etc.
            const sectionContent = currentContentBuffer.join('\n').trim();
            switch (currentSection) {
                case 'GAME_NAME':
                    gameData.gameName = sectionContent;
                    break;
                case 'MAIN_MENU':
                    gameData.mainMenuItems = sectionContent.split('\n').map(item => item.trim()).filter(item => item.length > 0);
                    break;
                case 'INVENTORY':
                    gameData.inventory = parseKeyValue(sectionContent);
                    break;
                case 'STATS':
                    gameData.stats = parseKeyValue(sectionContent);
                    break;
                case 'VARIABLES':
                    gameData.variables = parseKeyValue(sectionContent);
                    break;
                case 'ENDING_SUCCESS':
                    gameData.endings.success = sectionContent;
                    break;
                case 'ENDING_FAILURE':
                    gameData.endings.failure = sectionContent;
                    break;
                case 'ENDING_NEUTRAL':
                    gameData.endings.neutral = sectionContent;
                    break;
                case 'CONDITIONS':
                    gameData.conditions = parseConditions(sectionContent);
                    break;
                case 'CHECKPOINT':
                    gameData.checkpoints = parseCheckpoints(sectionContent);
                    break;
                case 'RANDOM_EVENT':
                    gameData.randomEvents = parseRandomEvent(sectionContent);
                    break;
                case 'CONSEQUENCE':
                    gameData.consequences = parseConsequence(sectionContent);
                    break;
                case 'NAME':
                    gameData.askForName = sectionContent.toLowerCase() === 'true';
                    break;
            }
        }
        currentContentBuffer = []; // Always clear buffer after processing
    };

    for (const line of lines) {
        const trimmedLine = line.trim();

        if (trimmedLine.startsWith('[') && trimmedLine.endsWith(']')) {
            processBuffer(); // Process content accumulated for the previous section/sub-section

            const tag = trimmedLine.substring(1, trimmedLine.length - 1);

            if (tag.startsWith('STEP_')) {
                currentSection = tag;
                currentSubSection = null;
                const stepKey = tag.replace('STEP_', '');
                if (!gameData.steps[stepKey]) {
                    gameData.steps[stepKey] = { narrative: '', choices: [] };
                }
            } else if (tag === 'NARRATIVE' || tag === 'CHOICES') {
                if (!currentSection || !currentSection.startsWith('STEP_')) {
                    throw new Error(`Invalid .adv file format: [${tag}] found outside of a [STEP_X] block.`);
                }
                currentSubSection = tag;
            } else if (tag.startsWith('/')) { // Closing tags like [/NARRATIVE], [/CHOICES]
                if (tag === `/${currentSubSection}`) {
                    currentSubSection = null;
                } else if (tag === `/${currentSection}`) {
                    currentSection = null;
                }
                // No need to reset currentContentBuffer here, processBuffer already did it.
            } else { // Other top-level sections
                currentSection = tag;
                currentSubSection = null;
            }
        } else {
            currentContentBuffer.push(line); // Accumulate lines
        }
    }

    processBuffer(); // Process any remaining content at the end of the file

    // Final validation
    if (!gameData.gameName) {
        throw new Error("Invalid .adv file format: Missing [GAME_NAME] section.");
    }
    if (gameData.mainMenuItems.length === 0) {
        throw new Error("Invalid .adv file format: Missing or empty [MAIN_MENU] section.");
    }
    if (Object.keys(gameData.steps).length === 0) {
        throw new Error("Invalid .adv file format: No [STEP_X] sections found.");
    }

    return gameData;
};

// Helper functions
const parseChoices = (contentLines) => {
    const choices = [];
    for (const line of contentLines) {
        const trimmedLine = line.trim();
        // Regex to capture the choice, target, and an optional block for conditions/consequences
        const match = trimmedLine.match(/^([A-D])\)\s*(.+?)\s*(?:->|→)\s*(STEP_\d+|ENDING_SUCCESS|ENDING_FAILURE|ENDING_NEUTRAL)(?:\s*\{\s*(.+?)\s*\})?$/);
        if (match) {
            const choice = {
                label: match[1],
                description: match[2].trim(),
                target: match[3],
                conditions: [],
                consequences: []
            };

            if (match[4]) {
                const extras = match[4].split(';').map(s => s.trim());
                for (const extra of extras) {
                    if (extra.startsWith('IF')) {
                        choice.conditions.push(extra.substring(2).trim());
                    } else if (extra.startsWith('SET') || extra.startsWith('USE')) {
                        choice.consequences.push(extra);
                    }
                }
            }

            choices.push(choice);
        } else if (trimmedLine.length > 0) {
            // Throw an error for malformed lines for stricter parsing
            throw new Error(`Malformed choice line: "${trimmedLine}"`);
        }
    }
    return choices;
};

const parseKeyValue = (content) => {    const obj = {};    content.split('\n').forEach(line => {        const trimmedLine = line.trim();        if (trimmedLine.length === 0) return; // Skip empty lines        if (trimmedLine.includes(':')) {            const parts = trimmedLine.split(':');            if (parts.length !== 2 || !parts[0].trim() || !parts[1].trim()) {                throw new Error(`Malformed key-value line: "${trimmedLine}"`);            }            const key = parts[0].trim();            const value = parts[1].trim();            obj[key] = isNaN(Number(value)) ? value : Number(value); // Convert to number if possible        } else {            throw new Error(`Malformed key-value line: "${trimmedLine}"`);        }    });    return obj;};

const parseConditions = (content) => {
    const conditions = [];
    content.split('\n').forEach(line => {
        const trimmedLine = line.trim();
        if (trimmedLine.length === 0) return; // Skip empty lines
        const match = trimmedLine.match(/^IF\s+(.+)\s+THEN\s+(.+)$/);
        if (match) {
            conditions.push({
                condition: match[1].trim(),
                action: match[2].trim()
            });
        } else {
            throw new Error(`Malformed condition line: "${trimmedLine}"`);
        }
    });
    return conditions;
};

const parseCheckpoints = (content) => {
    return content.split('\n').map(item => item.trim()).filter(item => item.startsWith('STEP_')).map(item => item.replace('STEP_', ''));
};

const parseRandomEvent = (content) => {
    const events = [];
    content.split('\n').forEach(line => {
        const trimmedLine = line.trim();
        if (trimmedLine.length === 0) return; // Skip empty lines
        const parts = trimmedLine.split(',').map(p => p.trim());
        const event = {};
        parts.forEach(part => {
            const [key, value] = part.split(':').map(s => s.trim());
            if (key === 'chance') {
                event.chance = parseFloat(value);
            } else if (key === 'outcome') {
                event.outcome = value; // e.g., STEP_X
            }
        });
        if (event.chance && event.outcome) {
            events.push(event);
        } else {
            throw new Error(`Malformed random event line: "${trimmedLine}"`);
        }
    });
    return events;
};

const parseConsequence = (content) => {
    const consequences = [];
    content.split('\n').forEach(line => {
        const trimmedLine = line.trim();
        if (trimmedLine.length === 0) return; // Skip empty lines
        const actions = trimmedLine.split(',').map(action => action.trim());
        const consequence = {};
        actions.forEach(action => {
            const parts = action.split(':');
            if (parts.length === 2) {
                const target = parts[0].trim();
                const value = parts[1].trim();
                consequence[target] = isNaN(Number(value)) ? value : Number(value);
            } else {
                throw new Error(`Malformed consequence action: "${action}"`);
            }
        });
        if (Object.keys(consequence).length > 0) {
            consequences.push(consequence);
        } else {
            throw new Error(`Malformed consequence line: "${trimmedLine}"`);
        }
    });
    return consequences;
};

export { parseFile };