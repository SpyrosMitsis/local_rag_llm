<script>
    import { createEventDispatcher } from "svelte";
    import { fade } from 'svelte/transition';
    
    const dispatch = createEventDispatcher();
    let uploadStatus = "";
    let isUploading = false;
    let statusTimeout;
    let showStatus = false;

    function clearStatus() {
        if (statusTimeout) {
            clearTimeout(statusTimeout);
        }
        statusTimeout = setTimeout(() => {
            showStatus = false;
        }, 3000);
    }

    async function handleFileUpload(event) {
        const files = event.target.files;
        if (!files || files.length === 0) return;
        
        isUploading = true;
        uploadStatus = "Uploading...";
        showStatus = true;
        
        const formData = new FormData();
        Array.from(files).forEach((file) => {
            formData.append("files", file);
        });

        try {
            const response = await fetch("http://localhost:8000/uploadFiles", {
                method: "POST",
                body: formData,
            });
            const result = await response.json();
            
            if (response.ok) {
                uploadStatus = `${files.length} file(s) uploaded successfully`;
                clearStatus();
                dispatch("filesuploaded");
            } else {
                uploadStatus = `Upload failed: ${result.error || "Unknown error"}`;
                clearStatus();
            }
        } catch (error) {
            uploadStatus = `Upload failed: ${error.message}`;
            clearStatus();
        } finally {
            isUploading = false;
            event.target.value = "";
        }
    }
</script>

<div class="upload-card">
    <h2>File Upload</h2>
    <div class="upload-area">
        <input
            type="file"
            on:change={handleFileUpload}
            disabled={isUploading}
            id="file-input-single"
            class="file-input"
        />
        <input
            type="file"
            on:change={handleFileUpload}
            disabled={isUploading}
            id="file-input-multiple"
            class="file-input"
            multiple
        />
        <label for="file-input-single" class="file-label">
            {isUploading ? "Uploading..." : "Choose a file"}
        </label>
        {#if showStatus}
            <div
                class="upload-status"
                class:success={uploadStatus.includes("successfully")}
                class:error={uploadStatus.includes("failed")}
                transition:fade={{ duration: 200 }}
            >
                {uploadStatus}
            </div>
        {/if}
    </div>
</div>

<style>
    .upload-card {
        color: #ddd;
        background-color: #222222;
        border-radius: 10px;
    }
    h2 {
        margin: 0.75rem;
    }
    .upload-area {
        margin-top: 1rem;
        padding: 1rem;
    }
    .file-input {
        display: none;
    }
    .file-label:hover {
        background-color: #444;
    }
    .file-label {
        display: block;
        padding: 10px;
        background-color: #333;
        color: #ddd;
        text-align: center;
        border-radius: 8px;
        cursor: pointer;
    }
    .upload-status {
        margin-top: 1rem;
        padding: 0.5rem;
        border-radius: 4px;
    }
    .success {
        background-color: #2a4d2a;
        color: #90ee90;
    }
    .error {
        background-color: #4d2a2a;
        color: #ee9090;
    }
</style>
