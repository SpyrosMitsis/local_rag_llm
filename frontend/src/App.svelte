<script>
    import FileUpload from './lib/FileUpload.svelte';
    import Chatbot from './lib/Chatbot.svelte';
    import PdfFilePicker from './lib/PdfFilePicker.svelte';
    
    let messages = [];
    let pdfPickerComponent;

    function handleFilesUploaded() {
        if (pdfPickerComponent) {
            pdfPickerComponent.refresh();
        }
    }
</script>

<div class="page-container">
    <div class="sidebar">
        <FileUpload on:filesuploaded={handleFilesUploaded} />
        <PdfFilePicker bind:this={pdfPickerComponent} />
    </div>
    <div class="main-content">
        <Chatbot bind:messages />
    </div>
</div>

<style>
    .page-container {
        display: flex;
        gap: 1rem;
        height: 100vh;
    }

    .sidebar {
        margin-top: 1rem;
        margin-left: 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        height: fit-content;
    }

    .main-content {
        padding: 1rem;
        padding-right: 2rem;
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
</style>
