<script>
    import { onMount, onDestroy } from "svelte";

    let pdfs = $state([]);
    let hasPdfs = $derived(pdfs.length > 0);

    const API_URL = "http://localhost:8000";
    let error = $state(null);
    let loading =$state(true);
    let pollingInterval;
    let deletingPdf =$state(null);
    let isDeleting = $state(false);

    async function fetchPdfs() {
        try {
            const response = await fetch(`${API_URL}/pdfs`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            pdfs = data.pdfs;
            error = null;
        } catch (err) {
            console.error("Error fetching PDFs:", err);
            error = err.message;
        } finally {
            loading = false;
        }
    }

    async function refreshList() {
        loading = true;
        await fetchPdfs();
    }

    // Export the refresh function to make it available to parent components
    export const refresh = refreshList;

    onMount(() => {
        fetchPdfs();
        pollingInterval = setInterval(fetchPdfs, 5000);
    });

    onDestroy(() => {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
    });

    function openPdf(pdfName) {
        window.open(`${API_URL}/pdf/${pdfName}`, "_blank");
    }

    async function deletePdf(pdfName) {
        try {
            // Set the deleting state and prevent any other deletions while in progress
            deletingPdf = pdfName;
            isDeleting = true;

            const response = await fetch(
                `${API_URL}/delete?pdf_name=${encodeURIComponent(pdfName)}`,
                {
                    method: "DELETE",
                    headers: {
                        Accept: "application/json",
                    },
                },
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status ${response.status}`);
            }

            console.log(`${pdfName} deleted successfully`);
        } catch (err) {
            console.error("Couldn't delete PDF", err);
        } finally {
            isDeleting = false;
            deletingPdf = null;
        }
    }
</script>

<div class="viewer-card">
    <h2>PDF Files</h2>
    <div class="pdf-list">
        {#if loading}
            <div class="empty-state">Loading PDFs...</div>
        {:else if error}
            <div class="empty-state error">Error: {error}</div>
        {:else if !hasPdfs}
            <div class="empty-state">No PDFs available</div>
        {:else}
            <ul>
                {#each pdfs as pdf}
                    <li class="pdf-item" onclick={() => openPdf(pdf)}>
                        <div class="pdf-icon">
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                stroke-width="2"
                            >
                                <path
                                    d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
                                />
                                <path d="M14 2v6h6" />
                                <path d="M16 13H8" />
                                <path d="M16 17H8" />
                                <path d="M10 9H8" />
                            </svg>
                        </div>
                        <div class="pdf-info">
                            <span class="filename" title={pdf}>{pdf}</span>
                            <div class="button-container">
                                <button
                                    class="delete-button"
                                    onclick={(event) => {
                                        event.stopPropagation(); // Prevent openPdf from being triggered
                                        deletePdf(pdf);
                                        refreshList();
                                    }}
                                    disabled={isDeleting && deletingPdf === pdf}
                                >
                                    {isDeleting && deletingPdf === pdf
                                        ? "Deleting..."
                                        : "Delete"}
                                </button>
                            </div>
                        </div>
                    </li>
                {/each}
            </ul>
        {/if}
    </div>
</div>

<style>
    .viewer-card {
        width: 18rem;
        background-color: #222;
        border-radius: 8px;
        padding: 1rem;
        color: #ddd;
        margin-top: 1rem;
        display: flex;
        flex-direction: column;
        overflow: hidden; /* Ensure nothing escapes the card */
    }

    h2 {
        margin: 0 0 1rem 0;
        color: #ddd;
    }

    .pdf-list {
        flex-grow: 1;
        overflow-y: auto;
        overflow-x: auto;
        height: 50dvh;
    }

    /* Webkit-based browsers */
    .pdf-list::-webkit-scrollbar {
        width: 8px; /* Explicit width instead of Tailwind class */
    }

    .pdf-list::-webkit-scrollbar-track {
        background-color: #1a1a1a; /* Explicit color instead of Tailwind class */
        border-radius: 9999px;
    }

    .pdf-list::-webkit-scrollbar-thumb {
        background-color: #4a4a4a; /* Explicit color instead of Tailwind class */
        border-radius: 9999px;
    }

    .pdf-list::-webkit-scrollbar-thumb:hover {
        background-color: #666; /* Explicit color instead of Tailwind class */
    }

    /* Firefox */
    .pdf-list {
        scrollbar-width: thin;
        scrollbar-color: #4a4a4a #1a1a1a;
    }

    ul {
        list-style: none;
        padding: 0;
        margin: 0;
        width: 100%;
    }
    .pdf-item {
        display: flex;
        align-items: center; /* Align items vertically */
        justify-content: space-between; /* Space between icon and button */
        background-color: #333;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        transition: background-color 0.2s;
        cursor: pointer;
        position: relative; /* Enable absolute positioning for child elements */
        overflow: hidden;
        min-width: 0;
    }

    .pdf-item:hover {
        background-color: #444;
    }

    .pdf-icon {
        width: 20px;
        height: 20px;
        margin-right: 0.75rem;
        color: #ddd;
        flex-shrink: 0;
    }

    .pdf-info {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .filename {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 0.9rem;
        color: #ddd;
    }
    .button-container {
        position: absolute; /* Position relative to the parent (.pdf-item) */
        top: 50%; /* Center vertically */
        right: 1rem; /* Anchor to the right */
        transform: translateY(-50%); /* Adjust for vertical centering */
        opacity: 0; /* Initially hidden */
        transition: opacity 0.2s;
    }

    .pdf-item:hover .button-container {
        opacity: 1;
    }
    .pdf-name {
        display: block;
        color: #ddd;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 0.9rem;
    }

    .delete-button {
        background-color: #4d2a2a;
        border: none;
        padding: 0.35rem 0.75rem;
        border-radius: 4px;
        color: #ff9090;
        cursor: pointer;
        transition: background-color 0.2s;
        flex-shrink: 0;
        font-size: 0.85rem;
    }

    .delete-button:hover {
        background-color: #662b2b;
    }

    .empty-state {
        text-align: center;
        padding: 1rem;
        background-color: #333;
        border-radius: 8px;
        color: #888;
        font-size: 0.9rem;
    }
</style>
