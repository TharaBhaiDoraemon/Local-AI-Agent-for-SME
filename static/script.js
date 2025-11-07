// API base URL
const API_BASE = '';

// DOM elements
const questionForm = document.getElementById('question-form');
const questionInput = document.getElementById('question-input');
const chatMessages = document.getElementById('chat-messages');
const fileUpload = document.getElementById('file-upload');
const documentsList = document.getElementById('documents-list');
const statusText = document.querySelector('.status-text');
const docCount = document.getElementById('doc-count');
const newChatBtn = document.getElementById('new-chat-btn');
const newGroupBtn = document.getElementById('new-group-btn');
const chatList = document.getElementById('chat-list');
const refreshDocumentsBtn = document.getElementById('refresh-documents-btn');
const voiceChatBtn = document.getElementById('voice-chat-btn');
const microphoneSelect = document.getElementById('microphone-select');

// Voice recognition
let recognition = null;
let isRecognizing = false;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        questionInput.value = transcript;
        stopRecognition();
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        showNotification(`Speech recognition error: ${event.error}`, 'error');
        stopRecognition();
    };

    recognition.onend = () => {
        if (isRecognizing) {
            stopRecognition();
        }
    };
} else {
    console.warn('Speech Recognition API not supported in this browser.');
}

// Profile elements
const profileModal = document.getElementById('profile-modal');
const createProfileModal = document.getElementById('create-profile-modal');
const pinModal = document.getElementById('pin-modal');
const profileSettingsModal = document.getElementById('profile-settings-modal');
const profileList = document.getElementById('profile-list');
const createProfileBtn = document.getElementById('create-profile-btn');
const createProfileForm = document.getElementById('create-profile-form');
const pinForm = document.getElementById('pin-form');
const profileSettingsForm = document.getElementById('profile-settings-form');
const switchProfileBtn = document.getElementById('switch-profile-btn');
const profileSettingsBtn = document.getElementById('profile-settings-btn');
const profileNameDisplay = document.getElementById('profile-name-display');

// Current state
let currentProfile = null;
let currentChatId = null;
let collapsedGroups = new Set();
let selectedProfileForPin = null;

// Theme management
const themeBtn = document.getElementById('theme-btn');
const themeDropdown = document.getElementById('theme-dropdown');
const darkModeBtn = document.getElementById('dark-mode-btn');
let themeColors = null; // Will be initialized after DOM is fully loaded

// Theme lists
const darkShades = ['slate', 'zinc', 'stone', 'gray', 'neutral', 'charcoal', 'midnight', 'onyx'];
const colorThemes = ['blue', 'purple', 'green', 'orange', 'pink', 'teal', 'red', 'indigo', 'emerald', 'amber', 'cyan'];

// Initialize the app
async function init() {
    // Initialize theme colors
    themeColors = document.querySelectorAll('.theme-color');

    // Load saved theme and dark mode
    loadTheme();

    // Show profile selection
    await loadProfiles();

    // Set up event listeners
    questionForm.addEventListener('submit', handleQuestionSubmit);
    fileUpload.addEventListener('change', handleFileUpload);
    newChatBtn.addEventListener('click', createNewChat);
    newGroupBtn.addEventListener('click', createNewGroup);
    refreshDocumentsBtn.addEventListener('click', async () => {
        await loadDocuments();
        showNotification('Documents refreshed!', 'success');
    });

    // Profile event listeners
    createProfileBtn.addEventListener('click', showCreateProfileModal);
    createProfileForm.addEventListener('submit', handleCreateProfile);
    document.getElementById('cancel-profile-btn').addEventListener('click', () => {
        createProfileModal.classList.remove('show');
        profileModal.classList.add('show');
    });
    pinForm.addEventListener('submit', handlePinSubmit);
    document.getElementById('cancel-pin-btn').addEventListener('click', () => {
        pinModal.classList.remove('show');
        profileModal.classList.add('show');
    });
    document.getElementById('show-hint-btn').addEventListener('click', showPinHint);
    switchProfileBtn.addEventListener('click', showProfileSelector);

    // Theme selector
    themeBtn.addEventListener('click', toggleThemeDropdown);
    darkModeBtn.addEventListener('click', toggleDarkMode);

    themeColors.forEach(color => {
        color.addEventListener('click', () => {
            const theme = color.dataset.theme;
            if (darkShades.includes(theme)) {
                changeDarkShade(theme);
            } else {
                changeColorTheme(theme);
            }
        });
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.theme-selector')) {
            themeDropdown.classList.remove('show');
        }
    });

    // Voice chat event listener
    if (voiceChatBtn) {
        voiceChatBtn.addEventListener('click', toggleRecognition);
    }

    // Auto-resize textarea
    questionInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Submit on Enter key (without Shift/Ctrl/Alt)
    questionInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey) {
            e.preventDefault(); // Prevent default Enter behavior (new line)
            // Create a proper submit event that can be cancelled
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
            questionForm.dispatchEvent(submitEvent); // Trigger form submission
        }
    });
}

// Profile Management Functions
async function loadProfiles() {
    try {
        const response = await fetch(`${API_BASE}/api/profiles`);
        const profiles = await response.json();

        profileList.innerHTML = '';

        profiles.forEach(profile => {
            const profileItem = createProfileItem(profile);
            profileList.appendChild(profileItem);
        });

        profileModal.classList.add('show');
    } catch (error) {
        console.error('Error loading profiles:', error);
        showNotification('Error loading profiles', 'error');
    }
}

