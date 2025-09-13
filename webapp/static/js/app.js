// Global variables
let modules = [];
let currentLayout = {};
let sortableInstances = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadModules();
    loadLayout();
    setupDragAndDrop();
    setupEventListeners();
    startDeviceSimulation();
});

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
    
    div.innerHTML = `
        <div class="module-icon">${module.icon}</div>
        <div class="module-name">${module.name}</div>
    `;
    
    // Add click event to show module details in sidebar overlay
    div.addEventListener('click', (e) => {
        e.stopPropagation();
        showModuleDetails(module);
    });
    
    console.log('Created module element:', module.id, module.name);
    return div;
}

// Apply the current layout to the grid
function applyLayout() {
    // Clear all slots first
    document.querySelectorAll('.module-container').forEach(container => {
        container.innerHTML = '';
    });
    
    // Place modules according to layout
    Object.entries(currentLayout).forEach(([slot, moduleId]) => {
        if (moduleId) {
            const module = modules.find(m => m.id === moduleId);
            if (module) {
                const slotElement = document.querySelector(`[data-slot="${slot}"] .module-container`);
                const moduleElement = createModuleElement(module);
                slotElement.appendChild(moduleElement);
            }
        }
    });
    
    // Refresh module pool and update visibility
    populateModulePool();
    updateSlotNumberVisibility();
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
            // Remove all highlights
            document.querySelectorAll('.grid-slot').forEach(slot => {
                slot.classList.remove('drop-zone-available', 'drop-zone-hover');
            });
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
                // Remove highlights
                document.querySelectorAll('.grid-slot').forEach(slot => {
                    slot.classList.remove('drop-zone-available', 'drop-zone-hover');
                });
                modulePool.classList.remove('drop-zone-available', 'drop-zone-hover');
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
                
                // Simulate button press for demo
                simulateButtonPress(targetSlot);
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
        // Create the module file content with proper docstring format
        const moduleContent = `"""
Name: ${name}
Description: ${description || 'No description provided'}
Icon: ${icon}
"""

${code}`;

        // For now, we'll simulate saving - in a real app you'd send this to the backend
        const moduleId = name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
        
        // Add to modules array (simulate backend response)
        const newModule = {
            id: moduleId,
            name: name,
            description: description || 'No description provided',
            icon: icon,
            path: `${moduleId}.py`,
            code: moduleContent
        };
        
        modules.push(newModule);
        populateModulePool();
        
        showNotification('Saved module!', 'success');
        closeSidebar();
        
    } catch (error) {
        console.error('Error saving module:', error);
        showNotification('Error saving module', 'error');
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
    // Save layout button
    document.getElementById('save-layout').addEventListener('click', saveLayout);
    
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
async function saveLayout() {
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
            showNotification('Layout saved successfully!', 'success');
        } else {
            showNotification('Error saving layout: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error saving layout:', error);
        showNotification('Error saving layout', 'error');
    }
}

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

// Device simulation functions
function startDeviceSimulation() {
    // Simulate connection status
    updateConnectionStatus();
    
    // Simulate battery level changes
    updateBatteryLevel();
    
    // Update every 30 seconds for demo purposes
    setInterval(() => {
        updateConnectionStatus();
        updateBatteryLevel();
    }, 30000);
}

function updateConnectionStatus() {
    const statusElement = document.getElementById('connection-status');
    const isConnected = Math.random() > 0.1; // 90% connected
    
    statusElement.textContent = isConnected ? 'Connected' : 'Disconnected';
    statusElement.className = `status-value ${isConnected ? 'connected' : 'disconnected'}`;
}

function updateBatteryLevel() {
    const batteryElement = document.getElementById('battery-level');
    const currentLevel = parseInt(batteryElement.textContent);
    const newLevel = Math.max(20, currentLevel - Math.floor(Math.random() * 5));
    
    batteryElement.textContent = `${newLevel}%`;
}

function simulateButtonPress(slot) {
    const previewButton = document.querySelector(`[data-preview="${slot}"]`);
    if (previewButton) {
        previewButton.classList.add('active');
        setTimeout(() => {
            previewButton.classList.remove('active');
        }, 1000);
    }
}
