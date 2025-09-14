// Global variables
let modules = [];
let currentLayout = {};
let sortableInstances = [];
let socket = null;
let bleConnected = false;
let logsVisible = false;
let buttonPressTimeout = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', async function() {
    await loadModules();
    await loadLayout();
    setupDragAndDrop();
    setupEventListeners();
    setupSocketIO();
    checkBLEStatus();
});

// Setup Socket.IO connection
function setupSocketIO() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        socket.emit('request_ble_status');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
    });
    
    socket.on('ble_status', function(data) {
        updateConnectionStatus(data.connected);
    });
    
    socket.on('button_press', function(data) {
        handleButtonPress(data);
    });
    
    socket.on('ble_log', function(data) {
        addLogEntry(data);
    });
    
    socket.on('ble_logs', function(data) {
        updateLogs(data.logs);
    });
}

// BLE Management Functions
async function connectBLE() {
    const connectBtn = document.getElementById('connect-btn');
    const disconnectBtn = document.getElementById('disconnect-btn');
    
    connectBtn.disabled = true;
    connectBtn.textContent = 'Connecting...';
    updateConnectionStatus('connecting');
    
    try {
        const response = await fetch('/api/ble/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('BLE connection initiated', 'success');
        } else {
            showStatus(`Connection failed: ${result.error}`, 'error');
            updateConnectionStatus(false);
        }
    } catch (error) {
        showStatus(`Connection error: ${error.message}`, 'error');
        updateConnectionStatus(false);
    } finally {
        connectBtn.disabled = false;
        connectBtn.textContent = 'Connect';
    }
}