function createProfileItem(profile) {
    const div = document.createElement('div');
    div.className = 'profile-item';
    div.onclick = () => selectProfile(profile);

    const initial = profile.name.charAt(0).toUpperCase();
    const hasPin = profile.has_pin === true;
    const guestClass = profile.is_guest ? 'guest' : '';

    div.innerHTML = `
        <div class="profile-item-info">
            <div class="profile-avatar ${guestClass}">${initial}</div>
            <div class="profile-details">
                <div class="profile-item-name">${profile.name}</div>
                <div class="profile-item-badge">
                    ${hasPin ? `<svg class="profile-lock-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg> Protected` : ''}
                    ${profile.is_guest ? 'Guest Profile' : ''}
                </div>
            </div>
        </div>
    `;

    return div;
}

async function selectProfile(profile) {
    // Check if PIN is required
    if (profile.has_pin) {
        selectedProfileForPin = profile;
        showPinModal(profile);
    } else {
        await loginProfile(profile.id, null);
    }
}

function showPinModal(profile) {
    profileModal.classList.remove('show');
    pinModal.classList.add('show');
    document.getElementById('pin-profile-name').textContent = `Profile: ${profile.name}`;
    document.getElementById('pin-input').value = '';
    document.getElementById('pin-error').classList.remove('show');
}

async function handlePinSubmit(e) {
    e.preventDefault();
    const pin = document.getElementById('pin-input').value;

    try {
        await loginProfile(selectedProfileForPin.id, pin);
    } catch (error) {
        document.getElementById('pin-error').textContent = 'Invalid PIN';
        document.getElementById('pin-error').classList.add('show');
    }
}

async function showPinHint() {
    if (!selectedProfileForPin) return;

    try {
        const response = await fetch(`${API_BASE}/api/profiles/${selectedProfileForPin.id}/hint`);
        const data = await response.json();
        alert(`Hint: ${data.hint}`);
    } catch (error) {
        console.error('Error getting hint:', error);
        showNotification('Error getting hint', 'error');
    }
}

async function loginProfile(profileId, pin) {
    try {
        const response = await fetch(`${API_BASE}/api/profiles/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_id: profileId, pin })
        });

        if (!response.ok) {
            throw new Error('Invalid PIN');
        }

        const data = await response.json();
        currentProfile = data.profile;
        sessionStorage.setItem('currentProfile', JSON.stringify(currentProfile));

        // Hide modals
        profileModal.classList.remove('show');
        pinModal.classList.remove('show');

        // Update UI
        profileNameDisplay.textContent = currentProfile.name;

        // Show welcome message first
        showNotification(`Welcome, ${currentProfile.name}!`, 'success');

        // Load user data
        await updateStatus();
        await loadDocuments();
        await loadGroupsAndChats();
        await displayUserAccessLevel();
    } catch (error) {
        throw error;
    }
}

function showCreateProfileModal() {
    profileModal.classList.remove('show');
    createProfileModal.classList.add('show');
    document.getElementById('create-profile-form').reset();

    // Show transfer option only if current profile is guest
    const transferOption = document.getElementById('transfer-chats-option');
    if (currentProfile && currentProfile.is_guest) {
        transferOption.style.display = 'block';
        document.getElementById('transfer-chats').checked = true;
    } else {
        transferOption.style.display = 'none';
    }
}

async function handleCreateProfile(e) {
    e.preventDefault();

    const name = document.getElementById('profile-name').value.trim();
    const pin = document.getElementById('profile-pin').value || null;
    const hint = document.getElementById('profile-hint').value || null;
    const shouldTransfer = document.getElementById('transfer-chats').checked;
    const fromGuestProfile = currentProfile && currentProfile.is_guest;

    try {
        const response = await fetch(`${API_BASE}/api/profiles`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, pin, hint })
        });

        const profile = await response.json();

        if (response.ok) {
            createProfileModal.classList.remove('show');

            // Transfer chats if requested and coming from guest
            if (shouldTransfer && fromGuestProfile && currentProfile) {
                try {
                    await fetch(`${API_BASE}/api/profiles/${profile.id}/transfer?from_profile_id=${currentProfile.id}`, {
                        method: 'POST'
                    });
                    showNotification('Profile created and chats transferred!', 'success');
                } catch (transferError) {
                    console.error('Error transferring chats:', transferError);
                    showNotification('Profile created but chat transfer failed', 'warning');
                }
            } else {
                showNotification('Profile created successfully!', 'success');
            }

            await loginProfile(profile.id, pin);
        } else {
            showNotification('Error creating profile', 'error');
        }
    } catch (error) {
        console.error('Error creating profile:', error);
        showNotification('Error creating profile', 'error');
    }
}

function showProfileSelector() {
    profileModal.classList.add('show');
    currentProfile = null;
    sessionStorage.removeItem('currentProfile');
    currentChatId = null;
    chatMessages.innerHTML = '';
    loadProfiles();
}

// Theme functions
function loadTheme() {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    const colorTheme = localStorage.getItem('colorTheme') || 'blue';
    const darkShade = localStorage.getItem('darkShade') || 'slate';

    applyColorTheme(colorTheme);

    if (isDarkMode) {
        applyDarkMode(true, darkShade);
    }

    updateActiveStates();
}

function toggleThemeDropdown(e) {
    e.stopPropagation();
    themeDropdown.classList.toggle('show');
}

function toggleDarkMode() {
    const isDarkMode = document.body.classList.contains('dark-mode');
    const darkShade = localStorage.getItem('darkShade') || 'slate';

    applyDarkMode(!isDarkMode, darkShade);
    localStorage.setItem('darkMode', !isDarkMode);

    updateActiveStates();
}

function changeColorTheme(theme) {
    applyColorTheme(theme);
    localStorage.setItem('colorTheme', theme);
    themeDropdown.classList.remove('show');
    updateActiveStates();
}

