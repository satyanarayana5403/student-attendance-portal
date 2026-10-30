// Page loader
window.addEventListener('load', () => {
    setTimeout(() => {
        const loader = document.getElementById('page-loader');
        if (loader) {
            loader.classList.add('gone');
            setTimeout(() => loader.remove(), 600);
        }
    }, 400);
});

// Flash message close buttons & auto-dismiss
document.querySelectorAll('.flash').forEach(flash => {
    // Auto-dismiss after 4 seconds
    setTimeout(() => {
        if (document.body.contains(flash)) {
            flash.classList.add('flash-dismissing');
            setTimeout(() => flash.remove(), 300);
        }
    }, 4000);
    
    const btn = flash.querySelector('.flash-close');
    if (btn) {
        btn.addEventListener('click', () => {
            flash.classList.add('flash-dismissing');
            setTimeout(() => flash.remove(), 300);
        });
    }
});

// Global theme toggle function
function toggleTheme() {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    if (isLight) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
    }
    // Dispatch event for other scripts to update
    window.dispatchEvent(new Event('theme_changed'));
    
    // If the toggle element exists, update it visually (mostly for settings page)
    const toggle = document.querySelector('[data-setting="dark_mode"]');
    if (toggle) {
        if (!isLight) toggle.classList.add('on');
        else toggle.classList.remove('on');
    }
    
    // Update simple dark mode buttons dynamically
    document.querySelectorAll('.dark-mode-btn').forEach(btn => {
        btn.textContent = !isLight ? '🌙 Dark Mode' : '☀️ Light Mode';
    });
}

// ==========================================
// Password Reveal / Visibility Toggle System
// ==========================================
const PASSWORD_EYE_ICON = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-eye"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
const PASSWORD_EYE_OFF_ICON = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-eye-off"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;

function togglePasswordVisibility(input, btn) {
    if (!input || !btn) return;
    const isRevealed = input.type === 'text';
    input.type = isRevealed ? 'password' : 'text';
    btn.innerHTML = isRevealed ? PASSWORD_EYE_ICON : PASSWORD_EYE_OFF_ICON;
    btn.setAttribute('aria-label', isRevealed ? 'Show password' : 'Hide password');
    btn.setAttribute('title', isRevealed ? 'Show password' : 'Hide password');
    btn.classList.toggle('active', !isRevealed);
    
    // Retain focus on input
    input.focus();
    try {
        const valLen = input.value.length;
        input.setSelectionRange(valLen, valLen);
    } catch (e) {
        // Ignored if browser does not support setSelectionRange
    }
}

// Global click delegation for all password toggle buttons
document.addEventListener('click', (e) => {
    const btn = e.target.closest('.toggle-password-btn');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    
    const wrapper = btn.closest('.password-wrapper');
    const input = wrapper ? wrapper.querySelector('input') : btn.parentElement.querySelector('input');
    if (input) {
        togglePasswordVisibility(input, btn);
    }
});

// Auto-enhance any password inputs across all views/modals
function initPasswordToggles() {
    document.querySelectorAll('input[type="password"]').forEach(input => {
        // Skip if already wrapped or has dedicated toggle (e.g. login.html)
        if (input.closest('.password-wrapper') || 
            input.parentElement.querySelector('#toggle-password') || 
            input.parentElement.querySelector('.toggle-password-btn')) {
            return;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'password-wrapper';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'toggle-password-btn';
        btn.setAttribute('aria-label', 'Show password');
        btn.setAttribute('title', 'Show password');
        btn.innerHTML = PASSWORD_EYE_ICON;
        wrapper.appendChild(btn);
    });
}

// Initialize on DOM load and when dynamic modals or elements might appear
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPasswordToggles);
} else {
    initPasswordToggles();
}
window.addEventListener('load', initPasswordToggles);


// ==========================================
// Interactive Image Adjustment & Cropper Engine
// ==========================================
let cropImage = null;
let cropImageSrc = null;
let cropZoom = 1.0;
let cropRotation = 0;
let cropPanX = 0;
let cropPanY = 0;
let cropIsDragging = false;
let cropDragStartX = 0;
let cropDragStartY = 0;
let currentAdjustTarget = null;
let originalFilesMap = new WeakMap();