async function disconnectBLE() {
    const connectBtn = document.getElementById('connect-btn');
    const disconnectBtn = document.getElementById('disconnect-btn');
    
    disconnectBtn.disabled = true;
    disconnectBtn.textContent = 'Disconnecting...';
    
    try {
        const response = await fetch('/api/ble/disconnect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('BLE disconnected', 'info');
            updateConnectionStatus(false);
        } else {
            showStatus(`Disconnect failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Disconnect error: ${error.message}`, 'error');
    } finally {
        disconnectBtn.disabled = false;
        disconnectBtn.textContent = 'Disconnect';
    }
}

async function checkBLEStatus() {
    try {
        const response = await fetch('/api/ble/status');
        const status = await response.json();
        
        updateConnectionStatus(status.connected);
        if (status.logs) {
            updateLogs(status.logs);
        }
        if (status.last_button) {
            handleButtonPress(status.last_button);
        }
    } catch (error) {
        console.error('Error checking BLE status:', error);
    }
}

function updateConnectionStatus(connected) {
    bleConnected = connected;
    const statusElement = document.getElementById('connection-status');
    const connectBtn = document.getElementById('connect-btn');
    const disconnectBtn = document.getElementById('disconnect-btn');
    
    if (connected === 'connecting') {
        statusElement.textContent = 'Connecting...';
        statusElement.className = 'status-value connecting';
        connectBtn.disabled = true;
        disconnectBtn.disabled = true;
    } else if (connected) {
        statusElement.textContent = 'Connected';
        statusElement.className = 'status-value connected';
        connectBtn.disabled = true;
        disconnectBtn.disabled = false;
    } else {
        statusElement.textContent = 'Disconnected';
        statusElement.className = 'status-value disconnected';
        connectBtn.disabled = false;
        disconnectBtn.disabled = true;
        
        // Clear any active button states
        clearButtonStates();
    }
}

function handleButtonPress(data) {
    // Update preview button
    updatePreviewButton(data.slot, data.pressed);
    
    // Highlight the corresponding grid slot
    highlightGridSlot(data.slot, data.pressed);
    
    // Add log entry for display
    if (logsVisible) {
        const logMessage = `🔘 Module ${data.module_number} ${data.pressed ? 'pressed' : 'released'}`;
        addLogEntry({
            timestamp: new Date().toLocaleTimeString(),
            message: logMessage,
            level: 'info'
        });
    }
}

function updatePreviewButton(slot, pressed) {
    const previewButton = document.querySelector(`[data-preview="${slot}"]`);
    if (previewButton) {
        if (pressed) {
            previewButton.classList.add('active', 'flash');
            // Remove flash class after animation
            setTimeout(() => {
                previewButton.classList.remove('flash');
            }, 300);
        } else {
            previewButton.classList.remove('active');
        }
    }
}

function highlightGridSlot(slot, pressed) {
    const gridSlot = document.querySelector(`[data-slot="${slot}"]`);
    if (gridSlot) {
        if (pressed) {
            gridSlot.classList.add('button-pressed');
            
            // Clear any existing timeout
            if (buttonPressTimeout) {
                clearTimeout(buttonPressTimeout);
            }
        } else {
            gridSlot.classList.remove('button-pressed');
        }
    }
}

function clearButtonStates() {
    // Clear all preview buttons
    document.querySelectorAll('.preview-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Clear all grid slot highlights
    document.querySelectorAll('.grid-slot').forEach(slot => {
        slot.classList.remove('button-pressed');
    });
}

function cleanupDragStates() {
    // Remove all drag-related classes from all elements
    document.querySelectorAll('.grid-slot').forEach(slot => {
        slot.classList.remove('drop-zone-available', 'drop-zone-hover', 'drag-over', 'sortable-over');
    });
    
    // Remove drag classes from module pool
    const modulePool = document.getElementById('module-pool');
    if (modulePool) {
        modulePool.classList.remove('drop-zone-available', 'drop-zone-hover');
    }
    
    // Remove any remaining drag classes from draggable items
    document.querySelectorAll('.module-item').forEach(item => {
        item.classList.remove('dragging', 'sortable-drag', 'sortable-chosen', 'sortable-ghost');
    });
    
    console.log('Cleaned up all drag states');
}

function toggleLogs() {
    const logsContainer = document.getElementById('ble-logs-container');
    const toggleBtn = document.getElementById('toggle-logs-btn');
    
    logsVisible = !logsVisible;
    
    if (logsVisible) {
        logsContainer.style.display = 'block';
        toggleBtn.textContent = 'Hide Logs';
        toggleBtn.classList.remove('btn-outline-secondary');
        toggleBtn.classList.add('btn-secondary');
    } else {
        logsContainer.style.display = 'none';
        toggleBtn.textContent = 'Show Logs';
        toggleBtn.classList.remove('btn-secondary');
        toggleBtn.classList.add('btn-outline-secondary');
    }
}

function addLogEntry(logEntry) {
    if (!logsVisible) return;
    
    const logsElement = document.getElementById('ble-logs');
    const logLine = `[${logEntry.timestamp}] ${logEntry.message}`;
    
    // Add new log entry
    if (logsElement.textContent) {
        logsElement.textContent += '\n' + logLine;
    } else {
        logsElement.textContent = logLine;
    }
    
    // Auto-scroll to bottom
    logsElement.scrollTop = logsElement.scrollHeight;
    
    // Limit log lines (keep last 50 lines visible)
    const lines = logsElement.textContent.split('\n');
    if (lines.length > 50) {
        logsElement.textContent = lines.slice(-50).join('\n');
    }
}

function updateLogs(logs) {
    if (!logsVisible) return;
    
    const logsElement = document.getElementById('ble-logs');
    logsElement.textContent = '';
    
    logs.forEach(logEntry => {
        addLogEntry(logEntry);
    });
}

// Load available modules from the backend
async function loadModules() {
    try {
        const response = await fetch('/api/scripts');
        modules = await response.json();
        populateModulePool();
    } catch (error) {
        console.error('Error loading modules:', error);
        showStatus('Error loading modules', 'error');
    }
}

// Load current layout from the backend
async function loadLayout() {
    try {
        const response = await fetch('/api/layout');
        currentLayout = await response.json();
        applyLayout();
    } catch (error) {
        console.error('Error loading layout:', error);
        showStatus('Error loading layout', 'error');
    }
}

// Populate the module pool with available modules
function populateModulePool() {
    const pool = document.getElementById('module-pool');
    
    // Keep the add module placeholder and only remove actual modules
    const existingModules = pool.querySelectorAll('.module-item');
    existingModules.forEach(module => module.remove());
    
    modules.forEach(module => {
        // Only show modules that aren't already placed in the grid
        if (!isModuleInGrid(module.id)) {
            const moduleElement = createModuleElement(module);
            pool.appendChild(moduleElement);
            console.log('Added module to pool:', module.id, module.name);
        } else {
            console.log('Module already in grid, not adding to pool:', module.id, module.name);
        }
    });
    
    console.log('Module pool updated. Modules in pool:', pool.querySelectorAll('.module-item').length);
}

// Check if a module is already placed in the grid
function isModuleInGrid(moduleId) {
    return Object.values(currentLayout).includes(moduleId);
}

// Create a draggable module element
function createModuleElement(module) {
    const div = document.createElement('div');
    div.className = 'module-item';
    div.draggable = true;
    div.dataset.moduleId = module.id;
    
    // Add unique identifier to help with tracking
    div.setAttribute('data-module-name', module.name);
    
    // Apply custom color if specified, otherwise use default pastel rotation
    if (module.color) {
        div.style.backgroundColor = module.color;
        div.dataset.customColor = module.color;
    }
    
    div.innerHTML = `
        <div class="module-icon">${module.icon}</div>
        <div class="module-name">${module.name}</div>
    `;
    
    // Add click event to show module details in sidebar overlay
    div.addEventListener('click', (e) => {
        e.stopPropagation();
        showModuleDetails(module);
    });
    
    console.log('Created module element:', module.id, module.name, 'color:', module.color);
    return div;
}

// Apply the current layout to the grid
function applyLayout() {
    console.log('Applying layout:', currentLayout);
    console.log('Available modules:', modules);
    
    // Clear all slots first
    document.querySelectorAll('.module-container').forEach(container => {
        container.innerHTML = '';
    });
    
    // Place modules according to layout
    Object.entries(currentLayout).forEach(([slot, moduleId]) => {
        if (moduleId) {
            console.log(`Looking for module ${moduleId} for slot ${slot}`);
            const module = modules.find(m => m.id === moduleId);
            if (module) {
                console.log(`Found module ${moduleId}:`, module);
                const slotElement = document.querySelector(`[data-slot="${slot}"] .module-container`);
                if (slotElement) {
                    const moduleElement = createModuleElement(module);
                    slotElement.appendChild(moduleElement);
                    console.log(`Placed module ${moduleId} in slot ${slot}`);
                } else {
                    console.warn(`Could not find slot element for ${slot}`);
                }
            } else {
                console.warn(`Could not find module ${moduleId}`);
            }
        }
    });
    
    // Refresh module pool and update visibility
    populateModulePool();
    updateSlotNumberVisibility();
    updateLivePreview(); // Update live preview when layout is applied
}

// Setup drag and drop functionality
function setupDragAndDrop() {
    console.log('Setting up drag and drop...');
    
    // Make module pool sortable (source for modules)
    const modulePool = document.getElementById('module-pool');
    const poolSortable = new Sortable(modulePool, {
        group: {
            name: 'modules',
            pull: 'clone', // Always clone from pool
            put: function(to, from, dragEl, evt) {
                // Safety check for undefined parameters
                if (!dragEl) {
                    console.warn('Invalid dragEl in pool put function');
                    return false;
                }
                
                // Accept modules back from grid slots (for returning unused modules)
                return dragEl.dataset?.moduleId && 
                       dragEl.dataset.moduleId !== 'undefined' &&
                       !dragEl.classList?.contains('add-module-placeholder');
            }
        },
        animation: 150,
        sort: false, // Don't allow sorting within the pool
        filter: '.add-module-placeholder', // Don't allow dragging the add button
        onStart: function(evt) {
            console.log('Drag started from pool:', evt.item.dataset.moduleId);
            evt.item.classList.add('dragging');
            // Highlight all empty slots
            document.querySelectorAll('.grid-slot').forEach(slot => {
                const container = slot.querySelector('.module-container');
                if (container.children.length === 0) {
                    slot.classList.add('drop-zone-available');
                }
            });
        },
        onEnd: function(evt) {
            console.log('Drag ended');
            evt.item.classList.remove('dragging');
            // Remove all highlights and drag-related classes
            cleanupDragStates();
        },
        onAdd: function(evt) {
            console.log('Module returned to pool:', evt.item?.dataset?.moduleId);
            // A module was returned to the pool from a grid slot
            const moduleId = evt.item?.dataset?.moduleId;
            if (moduleId && moduleId !== 'undefined') {
                // Remove from layout and refresh
                removeModuleFromLayout(moduleId);
                updateLayoutAndRefresh();
                saveLayoutSilently();
            }
        }
    });
    
    // Make each grid slot sortable (accepts modules)
    document.querySelectorAll('.module-container').forEach((container, index) => {
        const slotElement = container.closest('.grid-slot');
        const slotId = slotElement.dataset.slot;
        
        const gridSortable = new Sortable(container, {
            group: {
                name: 'modules',
                pull: true, // Allow dragging out to other slots or back to pool
                put: function(to, from, dragEl, evt) {
                    // Safety check for undefined parameters
                    if (!to || !dragEl) {
                        console.warn('Invalid parameters in put function:', { to, from, dragEl });
                        return false;
                    }
                    
                    // The 'to' parameter is a Sortable instance, we need to get the actual DOM element
                    const toElement = to.el; // This is the actual .module-container DOM element
                    
                    // Find the grid slot - 'toElement' is the .module-container, its parent is .grid-slot
                    const gridSlot = toElement?.parentElement;
                    const slotId = gridSlot && gridSlot.dataset ? gridSlot.dataset.slot : 'unknown';
                    const hasSpace = toElement?.children ? toElement.children.length === 0 : false;
                    
                    console.log('✅ Checking if can drop:', {
                        moduleId: dragEl.dataset?.moduleId,
                        slotId: slotId,
                        hasSpace: hasSpace
                    });
                    
                    // Only accept actual modules (not add button) and only if slot is empty
                    const isValidModule = dragEl.dataset?.moduleId && 
                                        dragEl.dataset.moduleId !== 'undefined' && 
                                        !dragEl.classList?.contains('add-module-placeholder');
                    
                    return isValidModule && hasSpace;
                }
            },
            animation: 150,
            onStart: function(evt) {
                console.log('Drag started from grid slot:', slotId);
                evt.item.classList.add('dragging');
                // Show available drop zones (empty slots and the pool)
                document.querySelectorAll('.grid-slot').forEach(slot => {
                    const slotContainer = slot.querySelector('.module-container');
                    if (slotContainer.children.length === 0 || slotContainer === evt.from) {
                        slot.classList.add('drop-zone-available');
                    }
                });
                // Also highlight the module pool as a valid drop zone
                modulePool.classList.add('drop-zone-available');
            },
            onEnd: function(evt) {
                console.log('Drag ended from grid slot');
                evt.item.classList.remove('dragging');
                // Remove highlights and drag-related classes
                cleanupDragStates();
            },
            onMove: function(evt) {
                // Visual feedback when hovering over drop zones
                const targetSlot = evt.related?.closest('.grid-slot');
                
                if (targetSlot) {
                    document.querySelectorAll('.grid-slot').forEach(s => s.classList.remove('drop-zone-hover'));
                    targetSlot.classList.add('drop-zone-hover');
                    console.log('🎯 Hovering over slot:', targetSlot.dataset?.slot);
                }
            },
            onAdd: function(evt) {
                // In event handlers, evt.to is the actual DOM element (.module-container)
                // This is different from the 'put' function where 'to' is the Sortable instance
                const toElement = evt.to; // This is the .module-container DOM element
                const gridSlot = toElement?.parentElement;
                const targetSlot = gridSlot?.dataset?.slot;
                const moduleId = evt.item?.dataset?.moduleId;
                
                console.log('Module added to grid (FIXED v2):', {
                    slot: targetSlot,
                    moduleId: moduleId,
                    fromPool: evt.from?.id === 'module-pool',
                    toElementClass: toElement?.className,
                    gridSlotClass: gridSlot?.className,
                    evtTo: evt.to,
                    evtToTagName: evt.to?.tagName
                });
                
                if (!moduleId || moduleId === 'undefined' || !targetSlot) {
                    console.error('Invalid module ID or target slot, removing element');
                    evt.item?.remove();
                    return;
                }
                
                // If moving from another grid slot, clear the old slot
                if (evt.from?.classList?.contains('module-container')) {
                    const fromElement = evt.from;
                    const fromGridSlot = fromElement.parentElement;
                    const fromSlot = fromGridSlot?.dataset?.slot;
                    if (fromSlot && fromSlot !== targetSlot) {
                        console.log('Clearing old slot:', fromSlot);
                        currentLayout[fromSlot] = null;
                    }
                }
                
                // Update the layout
                currentLayout[targetSlot] = moduleId;
                console.log('Updated layout:', currentLayout);
                
                // Refresh the UI
                updateLayoutAndRefresh();
                
                // Auto-save the layout
                saveLayoutSilently();
                
                // Clean up any remaining drag states
                cleanupDragStates();
            },
            onRemove: function(evt) {
                // In event handlers, evt.from is the actual DOM element (.module-container)
                const fromElement = evt.from;
                const fromGridSlot = fromElement?.parentElement;
                const fromSlot = fromGridSlot?.dataset?.slot;
                const moduleId = evt.item?.dataset?.moduleId;
                
                console.log('Module removed from slot (FIXED v2):', fromSlot, 'moduleId:', moduleId);
                
                // If the item was moved to the pool, clear the layout
                if (evt.to?.id === 'module-pool' && fromSlot) {
                    currentLayout[fromSlot] = null;
                    console.log('Cleared layout for slot:', fromSlot);
                    updateLayoutAndRefresh();
                    saveLayoutSilently();
                }
                // If moved to another grid slot, that will be handled by the onAdd of the target
            }
        });
        
        // Store sortable instance for potential cleanup
        sortableInstances.push(gridSortable);
    });
    
    // Store the pool sortable instance
    sortableInstances.push(poolSortable);
}

// Update layout based on current DOM state and refresh UI
function updateLayoutAndRefresh() {
    console.log('Updating layout and refreshing UI...');
    updateLayoutFromDOM();
    populateModulePool();
    updateSlotNumberVisibility();
    updateLivePreview(); // Update live preview when layout changes
    console.log('Current layout after refresh:', currentLayout);
}

// Update slot number visibility based on whether slots have modules
function updateSlotNumberVisibility() {
    document.querySelectorAll('.grid-slot').forEach(slot => {
        const slotNumber = slot.querySelector('.slot-number');
        const hasModule = slot.querySelector('.module-item');
        
        if (slotNumber) {
            if (hasModule) {
                slotNumber.classList.add('hidden');
            } else {
                slotNumber.classList.remove('hidden');
            }
        }
    });
}

// Update layout based on current DOM state
function updateLayoutFromDOM() {
    const newLayout = {
        "000": null, "001": null, "010": null, "011": null,
        "100": null, "101": null, "110": null, "111": null
    };
    
    document.querySelectorAll('.grid-slot').forEach(slot => {
        const slotId = slot.dataset.slot;
        const moduleElement = slot.querySelector('.module-item');
        if (moduleElement) {
            newLayout[slotId] = moduleElement.dataset.moduleId;
        }
    });
    
    currentLayout = newLayout;
}

// Remove module from layout
function removeModuleFromLayout(moduleId) {
    Object.keys(currentLayout).forEach(slot => {
        if (currentLayout[slot] === moduleId) {
            currentLayout[slot] = null;
        }
    });
}

// Show module details in sidebar overlay
function showModuleDetails(module) {
    const overlay = document.getElementById('sidebar-overlay');
    const details = document.getElementById('module-details');
    
    details.innerHTML = `
        <div class="module-info">
            <div class="module-header">
                <div class="module-icon-large">${module.icon}</div>
                <div class="module-title">
                    <h5>${module.name}</h5>
                </div>
            </div>
            <div class="module-description">
                <h6>Description</h6>
                <p>${module.description}</p>
            </div>
            <div class="module-code">
                <h6>Code</h6>
                <pre><code>${module.code}</code></pre>
            </div>
            
            <!-- Action Buttons -->
            <div class="module-actions mt-4">
                <div class="d-flex gap-2 mb-3">
                    <button type="button" class="btn btn-outline-primary flex-fill" onclick="editModule('${module.id}')">
                        <i class="fas fa-edit me-2"></i>Edit
                    </button>
                    <button type="button" class="btn btn-outline-success flex-fill" onclick="testModule('${module.id}')">
                        <i class="fas fa-play me-2"></i>Test
                    </button>
                    <button type="button" class="btn btn-outline-danger flex-fill" onclick="deleteModule('${module.id}')">
                        <i class="fas fa-trash me-2"></i>Delete
                    </button>
                </div>
            </div>
            
            <!-- Test Output Area (initially hidden) -->
            <div id="test-output-area" class="test-output mt-3" style="display: none;">
                <h6>Test Output</h6>
                <pre id="test-output" class="test-logs"></pre>
            </div>
        </div>
    `;
    
    overlay.classList.add('active');
}

// Show Add Module sidebar form
function showAddModuleSidebar() {
    const overlay = document.getElementById('sidebar-overlay');
    const details = document.getElementById('module-details');
    
    // Update sidebar header
    const sidebarHeader = document.querySelector('.sidebar-header h4');
    sidebarHeader.textContent = 'Add New Module';
    
    details.innerHTML = `
        <div class="add-module-form">
            <div class="form-group mb-3">
                <label for="module-name" class="form-label">Module Name</label>
                <input type="text" class="form-control" id="module-name" placeholder="Enter module name">
            </div>
            
            <div class="form-group mb-3">
                <label for="module-icon" class="form-label">Icon (Emoji)</label>
                <input type="text" class="form-control" id="module-icon" placeholder="🔧" maxlength="2">
            </div>
            
            <div class="form-group mb-3">
                <label for="module-color" class="form-label">Color (Optional)</label>
                <input type="color" class="form-control form-control-color" id="module-color" value="#e3f2fd" title="Choose module color">
                <small class="form-text text-muted">Leave default for automatic pastel color</small>
            </div>
            
            <div class="form-group mb-3">
                <label for="module-description" class="form-label">Description</label>
                <textarea class="form-control" id="module-description" rows="3" placeholder="Enter module description"></textarea>
            </div>
            
            <div class="form-group mb-4">
                <label for="module-code" class="form-label">Python Code</label>
                <textarea class="form-control" id="module-code" rows="10" placeholder="Enter your Python code here..."></textarea>
            </div>
            
            <div class="d-flex gap-2">
                <button type="button" class="btn btn-primary flex-fill" onclick="saveNewModule()">
                    <i class="fas fa-save me-2"></i>Save Module
                </button>
                <button type="button" class="btn btn-secondary" onclick="closeSidebar()">
                    Cancel
                </button>
            </div>
        </div>
    `;
    
    overlay.classList.add('active');
}

// Save new module
async function saveNewModule() {
    const name = document.getElementById('module-name').value.trim();
    const icon = document.getElementById('module-icon').value.trim() || '🔧';
    const color = document.getElementById('module-color').value;
    const description = document.getElementById('module-description').value.trim();
    const code = document.getElementById('module-code').value.trim();
    
    if (!name) {
        showNotification('Please enter a module name', 'error');
        return;
    }
    
    if (!code) {
        showNotification('Please enter module code', 'error');
        return;
    }
    
    try {
        // Send to backend to create the file
        const response = await fetch('/api/scripts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                description: description || 'No description provided',
                icon: icon,
                color: color !== '#e3f2fd' ? color : null, // Only include color if not default
                code: code
            })
        });
        
        const result = await response.json();
        if (result.success) {
            // Reload modules to get the latest data including the new one
            await loadModules();
            populateModulePool();
            updateLivePreview();
            
            showNotification('Module created successfully!', 'success');
            closeSidebar();
        } else {
            showNotification('Error creating module: ' + result.error, 'error');
        }
        
    } catch (error) {
        console.error('Error creating module:', error);
        showNotification('Error creating module', 'error');
    }
}