function changeDarkShade(shade) {
    const isDarkMode = document.body.classList.contains('dark-mode');

    // If not in dark mode, enable it
    if (!isDarkMode) {
        applyDarkMode(true, shade);
        localStorage.setItem('darkMode', 'true');
    } else {
        applyDarkMode(true, shade);
    }

    localStorage.setItem('darkShade', shade);
    themeDropdown.classList.remove('show');
    updateActiveStates();
}

function applyColorTheme(theme) {
    // Remove all color theme classes
    colorThemes.forEach(t => {
        if (t !== 'blue') {
            document.body.classList.remove(`theme-${t}`);
        }
    });

    // Add new color theme (blue is default, no class needed)
    if (theme !== 'blue') {
        document.body.classList.add(`theme-${theme}`);
    }
}

function applyDarkMode(enabled, shade = 'slate') {
    // Remove all dark shade classes
    darkShades.forEach(s => {
        document.body.classList.remove(`dark-${s}`);
    });

    if (enabled) {
        document.body.classList.add('dark-mode');
        document.body.classList.add(`dark-${shade}`);
        darkModeBtn.classList.add('active');
    } else {
        document.body.classList.remove('dark-mode');
        darkModeBtn.classList.remove('active');
    }
}

function getCurrentDarkShade() {
    for (const shade of darkShades) {
        if (document.body.classList.contains(`dark-${shade}`)) {
            return shade;
        }
    }
    return 'slate';
}

function getCurrentColorTheme() {
    for (const theme of colorThemes) {
        if (theme === 'blue') {
            // Check if no other color theme is active
            const hasOtherTheme = colorThemes.some(t => t !== 'blue' && document.body.classList.contains(`theme-${t}`));
            if (!hasOtherTheme) return 'blue';
        } else if (document.body.classList.contains(`theme-${theme}`)) {
            return theme;
        }
    }
    return 'blue';
}

function updateActiveStates() {
    if (!themeColors) return;

    const isDarkMode = document.body.classList.contains('dark-mode');
    const currentColor = getCurrentColorTheme();
    const currentShade = getCurrentDarkShade();

    themeColors.forEach(color => {
        const theme = color.dataset.theme;

        // Check if this color swatch should be active
        if (darkShades.includes(theme)) {
            // Dark shade swatch
            if (isDarkMode && theme === currentShade) {
                color.classList.add('active');
            } else {
                color.classList.remove('active');
            }
        } else {
            // Color theme swatch
            if (theme === currentColor) {
                color.classList.add('active');
            } else {
                color.classList.remove('active');
            }
        }
    });
}

// Update status indicator
async function updateStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();

        statusText.textContent = data.status === 'running' ? 'Running' : 'Offline';
        docCount.textContent = `${data.documents_count} document${data.documents_count !== 1 ? 's' : ''}`;

    } catch (error) {
        console.error('Error fetching status:', error);
        statusText.textContent = 'Error';
    }
}

// Load and display documents
async function loadDocuments() {
    try {
        // Pass profile_id to filter documents based on access level
        const profileId = currentProfile ? currentProfile.id : '';
        const url = profileId ? `${API_BASE}/api/documents?profile_id=${profileId}` : `${API_BASE}/api/documents`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.documents && data.documents.length > 0) {
            documentsList.innerHTML = '';
            data.documents.forEach(doc => {
                const docElement = createDocumentElement(doc);
                documentsList.appendChild(docElement);
            });
        } else {
            documentsList.innerHTML = '<p class="empty-state">No documents uploaded yet</p>';
        }

        await updateStatus();

    } catch (error) {
        console.error('Error loading documents:', error);
        documentsList.innerHTML = '<p class="empty-state">Error loading documents</p>';
    }
}

