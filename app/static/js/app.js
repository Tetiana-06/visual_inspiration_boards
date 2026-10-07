// State Management
const state = {
    currentUser: { id: 1, name: "Тетяна Шостак", email: "tetiana.shostak@inspiration.art" },
    usersList: [
        { id: 1, name: "Тетяна Шостак", email: "tetiana.shostak@inspiration.art" },
        { id: 2, name: "Наталія Шостак", email: "nataliia.shostak@inspiration.art" }
    ],
    boards: [],
    currentBoard: null,
    elements: [],
    dirtyBatch: false,
    draggedElement: null,
    dragOffset: { x: 0, y: 0 },
    lastExportData: null
};

const API_BASE = "/api/v1";

// DOM Initialization
document.addEventListener("DOMContentLoaded", async () => {
    lucide.createIcons();
    await checkSystemHealth();
    await loadBoards();
    setupCanvasDragEvents();
});

// System Health Check (background)
async function checkSystemHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();
        const badge = document.getElementById("systemHealthBadge");
        const badgeText = document.getElementById("healthStatusText");

        if (badge && badgeText) {
            if (data.status === "healthy") {
                badge.className = "hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-200/80";
                badgeText.textContent = `PostgreSQL & Redis: Active (v${data.version})`;
            } else {
                badge.className = "hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-50 text-amber-700 text-xs font-medium border border-amber-200/80";
                badgeText.textContent = `Status: ${data.status} (Redis: ${data.redis})`;
            }
        }
    } catch (e) {
        console.error("Health check error:", e);
    }
}

// User Switching
function switchUser() {
    if (state.currentUser.id === 1) {
        state.currentUser = state.usersList[1];
    } else {
        state.currentUser = state.usersList[0];
    }
    const avatarBtn = document.getElementById("currentUserAvatarBtn");
    if (avatarBtn) {
        const nextUser = state.currentUser.id === 1 ? state.usersList[1].name : state.usersList[0].name;
        avatarBtn.setAttribute("title", `Користувач: ${state.currentUser.name} (натисніть для зміни на ${nextUser})`);
    }
    showToast(`Ви увійшли як: ${state.currentUser.name}`, "info");
}

// Load Boards Gallery
async function loadBoards(searchQuery = "") {
    try {
        let url = `${API_BASE}/boards`;
        if (searchQuery) url += `?search=${encodeURIComponent(searchQuery)}`;
        const res = await fetch(url);
        state.boards = await res.json();
        renderBoardsGrid(state.boards);
    } catch (e) {
        showToast("Помилка завантаження дощок", "error");
    }
}

function handleSearch(query) {
    loadBoards(query);
}