// Edit module functionality
function editModule(moduleId) {
    const module = modules.find(m => m.id === moduleId);
    if (!module) {
        showNotification('Module not found', 'error');
        return;
    }
    
    const overlay = document.getElementById('sidebar-overlay');
    const details = document.getElementById('module-details');
    
    // Update sidebar header
    const sidebarHeader = document.querySelector('.sidebar-header h4');
    sidebarHeader.textContent = 'Edit Module';
    
    // Parse current code to extract docstring values
    const codeMatch = module.code.match(/"""([\s\S]*?)"""\s*([\s\S]*)/);
    const docstring = codeMatch ? codeMatch[1] : '';
    const codeWithoutDocstring = codeMatch ? codeMatch[2] : module.code;
    
    // Extract metadata from docstring
    const nameMatch = docstring.match(/Name:\s*(.+)/);
    const descMatch = docstring.match(/Description:\s*(.+)/);
    const iconMatch = docstring.match(/Icon:\s*(.+)/);
    const colorMatch = docstring.match(/Color:\s*(.+)/);
    
    const currentName = nameMatch ? nameMatch[1].trim() : module.name;
    const currentDesc = descMatch ? descMatch[1].trim() : module.description;
    const currentIcon = iconMatch ? iconMatch[1].trim() : module.icon;
    const currentColor = colorMatch ? colorMatch[1].trim() : (module.color || '#e3f2fd');
    
    details.innerHTML = `
        <div class="edit-module-form">
            <div class="form-group mb-3">
                <label for="edit-module-name" class="form-label">Module Name</label>
                <input type="text" class="form-control" id="edit-module-name" value="${currentName}">
            </div>
            
            <div class="form-group mb-3">
                <label for="edit-module-icon" class="form-label">Icon (Emoji)</label>
                <input type="text" class="form-control" id="edit-module-icon" value="${currentIcon}" maxlength="2">
            </div>
            
            <div class="form-group mb-3">
                <label for="edit-module-color" class="form-label">Color</label>
                <input type="color" class="form-control form-control-color" id="edit-module-color" value="${currentColor}" title="Choose module color">
            </div>
            
            <div class="form-group mb-3">
                <label for="edit-module-description" class="form-label">Description</label>
                <textarea class="form-control" id="edit-module-description" rows="3">${currentDesc}</textarea>
            </div>
            
            <div class="form-group mb-4">
                <label for="edit-module-code" class="form-label">Python Code</label>
                <textarea class="form-control" id="edit-module-code" rows="15">${codeWithoutDocstring.trim()}</textarea>
            </div>
            
            <div class="d-flex gap-2">
                <button type="button" class="btn btn-success flex-fill" onclick="saveEditedModule('${moduleId}')">
                    <i class="fas fa-save me-2"></i>Save Changes
                </button>
                <button type="button" class="btn btn-secondary" onclick="showModuleDetails(${JSON.stringify(module).replace(/"/g, '&quot;')})">
                    Cancel
                </button>
            </div>
        </div>
    `;
}

