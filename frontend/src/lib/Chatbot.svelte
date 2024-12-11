<script>
    import { afterUpdate } from "svelte";
    import { marked } from "marked";

    export let messages = [];

    let query = "";
    let chatContainer;

    marked.setOptions({
        breaks: true,
        gfm: true,
    });

    function scrollToBottom() {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    async function handleStreamResponse() {
        messages = [...messages, { text: query, sender: "user" }];
        let result = "";

        const response = await fetch("http://localhost:8000/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query }),
        });

        if (!response.body) {
            console.error("No response body available for streaming");
            return;
        }

        query = "";
        let aiMessage = { text: "", sender: "ai" };
        messages = [...messages, aiMessage];

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let done = false;
        while (!done) {
            const { value, done: doneReading } = await reader.read();
            done = doneReading;
            const chunk = decoder.decode(value);
            result += chunk;

            aiMessage.text = result;
            messages = [...messages.slice(0, -1), aiMessage];
        }
    }

    function renderMarkdown(text) {
        try {
            return marked(text);
        } catch (error) {
            console.error("Error rendering markdown:", error);
            return text;
        }
    }

    afterUpdate(() => {
        scrollToBottom();
    });
</script>

<div class="chat-container" bind:this={chatContainer}>
    {#each messages as { text, sender }}
        <div class="message {sender === 'user' ? 'user-message' : 'ai-message'}">
            <div class="markdown-content">
                {@html renderMarkdown(text)}
            </div>
        </div>
    {/each}
</div>

<div class="input-container">
    <input
        type="text"
        bind:value={query}
        placeholder="Type a message..."
        on:keydown={(e) => e.key === "Enter" && handleStreamResponse()}
    />
    <button disabled={!query} on:click={handleStreamResponse}>Send</button>
</div>

<style>
    .chat-container {
        flex: 1;
        overflow-y: auto;
        background-color: #222;
        color: #ddd;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        display: flex;
        flex-direction: column;
    }

    .input-container {
        display: flex;
        border-radius: 8px;
        gap: 1rem;
        padding: 0.5rem;
        
        input {
            font-size: 20px;
        }
        
    }

    .message {
        max-width: 100%;
        margin-bottom: 10px;
        word-wrap: break-word;
    }

    .user-message {
        background-color: #555;
        color: #fff;
        padding: 10px;
        border-radius: 12px;
        align-self: flex-end;
    }

    .ai-message {
        color: #ddd;
        align-self: flex-start;
        white-space: pre-wrap;
        text-align: left;
    }

    input[type="text"] {
        flex: 1;
        padding: 10px;
        border: 1px solid #555;
        border-radius: 20px;
        background-color: #333;
        color: #ddd;
    }

    button {
        padding: 10px 20px;
        background-color: #555;
        color: #fff;
        border: none;
        border-radius: 20px;
        cursor: pointer;
    }

    button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    :global(.markdown-content) {
        line-height: 1.5;
        overflow-x: auto;
        max-width: 100%;
    }

    :global(.markdown-content p) {
        margin: 0.5em 0;
    }

    :global(.markdown-content code) {
        background-color: #333;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-family: monospace;
    }

    :global(.markdown-content pre) {
        background-color: #333;
        padding: 1em;
        border-radius: 5px;
        overflow-x: auto;
        margin: 0.5rem 0;
    }

    :global(.markdown-content pre code) {
        display: block;
        white-space: pre;
        word-wrap: normal;
    }

    :global(.markdown-content h1, .markdown-content h2, .markdown-content h3) {
        margin: 0.5em 0;
        color: #fff;
    }

    :global(.markdown-content ul, .markdown-content ol) {
        margin: 0.5em 0;
        padding-left: 1.5em;
    }

    :global(.markdown-content img) {
        max-width: 100%;
        height: auto;
    }
</style>
