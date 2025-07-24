const askUserName = (terminal) => {
    return new Promise(resolve => {
        const namePromptSpan = document.createElement('span');
        namePromptSpan.textContent = `\nWhat is your name, adventurer? `;
        terminal.appendChild(namePromptSpan);

        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.className = 'user-input';
        nameInput.style.backgroundColor = 'transparent';
        nameInput.style.border = 'none';
        nameInput.style.color = 'white';
        nameInput.style.outline = 'none';
        nameInput.style.width = 'auto'; // Adjust width dynamically
        nameInput.style.minWidth = '100px'; // Minimum width
        nameInput.style.fontFamily = 'monospace';
        nameInput.style.fontSize = '1em';
        nameInput.style.flexGrow = '1'; // Allow input to grow

        const inputContainer = document.createElement('span');
        inputContainer.appendChild(nameInput);
        terminal.appendChild(inputContainer);

        nameInput.focus();

        nameInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const userName = nameInput.value.trim();
                inputContainer.remove(); // Remove the input field
                namePromptSpan.textContent += userName + '\n'; // Display the entered name
                resolve(userName);
            }
        });
    });
};

export { askUserName };