// Create a document element
function createDocumentElement(doc) {
    const div = document.createElement('div');
    div.className = 'document-item';

    const size = formatFileSize(doc.size);
    const type = doc.type.toUpperCase().replace('.', '');

    div.innerHTML = `
        <div class="document-info">
            <div class="document-name" title="${doc.name}">${doc.name}</div>
            <div class="document-meta">${type} • ${size}</div>
        </div>
        <button class="delete-btn" onclick="deleteDocument('${doc.name}')" title="Delete document">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                <line x1="10" y1="11" x2="10" y2="17"></line>
                <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
        </button>
    `;

    return div;
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Handle file upload
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        // Show loading state
        const uploadBtn = document.querySelector('.upload-btn');
        const originalText = uploadBtn.innerHTML;
        uploadBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
            </svg>
            Uploading...
        `;

        const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showNotification(`${file.name} uploaded successfully!`, 'success');
            await loadDocuments();
        } else {
            showNotification(data.detail || 'Error uploading file', 'error');
        }

        uploadBtn.innerHTML = originalText;

    } catch (error) {
        console.error('Error uploading file:', error);
        showNotification('Error uploading file', 'error');
    }

    // Reset file input
    event.target.value = '';
}

// Delete document
async function deleteDocument(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/documents/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showNotification(`${filename} deleted successfully!`, 'success');
            await loadDocuments();
        } else {
            showNotification(data.detail || 'Error deleting file', 'error');
        }

    } catch (error) {
        console.error('Error deleting document:', error);
        showNotification('Error deleting document', 'error');
    }
}

// Group and Chat Session Management
async function loadGroupsAndChats() {
    if (!currentProfile) return;

    try {
        const response = await fetch(`${API_BASE}/api/groups/with-chats?profile_id=${currentProfile.id}`);
        const data = await response.json();

        chatList.innerHTML = '';

        let hasChats = false;

        // Display grouped chats
        if (data.groups && data.groups.length > 0) {
            data.groups.forEach(groupData => {
                const groupElement = createGroupElement(groupData.group, groupData.chats);
                chatList.appendChild(groupElement);
                if (groupData.chats.length > 0) hasChats = true;
            });
        }

        // Display ungrouped chats
        if (data.ungrouped && data.ungrouped.length > 0) {
            const ungroupedHeader = document.createElement('div');
            ungroupedHeader.className = 'group-container';
            ungroupedHeader.innerHTML = `
                <div class="group-header" onclick="toggleGroup('ungrouped')">
                    <div class="group-header-left">
                        <div class="group-toggle" id="toggle-ungrouped">
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="6 9 12 15 18 9"></polyline>
                            </svg>
                        </div>
                        <div class="group-name">Ungrouped</div>
                    </div>
                </div>
                <div class="group-chats" id="group-ungrouped"></div>
            `;
            chatList.appendChild(ungroupedHeader);

            const ungroupedChats = document.getElementById('group-ungrouped');

            // Make ungrouped container a drop target
            ungroupedChats.dataset.groupId = 'ungrouped';
            ungroupedChats.addEventListener('dragover', handleGroupDragOver);
            ungroupedChats.addEventListener('drop', handleGroupDrop);
            ungroupedChats.addEventListener('dragleave', handleGroupDragLeave);

            data.ungrouped.forEach(session => {
                const chatElement = createChatElement(session);
                ungroupedChats.appendChild(chatElement);
            });
            hasChats = true;
        }

        if (!hasChats) {
            chatList.innerHTML = '<p class="empty-state">No chat history yet</p>';
        } else if (!currentChatId) {
            // Auto-select first chat
            const firstChat = data.groups[0]?.chats[0] || data.ungrouped[0];
            if (firstChat) {
                await switchToChat(firstChat.id);
            }
        }

    } catch (error) {
        console.error('Error loading groups and chats:', error);
        chatList.innerHTML = '<p class="empty-state">Error loading chat history</p>';
    }
}

function createGroupElement(group, chats) {
    const groupDiv = document.createElement('div');
    groupDiv.className = 'group-container';

    const isCollapsed = collapsedGroups.has(group.id);

    groupDiv.innerHTML = `
        <div class="group-header" onclick="toggleGroup('${group.id}')">
            <div class="group-header-left">
                <div class="group-toggle ${isCollapsed ? 'collapsed' : ''}" id="toggle-${group.id}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
                <div class="group-name" contenteditable="false" id="group-name-${group.id}" onblur="renameGroup('${group.id}')" onkeydown="if(event.key==='Enter'){event.preventDefault();this.blur();}">${group.name}</div>
            </div>
            <div class="group-actions">
                <button class="group-action-btn" onclick="event.stopPropagation(); enableGroupRename('${group.id}')" title="Rename group">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                </button>
                <button class="group-action-btn delete" onclick="event.stopPropagation(); deleteGroup('${group.id}')" title="Delete group">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        </div>
        <div class="group-chats ${isCollapsed ? 'collapsed' : ''}" id="group-${group.id}"></div>
    `;

    groupDiv.querySelector(`#group-${group.id}`);
    const groupChats = groupDiv.querySelector(`#group-${group.id}`);

    // Make group container a drop target
    groupChats.dataset.groupId = group.id;
    groupChats.addEventListener('dragover', handleGroupDragOver);
    groupChats.addEventListener('drop', handleGroupDrop);
    groupChats.addEventListener('dragleave', handleGroupDragLeave);

    chats.forEach(session => {
        const chatElement = createChatElement(session);
        groupChats.appendChild(chatElement);
    });

    return groupDiv;
}

function toggleGroup(groupId) {
    const toggle = document.getElementById(`toggle-${groupId}`);
    const chats = document.getElementById(`group-${groupId}`);

    if (toggle && chats) {
        toggle.classList.toggle('collapsed');
        chats.classList.toggle('collapsed');

        if (collapsedGroups.has(groupId)) {
            collapsedGroups.delete(groupId);
        } else {
            collapsedGroups.add(groupId);
        }
    }
}

function enableGroupRename(groupId) {
    const nameElement = document.getElementById(`group-name-${groupId}`);
    if (nameElement) {
        nameElement.contentEditable = 'true';
        nameElement.focus();
        // Select all text
        const range = document.createRange();
        range.selectNodeContents(nameElement);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    }
}

// Drag and Drop handlers
let draggedChatId = null;
let draggedFromGroupId = null;

function handleChatDragStart(e) {
    draggedChatId = e.currentTarget.dataset.chatId;
    draggedFromGroupId = e.currentTarget.dataset.groupId;
    e.currentTarget.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', e.currentTarget.innerHTML);
    console.log('Drag started:', { chatId: draggedChatId, fromGroup: draggedFromGroupId });
}

function handleChatDragEnd(e) {
    e.currentTarget.classList.remove('dragging');
    // Remove all drag-over classes
    document.querySelectorAll('.group-chats').forEach(el => {
        el.classList.remove('drag-over');
    });
}

function handleGroupDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault(); // Allows us to drop
    }
    e.dataTransfer.dropEffect = 'move';

    const groupChats = e.currentTarget;
    groupChats.classList.add('drag-over');

    return false;
}

function handleGroupDragLeave(e) {
    // Only remove if we're actually leaving the element (not just entering a child)
    if (e.currentTarget.contains(e.relatedTarget)) {
        return;
    }
    e.currentTarget.classList.remove('drag-over');
}