function openImageAdjusterForInput(fileInput, autoSubmitForm, previewId, nameId, adjustBtnId) {
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) return;
    const file = fileInput.files[0];
    
    // Save original file for re-adjusting
    originalFilesMap.set(fileInput, file);

    currentAdjustTarget = {
        input: fileInput,
        autoSubmitForm: autoSubmitForm || null,
        previewId: previewId || null,
        nameId: nameId || null,
        adjustBtnId: adjustBtnId || null
    };

    const reader = new FileReader();
    reader.onload = function(e) {
        loadImageToAdjuster(e.target.result);
    };
    reader.readAsDataURL(file);
}

function reopenAdjuster(fileInputId, autoSubmitForm, previewId, nameId, adjustBtnId) {
    const input = document.getElementById(fileInputId);
    if (!input) return;
    const orig = originalFilesMap.get(input) || (input.files && input.files[0]);
    if (!orig) return;

    currentAdjustTarget = {
        input: input,
        autoSubmitForm: autoSubmitForm || null,
        previewId: previewId || null,
        nameId: nameId || null,
        adjustBtnId: adjustBtnId || null
    };

    const reader = new FileReader();
    reader.onload = function(e) {
        loadImageToAdjuster(e.target.result);
    };
    reader.readAsDataURL(orig);
}

function loadImageToAdjuster(dataUrl) {
    cropImage = new Image();
    cropImage.onload = function() {
        cropZoom = 1.0;
        cropRotation = 0;
        cropPanX = 0;
        cropPanY = 0;
        const slider = document.getElementById('cropZoomSlider');
        if (slider) slider.value = 1.0;

        const modal = document.getElementById('imageAdjustModal');
        if (modal) modal.classList.add('show');
        renderCrop();
    };
    cropImage.src = dataUrl;
}

function closeImageAdjustModal() {
    const modal = document.getElementById('imageAdjustModal');
    if (modal) modal.classList.remove('show');
}

function onCropZoomInput(val) {
    cropZoom = parseFloat(val) || 1.0;
    renderCrop();
}

function stepCropZoom(delta) {
    const slider = document.getElementById('cropZoomSlider');
    if (!slider) return;
    let next = Math.max(1.0, Math.min(3.5, parseFloat(slider.value) + delta));
    slider.value = next.toFixed(2);
    cropZoom = next;
    renderCrop();
}

function rotateCropImage(deg) {
    cropRotation = (cropRotation + deg + 360) % 360;
    renderCrop();
}

function resetCropImage() {
    cropZoom = 1.0;
    cropRotation = 0;
    cropPanX = 0;
    cropPanY = 0;
    const slider = document.getElementById('cropZoomSlider');
    if (slider) slider.value = 1.0;
    renderCrop();
}

function renderCrop() {
    const canvas = document.getElementById('cropCanvas');
    if (!canvas || !cropImage) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;

    ctx.clearRect(0, 0, W, H);

    // 1. Draw transformed image centered at (W/2, H/2)
    ctx.save();
    ctx.translate(W / 2, H / 2);
    ctx.translate(cropPanX, cropPanY);
    ctx.rotate((cropRotation * Math.PI) / 180);

    const isSwapped = cropRotation === 90 || cropRotation === 270;
    const effW = isSwapped ? cropImage.height : cropImage.width;
    const effH = isSwapped ? cropImage.width : cropImage.height;
    const baseScale = 240 / Math.min(effW, effH);
    const scale = baseScale * cropZoom;
    ctx.scale(scale, scale);

    ctx.drawImage(cropImage, -cropImage.width / 2, -cropImage.height / 2);
    ctx.restore();

    // 2. Draw circular crop overlay (dark mask with clear circular aperture)
    ctx.save();
    ctx.fillStyle = 'rgba(10, 10, 15, 0.75)';
    ctx.beginPath();
    ctx.rect(0, 0, W, H);
    ctx.arc(W / 2, H / 2, 120, 0, Math.PI * 2, true);
    ctx.fill();

    // 3. Circle dashed guideline border
    ctx.beginPath();
    ctx.arc(W / 2, H / 2, 120, 0, Math.PI * 2);
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 4]);
    ctx.stroke();

    // 4. Subtle center target
    ctx.beginPath();
    ctx.moveTo(W / 2 - 8, H / 2); ctx.lineTo(W / 2 + 8, H / 2);
    ctx.moveTo(W / 2, H / 2 - 8); ctx.lineTo(W / 2, H / 2 + 8);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.lineWidth = 1;
    ctx.setLineDash([]);
    ctx.stroke();

    ctx.restore();
}