// Save edited module
async function saveEditedModule(moduleId) {
    const name = document.getElementById('edit-module-name').value.trim();
    const icon = document.getElementById('edit-module-icon').value.trim();
    const color = document.getElementById('edit-module-color').value;
    const description = document.getElementById('edit-module-description').value.trim();
    const code = document.getElementById('edit-module-code').value.trim();
    
    if (!name || !code) {
        showNotification('Name and code are required', 'error');
        return;
    }
    
    try {
        // Create updated module content
        const colorLine = color !== '#e3f2fd' ? `Color: ${color}\n` : '';
        const moduleContent = `"""
Name: ${name}
Description: ${description}
Icon: ${icon}
${colorLine}"""

${code}`;
        
        // Send to backend to save the file
        const response = await fetch(`/api/scripts/${moduleId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                description: description,
                icon: icon,
                color: color !== '#e3f2fd' ? color : null,
                code: code
            })
        });
        
        const result = await response.json();
        if (result.success) {
            // Update the module in our local array
            const moduleIndex = modules.findIndex(m => m.id === moduleId);
            if (moduleIndex !== -1) {
                modules[moduleIndex] = {
                    ...modules[moduleIndex],
                    name: name,
                    description: description,
                    icon: icon,
                    color: color !== '#e3f2fd' ? color : null,
                    code: moduleContent
                };
                
                // Refresh UI - reload all modules to get the latest data
                loadModules().then(() => {
                    updateLayoutAndRefresh();
                    // Find the updated module and show its details
                    const updatedModule = modules.find(m => m.id === moduleId);
                    if (updatedModule) {
                        showModuleDetails(updatedModule);
                    }
                });
            }
            
            showNotification('Module saved successfully!', 'success');
        } else {
            showNotification('Error saving module: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error saving module:', error);
        showNotification('Error saving module', 'error');
    }
}

// Test module functionality
async function testModule(moduleId) {
    const module = modules.find(m => m.id === moduleId);
    if (!module) {
        showNotification('Module not found', 'error');
        return;
    }
    
    const details = document.getElementById('module-details');
    
    // Show loading state
    details.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Testing module...</span>
            </div>
            <p class="mt-3">Running module test...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`/api/scripts/${moduleId}/test`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        // Show test results
        details.innerHTML = `
            <div class="test-results">
                <div class="d-flex align-items-center justify-content-between mb-3">
                    <h5 class="mb-0">Test Results: ${module.name}</h5>
                    <button type="button" class="btn-close" onclick="showModuleDetails(${JSON.stringify(module).replace(/"/g, '&quot;')})"></button>
                </div>
                
                <div class="alert ${result.success ? 'alert-success' : 'alert-danger'}" role="alert">
                    <strong>${result.success ? 'Success!' : 'Error:'}</strong> ${result.success ? 'Module executed without errors' : 'Module execution failed'}
                </div>
                
                ${result.output ? `
                    <div class="mb-3">
                        <h6>Output:</h6>
                        <pre class="bg-light p-3 rounded"><code>${result.output}</code></pre>
                    </div>
                ` : ''}
                
                ${result.error ? `
                    <div class="mb-3">
                        <h6>Error Details:</h6>
                        <pre class="bg-danger-subtle p-3 rounded"><code>${result.error}</code></pre>
                    </div>
                ` : ''}
                
                <div class="d-flex gap-2">
                    <button type="button" class="btn btn-primary" onclick="showModuleDetails(${JSON.stringify(module).replace(/"/g, '&quot;')})">
                        <i class="fas fa-arrow-left me-2"></i>Back to Details
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="testModule('${moduleId}')">
                        <i class="fas fa-redo me-2"></i>Test Again
                    </button>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error testing module:', error);
        details.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <strong>Error:</strong> Failed to test module. Please try again.
                <div class="mt-3">
                    <button type="button" class="btn btn-primary" onclick="showModuleDetails(${JSON.stringify(module).replace(/"/g, '&quot;')})">
                        <i class="fas fa-arrow-left me-2"></i>Back to Details
                    </button>
                </div>
            </div>
        `;
        showNotification('Error testing module', 'error');
    }
}

// Delete module functionality
function deleteModule(moduleId) {
    const module = modules.find(m => m.id === moduleId);
    if (!module) {
        showNotification('Module not found', 'error');
        return;
    }
    
    // Show confirmation dialog
    if (confirm(`Are you sure you want to delete the module "${module.name}"?\n\nThis action cannot be undone and will permanently delete the file.`)) {
        performDeleteModule(moduleId);
    }
}

async function performDeleteModule(moduleId) {
    const module = modules.find(m => m.id === moduleId);
    
    try {
        const response = await fetch(`/api/scripts/${moduleId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        if (result.success) {
            // Remove from local modules array
            const moduleIndex = modules.findIndex(m => m.id === moduleId);
            if (moduleIndex !== -1) {
                modules.splice(moduleIndex, 1);
            }
            
            // Remove from any grid positions
            Object.keys(currentLayout).forEach(position => {
                if (currentLayout[position] === moduleId) {
                    currentLayout[position] = null;
                }
            });
            
            // Close sidebar and refresh UI - reload all modules
            closeSidebar();
            loadModules().then(() => {
                updateLayoutAndRefresh();
            });
            
            showNotification('Module deleted successfully', 'success');
        } else {
            showNotification('Error deleting module: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error deleting module:', error);
        showNotification('Error deleting module', 'error');
    }
}