async function handleGroupDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation(); // Stops some browsers from redirecting
    }
    e.preventDefault();

    const targetGroupId = e.currentTarget.dataset.groupId;
    e.currentTarget.classList.remove('drag-over');

    console.log('Drop event:', { chatId: draggedChatId, fromGroup: draggedFromGroupId, toGroup: targetGroupId });

    // Don't do anything if dropping in the same group
    if (draggedFromGroupId === targetGroupId) {
        console.log('Same group, ignoring drop');
        return false;
    }

    if (draggedChatId && currentProfile) {
        try {
            // Convert 'ungrouped' to null for API
            const groupIdForApi = targetGroupId === 'ungrouped' ? null : targetGroupId;

            console.log('Moving chat via API:', { chatId: draggedChatId, toGroupId: groupIdForApi });

            const response = await fetch(`${API_BASE}/api/chats/${draggedChatId}/move?profile_id=${currentProfile.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ group_id: groupIdForApi })
            });

            if (response.ok) {
                // Reload the chat list to reflect changes
                await loadGroupsAndChats();
                showNotification('Chat moved successfully!', 'success');
            } else {
                const errorData = await response.json();
                console.error('Failed to move chat:', errorData);
                showNotification(`Failed to move chat: ${errorData.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('Error moving chat:', error);
            showNotification(`Error moving chat: ${error.message}`, 'error');
        }
    } else {
        console.warn('Cannot move chat:', { draggedChatId, hasProfile: !!currentProfile });
    }

    draggedChatId = null;
    draggedFromGroupId = null;

    return false;
}

async function renameGroup(groupId) {
    if (!currentProfile) return;

    const nameElement = document.getElementById(`group-name-${groupId}`);
    if (nameElement) {
        const newName = nameElement.textContent.trim();
        nameElement.contentEditable = 'false';

        if (newName) {
            try {
                const response = await fetch(`${API_BASE}/api/groups/${groupId}?profile_id=${currentProfile.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name: newName })
                });

                if (response.ok) {
                    showNotification('Group renamed successfully!', 'success');
                } else {
                    showNotification('Error renaming group', 'error');
                    await loadGroupsAndChats();
                }
            } catch (error) {
                console.error('Error renaming group:', error);
                showNotification('Error renaming group', 'error');
                await loadGroupsAndChats();
            }
        }
    }
}

async function createNewGroup() {
    if (!currentProfile) {
        showNotification('Please select a profile first', 'error');
        return;
    }

    const name = prompt('Enter group name:');
    if (name && name.trim()) {
        try {
            const response = await fetch(`${API_BASE}/api/groups?profile_id=${currentProfile.id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: name.trim() })
            });

            if (response.ok) {
                showNotification('Group created successfully!', 'success');
                await loadGroupsAndChats();
            } else {
                const errorData = await response.json();
                console.error('Error creating group:', errorData);
                showNotification(`Error creating group: ${errorData.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('Error creating group:', error);
            showNotification(`Error creating group: ${error.message}`, 'error');
        }
    }
}

async function deleteGroup(groupId) {
    if (!currentProfile) return;
    if (!confirm('Are you sure you want to delete this group? Chats will be moved to ungrouped.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/groups/${groupId}?profile_id=${currentProfile.id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Group deleted successfully!', 'success');
            await loadGroupsAndChats();
        } else {
            showNotification('Error deleting group', 'error');
        }
    } catch (error) {
        console.error('Error deleting group:', error);
        showNotification('Error deleting group', 'error');
    }
}

function createChatElement(session) {
    const div = document.createElement('div');
    div.className = 'chat-item' + (session.id === currentChatId ? ' active' : '');
    div.onclick = () => switchToChat(session.id);

    // Add drag-and-drop attributes
    div.draggable = true;
    div.dataset.chatId = session.id;
    div.dataset.groupId = session.group_id || 'ungrouped';

    const preview = session.messages && session.messages.length > 0
        ? session.messages[session.messages.length - 1].content.substring(0, 50)
        : 'No messages yet';

    div.innerHTML = `
        <div class="chat-item-header">
            <div class="chat-title" title="${session.title}">${session.title}</div>
            <button class="chat-delete-btn" onclick="event.stopPropagation(); deleteChatSession('${session.id}')" title="Delete chat">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        </div>
        <div class="chat-preview">${preview}</div>
    `;

    // Add drag event listeners
    div.addEventListener('dragstart', handleChatDragStart);
    div.addEventListener('dragend', handleChatDragEnd);

    return div;
}

async function createNewChat() {
    if (!currentProfile) {
        showNotification('Please select a profile first', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/chats?profile_id=${currentProfile.id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: 'New Chat' })
        });

        const session = await response.json();

        if (response.ok) {
            await loadGroupsAndChats();
            await switchToChat(session.id);
            showNotification('New chat created!', 'success');
        } else {
            console.error('Error creating chat:', session);
            showNotification(`Error creating chat: ${session.detail || 'Unknown error'}`, 'error');
        }

    } catch (error) {
        console.error('Error creating chat:', error);
        showNotification(`Error creating chat: ${error.message}`, 'error');
    }
}

async function switchToChat(chatId) {
    if (!currentProfile) return;

    try {
        const response = await fetch(`${API_BASE}/api/chats/${chatId}?profile_id=${currentProfile.id}`);
        const session = await response.json();

        if (response.ok) {
            currentChatId = chatId;

            // Clear current messages
            chatMessages.innerHTML = '';

            // Load messages from session
            if (session.messages && session.messages.length > 0) {
                session.messages.forEach(msg => {
                    addMessage(msg.role, msg.content, msg.sources || []);
                });
            } else {
                // Show welcome message for empty chat
                chatMessages.innerHTML = `
                    <div class="welcome-message">
                        <h2>Welcome!</h2>
                        <p>Upload documents and ask questions about them. The AI will use the context from your documents to provide accurate answers.</p>
                        <div class="example-questions">
                            <p><strong>Example questions:</strong></p>
                            <ul>
                                <li>What are the main topics covered in these documents?</li>
                                <li>Can you summarize the key findings?</li>
                                <li>What are the recommendations mentioned?</li>
                            </ul>
                        </div>
                    </div>
                `;
            }

            // Update active state in chat list
            document.querySelectorAll('.chat-item').forEach(item => {
                item.classList.remove('active');
            });
            const activeChat = Array.from(document.querySelectorAll('.chat-item')).find(
                item => item.onclick.toString().includes(chatId)
            );
            if (activeChat) {
                activeChat.classList.add('active');
            }

            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;

        } else {
            showNotification('Error loading chat', 'error');
        }

    } catch (error) {
        console.error('Error switching chat:', error);
        showNotification('Error loading chat', 'error');
    }
}

async function deleteChatSession(chatId) {
    if (!currentProfile) return;
    if (!confirm('Are you sure you want to delete this chat?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/chats/${chatId}?profile_id=${currentProfile.id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Chat deleted successfully!', 'success');

            // If deleted chat was current, clear it
            if (currentChatId === chatId) {
                currentChatId = null;
                chatMessages.innerHTML = '';
            }

            await loadGroupsAndChats();
        } else {
            showNotification('Error deleting chat', 'error');
        }

    } catch (error) {
        console.error('Error deleting chat:', error);
        showNotification('Error deleting chat', 'error');
    }
}

// Handle question submission
async function handleQuestionSubmit(event) {
    event.preventDefault();

    if (!currentProfile) return;

    const question = questionInput.value.trim();
    if (!question) return;

    // Create a new chat if there isn't one
    if (!currentChatId) {
        const response = await fetch(`${API_BASE}/api/chats?profile_id=${currentProfile.id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: 'New Chat' })
        });

        const session = await response.json();
        if (response.ok) {
            currentChatId = session.id;
            await loadGroupsAndChats();
        } else {
            showNotification('Error creating chat session', 'error');
            return;
        }
    }

    // Clear input and remove welcome message
    questionInput.value = '';
    questionInput.style.height = 'auto';
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    // Add user message to UI (will be saved by backend)
    addMessage('user', question);

    // Show loading indicator and track start time
    const startTime = Date.now();
    const loadingId = addLoadingIndicator();

    try {
        // Check if this is a table operation query by calling the new table API first
        // We can implement logic to detect table-related queries, or just try both APIs
        const tableResponse = await fetch(`${API_BASE}/api/table/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                profile_id: currentProfile.id,
                chat_id: currentChatId
            })
        });

        const tableData = await tableResponse.json();

        if (tableResponse.ok && tableData.has_data) {
            // This is a table operation result
            let answer = tableData.message;
            if (tableData.download_url) {
                answer += ` <a href="${tableData.download_url}" target="_blank" class="download-link" download>Download Result</a>`;
            }
            
            // Calculate generation time
            const endTime = Date.now();
            const generationTime = ((endTime - startTime) / 1000).toFixed(1);

            // Remove loading indicator
            removeLoadingIndicator(loadingId);

            // Add the table response to the chat
            addMessage('assistant', answer, [], generationTime);
            // Reload chat sessions to update preview and title
            await loadGroupsAndChats();
        } else {
            // This is a regular document query, use the original API
            const response = await fetch(`${API_BASE}/api/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: question,
                    profile_id: currentProfile.id,
                    chat_id: currentChatId
                })
            });

            const data = await response.json();

            // Calculate generation time
            const endTime = Date.now();
            const generationTime = ((endTime - startTime) / 1000).toFixed(1);

            // Remove loading indicator
            removeLoadingIndicator(loadingId);

            if (response.ok) {
                addMessage('assistant', data.answer, data.sources, generationTime);
                // Reload chat sessions to update preview and title
                await loadGroupsAndChats();
            } else {
                addMessage('assistant', `Error: ${data.detail || 'Unknown error occurred'}`, [], generationTime);
            }
        }

    } catch (error) {
        console.error('Error asking question:', error);
        const endTime = Date.now();
        const generationTime = ((endTime - startTime) / 1000).toFixed(1);
        removeLoadingIndicator(loadingId);
        addMessage('assistant', 'Error: Could not connect to the server. Please ensure the backend is running.', [], generationTime);
    }

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add a message to the chat
function addMessage(role, text, sources = [], generationTime = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'AI';

    const content = document.createElement('div');
    content.className = 'message-content';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';

    // Simple formatting: only convert **text** to bold
    const formattedText = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    messageText.innerHTML = formattedText;

    content.appendChild(messageText);

    // Add generation time for assistant messages
    if (role === 'assistant' && generationTime !== null) {
        const timeDiv = document.createElement('div');
        timeDiv.className = 'generation-time';
        timeDiv.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <span>Generated in ${generationTime}s</span>
        `;
        content.appendChild(timeDiv);
    }

    // Add sources if available
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';

        const sourcesTitle = document.createElement('div');
        sourcesTitle.className = 'message-sources-title';
        sourcesTitle.textContent = 'Sources:';
        sourcesDiv.appendChild(sourcesTitle);

        sources.forEach(source => {
            const sourceTag = document.createElement('span');
            sourceTag.className = 'source-tag';
            sourceTag.textContent = source;
            sourcesDiv.appendChild(sourceTag);
        });

        content.appendChild(sourcesDiv);
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add loading indicator with timer
function addLoadingIndicator() {
    const loadingId = `loading-${Date.now()}`;
    const messageDiv = document.createElement('div');
    messageDiv.id = loadingId;
    messageDiv.className = 'message assistant';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';

    const content = document.createElement('div');
    content.className = 'message-content';

    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.innerHTML = `
        <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
        <div class="loading-timer" id="timer-${loadingId}">0s</div>
    `;

    content.appendChild(loadingIndicator);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Start timer
    const startTime = Date.now();
    const timerElement = document.getElementById(`timer-${loadingId}`);
    const timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        if (timerElement) {
            timerElement.textContent = `${elapsed}s`;
        }
    }, 1000);

    // Store timer interval ID for cleanup
    messageDiv.dataset.timerInterval = timerInterval;

    return loadingId;
}

// Remove loading indicator
function removeLoadingIndicator(loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
        // Clear timer interval
        const timerInterval = loadingElement.dataset.timerInterval;
        if (timerInterval) {
            clearInterval(parseInt(timerInterval));
        }
        loadingElement.remove();
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Get existing notifications to calculate vertical offset
    const existingNotifications = document.querySelectorAll('.notification-toast');
    let topOffset = 20;

    existingNotifications.forEach(notif => {
        const rect = notif.getBoundingClientRect();
        topOffset = Math.max(topOffset, rect.bottom - window.scrollY + 10);
    });

    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification-toast';
    notification.style.cssText = `
        position: fixed;
        top: ${topOffset}px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
        width: 350px;
        word-wrap: break-word;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Display user access level
async function displayUserAccessLevel() {
    if (!currentProfile) return;

    try {
        const response = await fetch(`${API_BASE}/api/users/${currentProfile.id}/access-info`);
        if (response.ok) {
            const data = await response.json();

            // Update profile display with access level
            if (data.has_access) {
                const accessBadge = `<span class="access-badge">${data.access_level_name}</span>`;
                profileNameDisplay.innerHTML = `${currentProfile.name} ${accessBadge}`;

                // Show notification about access level
                const docText = data.document_count === 1 ? 'document' : 'documents';
                showNotification(`Access Level: ${data.access_level_name} (${data.document_count} ${docText})`, 'info');
            }
        }
    } catch (error) {
        console.error('Error fetching access level:', error);
    }
}

// Profile Settings Functions
profileSettingsBtn?.addEventListener('click', () => {
    if (!currentProfile || currentProfile.is_guest) {
        showNotification('Guest profile cannot be edited', 'error');
        return;
    }
    openProfileSettings();
});

async function openProfileSettings() {
    // Load current profile data
    document.getElementById('settings-name').value = currentProfile.name;
    document.getElementById('settings-hint').value = currentProfile.hint || '';
    document.getElementById('settings-pin').value = '';

    // Populate microphones
    await populateMicrophones();

    // Load profile picture if exists
    try {
        const response = await fetch(`${API_BASE}/api/profiles/${currentProfile.id}/picture`);
        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            document.getElementById('profile-pic-preview').innerHTML = `<img src="${url}" style="width: 100%; height: 100%; object-fit: cover;">`;
            document.getElementById('remove-pic-btn').style.display = 'block';
        } else {
            // Show default avatar
            document.getElementById('profile-pic-preview').innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>`;
            document.getElementById('remove-pic-btn').style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading profile picture:', error);
    }

    profileSettingsModal.classList.add('show');
}

document.getElementById('upload-pic-btn')?.addEventListener('click', () => {
    document.getElementById('profile-pic-input').click();
});

document.getElementById('profile-pic-input')?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/profiles/${currentProfile.id}/picture`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            // Display uploaded image
            const url = URL.createObjectURL(file);
            document.getElementById('profile-pic-preview').innerHTML = `<img src="${url}" style="width: 100%; height: 100%; object-fit: cover;">`;
            document.getElementById('remove-pic-btn').style.display = 'block';
            showNotification('Profile picture uploaded successfully', 'success');
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to upload picture', 'error');
        }
    } catch (error) {
        showNotification('Error uploading picture: ' + error.message, 'error');
    }
});