function applyCroppedImage() {
    if (!cropImage || !currentAdjustTarget) return;

    const out = document.createElement('canvas');
    out.width = 400;
    out.height = 400;
    const ctx = out.getContext('2d');

    ctx.translate(200, 200);
    const M = 400 / 240;
    ctx.translate(cropPanX * M, cropPanY * M);
    ctx.rotate((cropRotation * Math.PI) / 180);

    const isSwapped = cropRotation === 90 || cropRotation === 270;
    const effW = isSwapped ? cropImage.height : cropImage.width;
    const effH = isSwapped ? cropImage.width : cropImage.height;
    const baseScale = 240 / Math.min(effW, effH);
    const scale = baseScale * cropZoom * M;
    ctx.scale(scale, scale);

    ctx.drawImage(cropImage, -cropImage.width / 2, -cropImage.height / 2);

    out.toBlob((blob) => {
        if (!blob) return;
        const targetInput = currentAdjustTarget.input;
        const origFile = originalFilesMap.get(targetInput) || (targetInput.files && targetInput.files[0]);
        const fileName = origFile ? origFile.name : 'avatar.jpg';

        try {
            const croppedFile = new File([blob], fileName, { type: 'image/jpeg', lastModified: Date.now() });
            const dt = new DataTransfer();
            dt.items.add(croppedFile);
            targetInput.files = dt.files;
        } catch (e) {
            console.warn("Could not set files via DataTransfer:", e);
        }

        const dataUrl = out.toDataURL('image/jpeg', 0.92);

        // Update preview image
        if (currentAdjustTarget.previewId) {
            const pImg = document.getElementById(currentAdjustTarget.previewId);
            if (pImg) pImg.src = dataUrl;
        }

        // Update filename text
        if (currentAdjustTarget.nameId) {
            const nEl = document.getElementById(currentAdjustTarget.nameId);
            if (nEl) nEl.textContent = '✓ Adjusted: ' + fileName;
        }

        // Show adjust button
        if (currentAdjustTarget.adjustBtnId) {
            const aBtn = document.getElementById(currentAdjustTarget.adjustBtnId);
            if (aBtn) aBtn.style.display = 'inline-flex';
        }

        const autoForm = currentAdjustTarget.autoSubmitForm;
        closeImageAdjustModal();

        if (autoForm) {
            autoForm.submit();
        }
    }, 'image/jpeg', 0.92);
}

// Setup Canvas Dragging & Wheel events
function initCropCanvasEvents() {
    const wrapper = document.getElementById('cropCanvasWrapper');
    if (!wrapper) return;

    wrapper.addEventListener('mousedown', (e) => {
        cropIsDragging = true;
        cropDragStartX = e.clientX;
        cropDragStartY = e.clientY;
        wrapper.style.cursor = 'grabbing';
    });

    window.addEventListener('mousemove', (e) => {
        if (!cropIsDragging) return;
        const dx = e.clientX - cropDragStartX;
        const dy = e.clientY - cropDragStartY;
        cropDragStartX = e.clientX;
        cropDragStartY = e.clientY;
        cropPanX += dx;
        cropPanY += dy;
        renderCrop();
    });

    window.addEventListener('mouseup', () => {
        if (cropIsDragging) {
            cropIsDragging = false;
            if (wrapper) wrapper.style.cursor = 'grab';
        }
    });

    // Touch support for mobile/tablets
    wrapper.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
            cropIsDragging = true;
            cropDragStartX = e.touches[0].clientX;
            cropDragStartY = e.touches[0].clientY;
        }
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
        if (!cropIsDragging || e.touches.length !== 1) return;
        const dx = e.touches[0].clientX - cropDragStartX;
        const dy = e.touches[0].clientY - cropDragStartY;
        cropDragStartX = e.touches[0].clientX;
        cropDragStartY = e.touches[0].clientY;
        cropPanX += dx;
        cropPanY += dy;
        renderCrop();
    }, { passive: true });

    window.addEventListener('touchend', () => {
        cropIsDragging = false;
    });

    // Mouse wheel zoom
    wrapper.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 0.08 : -0.08;
        stepCropZoom(delta);
    }, { passive: false });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCropCanvasEvents);
} else {
    initCropCanvasEvents();
}