// Render Boards Grid
function renderBoardsGrid(boards) {
    const grid = document.getElementById("boardsGrid");
    grid.innerHTML = "";

    if (!boards || boards.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full py-16 text-center text-stone-600">
                <i data-lucide="layout-grid" class="w-12 h-12 mx-auto mb-3 opacity-40"></i>
                <p class="text-base font-medium">Ще немає створених дощок</p>
                <p class="text-xs text-stone-600 mt-1">Створіть свій перший простір для візуального натхнення</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    boards.forEach(board => {
        const card = document.createElement("div");
        card.className = "card-soft overflow-hidden group cursor-pointer flex flex-col justify-between";
        card.style.backgroundColor = board.background_color || "#FAF8F5";

        card.innerHTML = `
            <div class="p-6">
                <div class="flex items-start justify-between gap-2 mb-3">
                    <span class="text-[11px] font-semibold tracking-wider uppercase px-2.5 py-1 rounded-full bg-white/80 text-stone-700 shadow-xs border border-stone-200/50">
                        ${board.grid_type} • v${board.version}
                    </span>
                    <button onclick="event.stopPropagation(); deleteBoard(${board.id})" class="p-1.5 rounded-full hover:bg-stone-200/60 text-stone-600 hover:text-stone-900 transition-colors" title="Видалити дошку">
                        <i data-lucide="trash-2" class="w-4 h-4"></i>
                    </button>
                </div>

                <h3 class="text-xl font-bold font-editorial text-stone-900 group-hover:text-pin transition-colors">${escapeHtml(board.title)}</h3>
                <p class="text-xs text-stone-700 mt-2 line-clamp-2 leading-relaxed">${escapeHtml(board.description || 'Немає опису концепції.')}</p>
            </div>

            <div class="px-6 py-4 bg-white/60 border-t border-stone-200/50 flex items-center justify-end gap-2">
                <button onclick="event.stopPropagation(); exportBoardById(${board.id})" class="p-2 hover:bg-white text-stone-600 hover:text-stone-900 shadow-2xs" title="Експорт">
                    <i data-lucide="download" class="w-4 h-4"></i>
                </button>
                <!-- Button renamed to 'Відкрити' without arrow and sharp -->
                <button onclick="openBoardStudio(${board.id})" class="px-4 py-1.5 bg-stone-900 text-white hover:bg-stone-800 text-xs font-semibold shadow-xs flex items-center">
                    <span>Відкрити</span>
                </button>
            </div>
        `;
        grid.appendChild(card);
    });

    lucide.createIcons();
}

// Open Interactive Canvas View
async function openBoardStudio(boardId) {
    try {
        const res = await fetch(`${API_BASE}/boards/${boardId}`);
        if (!res.ok) throw new Error("Board not found");
        state.currentBoard = await res.json();
        state.elements = state.currentBoard.elements || [];
        state.dirtyBatch = false;

        // Switch Views
        document.getElementById("galleryView").classList.add("hidden");
        document.getElementById("canvasView").classList.remove("hidden");

        // Set Headers
        document.getElementById("currentBoardTitle").textContent = state.currentBoard.title;
        document.getElementById("currentBoardDesc").textContent = state.currentBoard.description || "";
        document.getElementById("boardVersionBadge").textContent = `v${state.currentBoard.version}`;
        document.getElementById("collabsCountBadge").textContent = `${state.currentBoard.collaborators?.length || 1}`;

        // Set Canvas background
        const canvas = document.getElementById("moodboardCanvas");
        canvas.style.backgroundColor = state.currentBoard.background_color || "#FAF8F5";

        renderCanvasElements();
        updateBatchButtonState();
        lucide.createIcons();
    } catch (e) {
        showToast("Не вдалося відкрити дошку: " + e.message, "error");
    }
}

function showGalleryView() {
    document.getElementById("canvasView").classList.add("hidden");
    document.getElementById("galleryView").classList.remove("hidden");
    loadBoards();
}

// Render Canvas Elements
function renderCanvasElements() {
    const canvas = document.getElementById("moodboardCanvas");
    canvas.innerHTML = "";

    state.elements.forEach(el => {
        const elCard = document.createElement("div");
        elCard.className = "canvas-card select-none group";
        elCard.dataset.id = el.id;
        elCard.style.left = `${el.x}px`;
        elCard.style.top = `${el.y}px`;
        elCard.style.width = `${el.width}px`;
        elCard.style.zIndex = el.z_index;

        let contentHtml = "";

        if (el.element_type === "image") {
            contentHtml = `
                <div class="bg-white p-3 rounded-2xl shadow-md border border-stone-200/70 hover:shadow-xl transition-all">
                    <div class="overflow-hidden rounded-xl bg-stone-100 aspect-[3/4] relative">
                        <img src="${escapeHtml(el.content.image_url)}" alt="${escapeHtml(el.content.title || '')}" class="w-full h-full object-cover pointer-events-none">
                    </div>
                    ${el.content.title ? `<div class="mt-2.5 font-semibold text-xs text-stone-900">${escapeHtml(el.content.title)}</div>` : ''}
                    ${el.content.caption ? `<div class="text-[11px] text-stone-700 leading-snug line-clamp-2 mt-0.5">${escapeHtml(el.content.caption)}</div>` : ''}
                </div>
            `;
        } else if (el.element_type === "note") {
            const noteBg = el.content.color || "#FEF3C7";
            contentHtml = `
                <div class="sticky-paper p-5 rounded-2xl border border-stone-300/40" style="background-color: ${noteBg}; min-height: 140px;">
                    <div class="text-[11px] font-semibold text-stone-700 tracking-wider uppercase mb-1">${escapeHtml(el.content.title || 'Нотатка')}</div>
                    <p class="text-xs text-stone-800 leading-relaxed font-sans whitespace-pre-line">${escapeHtml(el.content.text || '')}</p>
                    ${el.content.author ? `<div class="mt-3 text-[10px] text-stone-600 font-medium text-right">— ${escapeHtml(el.content.author)}</div>` : ''}
                </div>
            `;
        } else if (el.element_type === "palette") {
            const colors = el.content.colors || ["#EDE0D4", "#DDB892", "#B08968", "#7F5539", "#463F3A"];
            const swatches = colors.map(c => `
                <div class="palette-swatch flex-1 h-16 rounded-xl flex items-end justify-center pb-1 text-[9px] font-mono font-bold text-white shadow-xs drop-shadow" 
                     style="background-color: ${c}" title="Колір: ${c}" onclick="copyHex('${c}')">
                    <span class="bg-black/30 px-1 rounded backdrop-blur-xs">${c}</span>
                </div>
            `).join("");

            contentHtml = `
                <div class="bg-white p-4 rounded-2xl shadow-md border border-stone-200/80">
                    <div class="flex items-center justify-between mb-2.5">
                        <span class="text-xs font-bold text-stone-800 font-editorial">${escapeHtml(el.content.title || 'Кольорова палітра')}</span>
                        <i data-lucide="palette" class="w-3.5 h-3.5 text-stone-600"></i>
                    </div>
                    <div class="flex gap-1.5">${swatches}</div>
                </div>
            `;
        } else if (el.element_type === "sticker") {
            const emoji = el.content.emoji || "✨";
            contentHtml = `
                <div class="bg-white/95 backdrop-blur-md px-5 py-4 rounded-2xl shadow-md border border-stone-200 flex items-center gap-3">
                    <span class="text-2xl">${emoji}</span>
                    <div>
                        <div class="text-xs font-bold font-editorial text-stone-900">${escapeHtml(el.content.text || '')}</div>
                    </div>
                </div>
            `;
        }

        // Element Actions overlay (Delete & Bring to front)
        elCard.innerHTML = `
            ${contentHtml}
            <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 z-20">
                <button onclick="bringToFront(${el.id})" class="p-1 rounded-full bg-white/90 text-stone-700 hover:text-stone-900 shadow-sm" title="На передній план">
                    <i data-lucide="bring-to-front" class="w-3.5 h-3.5"></i>
                </button>
                <button onclick="deleteCanvasElement(${el.id})" class="p-1 rounded-full bg-white/90 text-rose-600 hover:text-rose-800 shadow-sm" title="Видалити">
                    <i data-lucide="x" class="w-3.5 h-3.5"></i>
                </button>
            </div>
        `;

        canvas.appendChild(elCard);
    });

    lucide.createIcons();
}

// Drag & Drop Mechanics for 2D Canvas
function setupCanvasDragEvents() {
    const canvas = document.getElementById("moodboardCanvas");

    canvas.addEventListener("mousedown", (e) => {
        const card = e.target.closest(".canvas-card");
        if (!card) return;
        if (e.target.closest("button") || e.target.closest(".palette-swatch")) return; // Don't drag on button click

        state.draggedElement = card;
        const rect = card.getBoundingClientRect();
        state.dragOffset.x = e.clientX - rect.left;
        state.dragOffset.y = e.clientY - rect.top;

        card.classList.add("is-dragging");
        e.preventDefault();
    });

    document.addEventListener("mousemove", (e) => {
        if (!state.draggedElement) return;

        const canvasRect = canvas.getBoundingClientRect();
        let newX = e.clientX - canvasRect.left - state.dragOffset.x;
        let newY = e.clientY - canvasRect.top - state.dragOffset.y;

        // Bounding constraints
        newX = Math.max(10, Math.min(newX, canvasRect.width - state.draggedElement.offsetWidth - 10));
        newY = Math.max(10, Math.min(newY, canvasRect.height - state.draggedElement.offsetHeight - 10));

        state.draggedElement.style.left = `${newX}px`;
        state.draggedElement.style.top = `${newY}px`;

        // Update in-memory state
        const elId = parseInt(state.draggedElement.dataset.id);
        const item = state.elements.find(el => el.id === elId);
        if (item) {
            item.x = Math.round(newX);
            item.y = Math.round(newY);
        }

        markDirty();
    });

    document.addEventListener("mouseup", () => {
        if (state.draggedElement) {
            state.draggedElement.classList.remove("is-dragging");
            state.draggedElement = null;
        }
    });
}

function bringToFront(elementId) {
    const maxZ = state.elements.reduce((max, el) => Math.max(max, el.z_index), 1);
    const target = state.elements.find(el => el.id === elementId);
    if (target) {
        target.z_index = maxZ + 1;
        const domCard = document.querySelector(`.canvas-card[data-id="${elementId}"]`);
        if (domCard) domCard.style.zIndex = target.z_index;
        markDirty();
    }
}

function markDirty() {
    state.dirtyBatch = true;
    updateBatchButtonState();
}

function updateBatchButtonState() {
    const btn = document.getElementById("batchSaveBtn");
    const text = document.getElementById("batchSaveBtnText");
    if (state.dirtyBatch) {
        btn.className = "px-4 py-2 rounded-xl bg-[#0ABAB5] hover:bg-[#089A96] text-white text-xs font-semibold shadow-md shadow-[#0ABAB5]/30 flex items-center gap-1.5 transition-all animate-pulse";
        text.textContent = "💾 Зберегти зміни (Batch)";
    } else {
        btn.className = "px-4 py-2 rounded-xl bg-stone-900 hover:bg-stone-800 text-white text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-all";
        text.textContent = "✓ Синхронізовано";
    }
}

// BATCH SYNC ENDPOINT (High-Throughput Operation with Optimistic Locking)
async function saveCanvasBatch() {
    if (!state.currentBoard) return;

    const payload = {
        expected_board_version: state.currentBoard.version,
        elements: state.elements.map(el => ({
            id: el.id,
            element_type: el.element_type,
            x: el.x,
            y: el.y,
            width: el.width,
            height: el.height,
            z_index: el.z_index,
            content: el.content
        }))
    };

    try {
        const res = await fetch(`${API_BASE}/boards/${state.currentBoard.id}/elements/batch`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.status === 409) {
            const err = await res.json();
            showToast(`⚠️ Конфлікт версій (Optimistic Lock): ${err.detail}. Оновіть дошку.`, "error");
            return;
        }

        if (!res.ok) throw new Error("Помилка синхронізації");

        const data = await res.json();
        state.currentBoard.version = data.new_board_version;
        document.getElementById("boardVersionBadge").textContent = `v${state.currentBoard.version}`;
        state.dirtyBatch = false;
        updateBatchButtonState();
        showToast(`Успішно збережено ${data.updated_count} елементів! (Нова версія: v${data.new_board_version})`, "success");
    } catch (e) {
        showToast("Помилка збереження: " + e.message, "error");
    }
}

// Create Canvas Element
function openAddElementModal(type) {
    document.getElementById("elTypeInput").value = type;
    document.getElementById("addElementModalTitle").textContent = 
        type === "note" ? "Додати стікер-нотатку" :
        type === "image" ? "Додати фотографію" :
        type === "palette" ? "Додати кольорову палітру" : "Додати цитату";

    // Toggle form sections
    document.getElementById("formSectionNote").classList.toggle("hidden", type !== "note");
    document.getElementById("formSectionImage").classList.toggle("hidden", type !== "image");
    document.getElementById("formSectionPalette").classList.toggle("hidden", type !== "palette");
    document.getElementById("formSectionSticker").classList.toggle("hidden", type !== "sticker");

    openModal("addElementModal");
}

function selectImagePreset(url, title) {
    document.getElementById("imageUrl").value = url;
    document.getElementById("imageTitle").value = title;
}

async function handleCreateElement(e) {
    e.preventDefault();
    const type = document.getElementById("elTypeInput").value;
    let content = {};
    let width = 280;
    let height = 240;

    if (type === "note") {
        const checkedColor = document.querySelector('input[name="noteColor"]:checked')?.value || "#FEF3C7";
        content = {
            title: document.getElementById("noteTitle").value || "Нотатка",
            text: document.getElementById("noteText").value,
            color: checkedColor,
            author: state.currentUser.name
        };
        height = 180;
    } else if (type === "image") {
        content = {
            title: document.getElementById("imageTitle").value || "Фото",
            image_url: document.getElementById("imageUrl").value,
            caption: "Збережено у мудборд"
        };
        width = 320;
        height = 420;
    } else if (type === "palette") {
        const rawColors = document.getElementById("paletteColors").value;
        const colors = rawColors.split(",").map(c => c.trim()).filter(Boolean);
        content = {
            title: document.getElementById("paletteTitle").value || "Палітра кольорів",
            colors: colors.length ? colors : ["#EDE0D4", "#DDB892", "#B08968", "#7F5539"]
        };
        width = 320;
        height = 140;
    } else if (type === "sticker") {
        content = {
            text: document.getElementById("stickerText").value,
            emoji: document.getElementById("stickerEmoji").value || "✨"
        };
        width = 260;
        height = 90;
    }

    // Place randomly in visible canvas zone
    const x = 50 + Math.floor(Math.random() * 300);
    const y = 80 + Math.floor(Math.random() * 200);

    const payload = {
        element_type: type,
        x: x,
        y: y,
        width: width,
        height: height,
        z_index: state.elements.length + 1,
        content: content
    };

    try {
        const res = await fetch(`${API_BASE}/boards/${state.currentBoard.id}/elements`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Не вдалося створити елемент");

        const newEl = await res.json();
        state.elements.push(newEl);
        state.currentBoard.version += 1;
        document.getElementById("boardVersionBadge").textContent = `v${state.currentBoard.version}`;

        closeModal("addElementModal");
        renderCanvasElements();
        showToast("Елемент додано на полотно!", "success");
    } catch (e) {
        showToast(e.message, "error");
    }
}

// Delete Canvas Element
async function deleteCanvasElement(elementId) {
    try {
        const res = await fetch(`${API_BASE}/boards/${state.currentBoard.id}/elements/${elementId}`, {
            method: "DELETE"
        });

        if (!res.ok) throw new Error("Не вдалося видалити");

        state.elements = state.elements.filter(el => el.id !== elementId);
        state.currentBoard.version += 1;
        document.getElementById("boardVersionBadge").textContent = `v${state.currentBoard.version}`;
        renderCanvasElements();
        showToast("Елемент видалено", "info");
    } catch (e) {
        showToast(e.message, "error");
    }
}

// Create Board
function openCreateBoardModal() {
    document.getElementById("newBoardTitle").value = "";
    document.getElementById("newBoardDesc").value = "";
    openModal("createBoardModal");
}

async function handleCreateBoard(e) {
    e.preventDefault();
    const title = document.getElementById("newBoardTitle").value;
    const desc = document.getElementById("newBoardDesc").value;
    const bg = document.querySelector('input[name="boardBg"]:checked')?.value || "#FAF8F5";

    const payload = {
        title: title,
        description: desc,
        background_color: bg,
        grid_type: "freeform",
        owner_id: state.currentUser.id
    };

    try {
        const res = await fetch(`${API_BASE}/boards`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Не вдалося створити дошку");

        const newBoard = await res.json();
        closeModal("createBoardModal");
        showToast("Дошку створено!", "success");
        await openBoardStudio(newBoard.id);
    } catch (e) {
        showToast(e.message, "error");
    }
}

// Delete Board
async function deleteBoard(boardId) {
    if (!confirm("Ви впевнені, що бажаєте видалити цю дошку?")) return;

    try {
        const res = await fetch(`${API_BASE}/boards/${boardId}`, {
            method: "DELETE"
        });
        if (!res.ok) throw new Error("Помилка видалення");
        showToast("Дошку видалено", "info");
        await loadBoards();
    } catch (e) {
        showToast(e.message, "error");
    }
}

// Export Board Snapshot (High-Load Scenario)
async function exportCurrentBoard() {
    if (!state.currentBoard) return;
    await exportBoardById(state.currentBoard.id);
}

async function exportBoardById(boardId) {
    try {
        const res = await fetch(`${API_BASE}/boards/${boardId}/export`);
        if (!res.ok) throw new Error("Помилка експорту");
        const data = await res.json();
        state.lastExportData = data;

        // Render Summary Stats
        const statsEl = document.getElementById("exportSummaryStats");
        statsEl.innerHTML = `
            <div>
                <span class="text-stone-600 block">Всього блоків:</span>
                <span class="font-bold text-stone-900 text-sm">${data.summary.total_elements}</span>
            </div>
            <div>
                <span class="text-stone-600 block">Розміри полотна:</span>
                <span class="font-bold text-stone-900 text-sm">${data.summary.canvas_dimensions}</span>
            </div>
            <div>
                <span class="text-stone-600 block">Версія експорту:</span>
                <span class="font-bold text-stone-900 text-sm">v${data.export_version}</span>
            </div>
        `;

        // Render formatted JSON
        document.getElementById("exportJsonCode").textContent = JSON.stringify(data, null, 2);
        openModal("exportModal");
        lucide.createIcons();
    } catch (e) {
        showToast(e.message, "error");
    }
}

function copyExportJson() {
    if (!state.lastExportData) return;
    navigator.clipboard.writeText(JSON.stringify(state.lastExportData, null, 2));
    showToast("JSON скопійовано в буфер обміну!", "success");
}

function downloadExportJson() {
    if (!state.lastExportData) return;
    const blob = new Blob([JSON.stringify(state.lastExportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `board_export_${state.lastExportData.board.id}_v${state.lastExportData.board.version}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Файл завантажено", "success");
}

// Collaborators Modal
async function openCollaboratorsModal() {
    if (!state.currentBoard) return;
    try {
        const res = await fetch(`${API_BASE}/boards/${state.currentBoard.id}/collaborators`);
        const collabs = await res.json();

        const listEl = document.getElementById("collaboratorsList");
        listEl.innerHTML = collabs.map(c => `
            <div class="flex items-center justify-between p-2.5 rounded-xl bg-stone-50 border border-stone-200/70 text-xs">
                <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold">
                        ${(c.user_name || 'U')[0]}
                    </div>
                    <div>
                        <div class="font-semibold text-stone-900">${escapeHtml(c.user_name || 'Користувач')}</div>
                        <div class="text-[10px] text-stone-600">${escapeHtml(c.user_email || '')}</div>
                    </div>
                </div>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${c.role === 'OWNER' ? 'bg-amber-100 text-amber-800' : 'bg-stone-200 text-stone-700'}">
                    ${c.role}
                </span>
            </div>
        `).join("");

        openModal("collabsModal");
        lucide.createIcons();
    } catch (e) {
        showToast("Не вдалося завантажити учасників", "error");
    }
}

async function handleAddCollaborator(e) {
    e.preventDefault();
    const userId = parseInt(document.getElementById("newCollabUserId").value);
    const role = document.getElementById("newCollabRole").value;

    try {
        const res = await fetch(`${API_BASE}/boards/${state.currentBoard.id}/collaborators`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, role: role })
        });
        if (!res.ok) throw new Error("Помилка надання доступу");
        showToast("Учасника додано!", "success");
        await openCollaboratorsModal();
    } catch (e) {
        showToast(e.message, "error");
    }
}

// Helper Utilities
function copyHex(hex) {
    navigator.clipboard.writeText(hex);
    showToast(`Колір скопійовано: ${hex}`, "info");
}

function openModal(id) {
    document.getElementById(id).classList.remove("hidden");
    lucide.createIcons();
}

function closeModal(id) {
    document.getElementById(id).classList.add("hidden");
}

function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/[&<>"']/g, function(m) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        }[m];
    });
}

function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    const bg = type === "success" ? "bg-teal-800 text-white" :
               type === "error" ? "bg-rose-800 text-white" : "bg-stone-900 text-white";

    toast.className = `${bg} px-4 py-2.5 rounded-2xl shadow-xl text-xs font-medium flex items-center gap-2 pointer-events-auto animate-enter`;
    toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}