document.getElementById('remove-pic-btn')?.addEventListener('click', async () => {
    if (!confirm('Remove profile picture?')) return;

    try {
        const response = await fetch(`${API_BASE}/api/profiles/${currentProfile.id}/picture`, {
            method: 'DELETE'
        });

        if (response.ok) {
            document.getElementById('profile-pic-preview').innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>`;
            document.getElementById('remove-pic-btn').style.display = 'none';
            showNotification('Profile picture removed', 'success');
        }
    } catch (error) {
        showNotification('Error removing picture: ' + error.message, 'error');
    }
});

document.getElementById('cancel-settings-btn')?.addEventListener('click', () => {
    profileSettingsModal.classList.remove('show');
});

profileSettingsForm?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('settings-name').value.trim();
    const pin = document.getElementById('settings-pin').value.trim();
    const hint = document.getElementById('settings-hint').value.trim();

    if (!name) {
        showNotification('Name is required', 'error');
        return;
    }

    try {
        const updateData = { name };
        if (pin) updateData.pin = pin;
        if (hint) updateData.hint = hint;

        const response = await fetch(`${API_BASE}/api/profiles/${currentProfile.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });

        if (response.ok) {
            const data = await response.json();
            currentProfile = data.profile;
            sessionStorage.setItem('currentProfile', JSON.stringify(currentProfile));

            // Update UI
            profileNameDisplay.textContent = currentProfile.name;
            await displayUserAccessLevel();

            profileSettingsModal.classList.remove('show');
            showNotification('Profile updated successfully', 'success');
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to update profile', 'error');
        }
    } catch (error) {
        showNotification('Error updating profile: ' + error.message, 'error');
    }
});