// Close sidebar overlay
function closeSidebar() {
    const overlay = document.getElementById('sidebar-overlay');
    const sidebarHeader = document.querySelector('.sidebar-header h4');
    
    // Reset header text
    sidebarHeader.textContent = 'Module Details';
    
    overlay.classList.remove('active');
}

// Setup event listeners
function setupEventListeners() {
    // Add Module button click handler
    document.addEventListener('click', function(event) {
        if (event.target.closest('.add-module-placeholder')) {
            event.stopPropagation();
            showAddModuleSidebar();
        }
    });
    
    // Close sidebar when clicking outside
    document.addEventListener('click', function(event) {
        const overlay = document.getElementById('sidebar-overlay');
        const target = event.target;
        
        if (overlay.classList.contains('active') && 
            !overlay.contains(target) && 
            !target.classList.contains('module-item') &&
            !target.closest('.module-item') &&
            !target.closest('.add-module-placeholder')) {
            closeSidebar();
        }
    });
    
    // Prevent sidebar from closing when clicking inside it
    document.getElementById('sidebar-overlay').addEventListener('click', function(event) {
        event.stopPropagation();
    });
}

// Save current layout to backend (silent version without notification)
async function saveLayoutSilently() {
    try {
        const response = await fetch('/api/layout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(currentLayout)
        });
        
        const result = await response.json();
        if (result.success) {
            console.log('Layout auto-saved successfully');
        } else {
            console.error('Error auto-saving layout:', result.error);
        }
    } catch (error) {
        console.error('Error auto-saving layout:', error);
    }
}

