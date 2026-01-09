/**
 * Main TypeScript file for Natural Language SQL Interface client
 * Handles file uploads and UI updates
 */

const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const uploadZone = document.getElementById('uploadZone') as HTMLDivElement;
const fileInput = document.getElementById('fileInput') as HTMLInputElement;
const messageArea = document.getElementById('messageArea') as HTMLDivElement;
const loader = document.getElementById('loader') as HTMLDivElement;
const tableInfo = document.getElementById('tableInfo') as HTMLDivElement;
const tableName = document.getElementById('tableName') as HTMLDivElement;
const rowCount = document.getElementById('rowCount') as HTMLDivElement;
const columnCount = document.getElementById('columnCount') as HTMLDivElement;
const schemaList = document.getElementById('schemaList') as HTMLDivElement;

/**
 * Display a message to the user
 */
function showMessage(message: string, type: 'success' | 'error'): void {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    messageArea.innerHTML = '';
    messageArea.appendChild(messageDiv);
    messageDiv.style.display = 'block';

    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }
}

/**
 * Show/hide the loader
 */
function setLoading(isLoading: boolean): void {
    loader.style.display = isLoading ? 'block' : 'none';
    uploadZone.style.opacity = isLoading ? '0.5' : '1';
    uploadZone.style.pointerEvents = isLoading ? 'none' : 'auto';
}

/**
 * Update the table information display
 */
function updateTableInfo(data: any): void {
    tableName.textContent = data.table_name || '-';
    rowCount.textContent = data.row_count?.toString() || '-';

    const schema = data.schema || {};
    const columns = Object.keys(schema);
    columnCount.textContent = columns.length.toString();

    // Display schema
    schemaList.innerHTML = '';
    columns.forEach(columnName => {
        const schemaItem = document.createElement('div');
        schemaItem.className = 'schema-item';
        schemaItem.innerHTML = `
            <span class="column-name">${columnName}</span>
            <span class="column-type">${schema[columnName]}</span>
        `;
        schemaList.appendChild(schemaItem);
    });

    tableInfo.style.display = 'block';
}

/**
 * Handle file upload
 */
async function handleFileUpload(file: File): Promise<void> {
    try {
        setLoading(true);
        tableInfo.style.display = 'none';

        // Validate file type
        const validExtensions = ['.csv', '.json', '.jsonl'];
        const fileName = file.name.toLowerCase();
        const isValid = validExtensions.some(ext => fileName.endsWith(ext));

        if (!isValid) {
            showMessage(
                `Invalid file type. Please upload ${validExtensions.join(', ')} files only.`,
                'error'
            );
            setLoading(false);
            return;
        }

        // Create form data
        const formData = new FormData();
        formData.append('file', file);

        // Send to server
        const response = await fetch(`${API_BASE_URL}/api/upload`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showMessage(result.message || 'File uploaded successfully!', 'success');
            updateTableInfo(result);
        } else {
            showMessage(
                result.error || 'Failed to upload file. Please try again.',
                'error'
            );
        }
    } catch (error) {
        console.error('Upload error:', error);
        showMessage(
            'Network error. Please check that the server is running.',
            'error'
        );
    } finally {
        setLoading(false);
    }
}

/**
 * Handle drag and drop events
 */
uploadZone.addEventListener('click', () => {
    fileInput.click();
});

uploadZone.addEventListener('dragover', (e: DragEvent) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e: DragEvent) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');

    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
        handleFileUpload(files[0]);
    }
});

fileInput.addEventListener('change', (e: Event) => {
    const target = e.target as HTMLInputElement;
    const files = target.files;
    if (files && files.length > 0) {
        handleFileUpload(files[0]);
    }
});

// Initialize
console.log('Natural Language SQL Interface client initialized');
console.log(`API Base URL: ${API_BASE_URL}`);