// ============================================================================
// MODEL MANAGEMENT
// ============================================================================

const modelSelectorBtn = document.getElementById('model-selector-btn');
const modelDropdown = document.getElementById('model-dropdown');
const refreshModelsBtn = document.getElementById('refresh-models-btn');
const mainLlmSelect = document.getElementById('main-llm-select');
const mainEmbeddingSelect = document.getElementById('main-embedding-select');
const saveModelsBtn = document.getElementById('save-models-btn');
const installModelBtn = document.getElementById('install-model-btn');
const mainModelNameInput = document.getElementById('main-model-name-input');
const modelStatusMessage = document.getElementById('model-status-message');

// Toggle model dropdown
modelSelectorBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    modelDropdown.classList.toggle('show');
    if (modelDropdown.classList.contains('show')) {
        loadMainPageModels();
    }
});

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!modelDropdown?.contains(e.target) && !modelSelectorBtn?.contains(e.target)) {
        modelDropdown?.classList.remove('show');
    }
});

// Refresh models
refreshModelsBtn?.addEventListener('click', async (e) => {
    e.preventDefault();
    await loadMainPageModels();
    showModelStatus('Models refreshed!', 'success');
});

// Load models for main page
async function loadMainPageModels() {
    try {
        // Load available models
        const modelsResponse = await fetch(`${API_BASE}/api/models/available`);
        const modelsData = await modelsResponse.json();

        // Load current model selection
        const currentResponse = await fetch(`${API_BASE}/api/models/current`);
        const currentData = await currentResponse.json();

        // Populate dropdowns
        mainLlmSelect.innerHTML = '';
        mainEmbeddingSelect.innerHTML = '';

        if (modelsData.models && modelsData.models.length > 0) {
            modelsData.models.forEach(model => {
                const llmOption = document.createElement('option');
                llmOption.value = model;
                llmOption.textContent = model;
                if (model === currentData.llm_model) {
                    llmOption.selected = true;
                }
                mainLlmSelect.appendChild(llmOption);

                const embOption = document.createElement('option');
                embOption.value = model;
                embOption.textContent = model;
                if (model === currentData.embedding_model) {
                    embOption.selected = true;
                }
                mainEmbeddingSelect.appendChild(embOption);
            });
        } else {
            mainLlmSelect.innerHTML = '<option value="">No models found</option>';
            mainEmbeddingSelect.innerHTML = '<option value="">No models found</option>';
        }
    } catch (error) {
        console.error('Error loading models:', error);
        showModelStatus('Failed to load models', 'error');
    }
}