// Save current layout to backend (with notification)
// Show notification dropdown from top-right
function showNotification(message, type = 'success') {
    const notificationArea = document.getElementById('notification-area');
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const icon = type === 'success' ? '✓' : '!';
    
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-icon">${icon}</div>
            <div class="notification-message">${message}</div>
        </div>
    `;
    
    notificationArea.appendChild(notification);
    
    // Trigger the slide-in animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

// Show status message
function showStatus(message, type) {
    const statusDiv = document.getElementById('save-status');
    statusDiv.innerHTML = `<div class="alert alert-${type === 'success' ? 'success' : 'danger'} fade show" role="alert">
        ${message}
    </div>`;
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        statusDiv.innerHTML = '';
    }, 3000);
}

// Live preview update function
function updateLivePreview() {
    console.log('Updating live preview with current layout:', currentLayout);
    
    // Clear all preview buttons first
    document.querySelectorAll('.preview-button').forEach(button => {
        button.innerHTML = '';
        button.style.backgroundColor = '#dee2e6'; // default gray
        button.classList.remove('active');
    });
    
    // Update preview buttons with current layout
    Object.entries(currentLayout).forEach(([slotId, moduleId]) => {
        const previewButton = document.querySelector(`[data-preview="${slotId}"]`);
        if (previewButton && moduleId) {
            const module = modules.find(m => m.id === moduleId);
            if (module) {
                previewButton.innerHTML = module.icon;
                previewButton.style.fontSize = '10px';
                previewButton.style.display = 'flex';
                previewButton.style.alignItems = 'center';
                previewButton.style.justifyContent = 'center';
                if (module.color) {
                    previewButton.style.backgroundColor = module.color;
                } else {
                    previewButton.style.backgroundColor = '#007bff'; // default blue
                }
                console.log('Updated preview button for slot', slotId, 'with module', moduleId, 'icon:', module.icon);
            }
        }
    });
}

// Make functions available globally for onclick handlers
window.connectBLE = connectBLE;
window.disconnectBLE = disconnectBLE;
window.toggleLogs = toggleLogs;