// Save model selection
saveModelsBtn?.addEventListener('click', async () => {
    const llmModel = mainLlmSelect.value;
    const embeddingModel = mainEmbeddingSelect.value;

    if (!llmModel || !embeddingModel) {
        showModelStatus('Please select both models', 'error');
        return;
    }

    try {
        showModelStatus('Saving models...', 'loading');

        const response = await fetch(`${API_BASE}/api/models/select`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                llm_model: llmModel,
                embedding_model: embeddingModel
            })
        });

        const data = await response.json();

        if (response.ok) {
            showModelStatus('Models updated successfully!', 'success');
            setTimeout(() => {
                modelDropdown.classList.remove('show');
            }, 1500);
        } else {
            showModelStatus(data.detail || 'Failed to update models', 'error');
        }
    } catch (error) {
        showModelStatus('Error: ' + error.message, 'error');
    }
});

// Install new model
installModelBtn?.addEventListener('click', async () => {
    const modelName = mainModelNameInput.value.trim();

    if (!modelName) {
        showModelStatus('Please enter a model name', 'error');
        return;
    }

    try {
        showModelStatus('Installing ' + modelName + '... This may take several minutes.', 'loading');

        const response = await fetch(`${API_BASE}/api/models/install`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({model_name: modelName})
        });

        const data = await response.json();

        if (response.ok) {
            showModelStatus('Model installed successfully!', 'success');
            mainModelNameInput.value = '';
            await loadMainPageModels();
        } else {
            showModelStatus(data.detail || 'Failed to install model', 'error');
        }
    } catch (error) {
        showModelStatus('Error: ' + error.message, 'error');
    }
});

// Show model status message
function showModelStatus(message, type) {
    modelStatusMessage.textContent = message;
    modelStatusMessage.className = 'model-status-message ' + type;

    if (type === 'success') {
        setTimeout(() => {
            modelStatusMessage.className = 'model-status-message';
        }, 3000);
    }
}

// Initialize on page load
init();

// Voice Recognition Functions
function toggleRecognition() {
    if (!recognition) {
        showNotification('Speech Recognition API not supported in this browser.', 'error');
        return;
    }
    if (isRecognizing) {
        stopRecognition();
    } else {
        startRecognition();
    }
}

function startRecognition() {
    if (recognition) {
        const selectedMicrophone = localStorage.getItem('selectedMicrophone');
        if (selectedMicrophone) {
            // This is a conceptual representation. The Web Speech API does not directly support setting the input device.
            // This would require using navigator.mediaDevices.getUserMedia with the deviceId and integrating it with the Web Audio API.
            // For now, we'll just log the selected device.
            console.log('Using microphone:', selectedMicrophone);
        }
        isRecognizing = true;
        voiceChatBtn.classList.add('active');
        recognition.start();
        showNotification('Listening...', 'info');
    }
}

function stopRecognition() {
    if (recognition) {
        isRecognizing = false;
        voiceChatBtn.classList.remove('active');
        recognition.stop();
        showNotification('Stopped listening.', 'info');
    }
}

async function populateMicrophones() {
    if (microphoneSelect) {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioInputDevices = devices.filter(device => device.kind === 'audioinput');
            
            microphoneSelect.innerHTML = '<option value="">Default</option>';
            audioInputDevices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.textContent = device.label || `Microphone ${microphoneSelect.length}`;
                microphoneSelect.appendChild(option);
            });

            const selectedMicrophone = localStorage.getItem('selectedMicrophone');
            if (selectedMicrophone) {
                microphoneSelect.value = selectedMicrophone;
            }
        } catch (error) {
            console.error('Error enumerating audio devices:', error);
            showNotification('Could not access microphones.', 'error');
        }
    }
}

microphoneSelect?.addEventListener('change', () => {
    localStorage.setItem('selectedMicrophone', microphoneSelect.value);
});

