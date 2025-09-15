/**
 * MarkdownUtils - Shared markdown rendering utilities
 */
class MarkdownUtils {
    constructor() {
        this.initializeMarked();
        this.initializeHighlight();
    }
    
    initializeMarked() {
        // Configure marked for better rendering
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                highlight: (code, lang) => {
                    if (lang && hljs.getLanguage(lang)) {
                        try {
                            return hljs.highlight(code, { language: lang }).value;
                        } catch (e) {
                            console.warn('Highlight.js failed for language:', lang, e);
                        }
                    }
                    try {
                        return hljs.highlightAuto(code).value;
                    } catch (e) {
                        return code; // Fallback to plain text
                    }
                },
                langPrefix: 'hljs language-',
                breaks: true,
                gfm: true,
                tables: true,
                sanitize: false // We'll use DOMPurify instead
            });
            
            console.log('[MarkdownUtils] Marked.js configured');
        } else {
            console.warn('[MarkdownUtils] Marked.js not found');
        }
    }
    
    initializeHighlight() {
        // Configure highlight.js
        if (typeof hljs !== 'undefined') {
            hljs.configure({
                languages: ['python', 'javascript', 'html', 'css', 'json', 'sql', 'bash', 'yaml', 'xml', 'markdown'],
                classPrefix: 'hljs-',
                ignoreUnescapedHTML: true
            });
            console.log('[MarkdownUtils] Highlight.js configured');
        } else {
            console.warn('[MarkdownUtils] Highlight.js not found');
        }
    }
    
    /**
     * Render markdown text to HTML with syntax highlighting and XSS protection
     * @param {string} text - Raw markdown text
     * @param {boolean} inline - Whether to render as inline (no block elements)
     * @returns {string} - Sanitized HTML
     */
    renderMarkdown(text, inline = false) {
        if (!text || typeof text !== 'string') {
            return '';
        }
        
        try {
            // Handle inline rendering
            if (inline) {
                return this.renderInlineMarkdown(text);
            }
            
            // Process markdown with marked.js
            let html = '';
            if (typeof marked !== 'undefined') {
                html = marked.parse(text);
            } else {
                // Fallback to basic formatting if marked.js is not available
                html = this.basicMarkdownFallback(text);
            }
            
            // Sanitize HTML to prevent XSS attacks
            if (typeof DOMPurify !== 'undefined') {
                html = DOMPurify.sanitize(html, {
                    ALLOWED_TAGS: [
                        'p', 'br', 'strong', 'em', 'code', 'pre', 'blockquote',
                        'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                        'table', 'thead', 'tbody', 'tr', 'th', 'td',
                        'a', 'img', 'hr', 'div', 'span'
                    ],
                    ALLOWED_ATTR: [
                        'href', 'target', 'rel', 'src', 'alt', 'title', 'class',
                        'id', 'data-*'
                    ],
                    ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i
                });
            }
            
            return html;
            
        } catch (error) {
            console.error('[MarkdownUtils] Error rendering markdown:', error);
            return this.escapeHtml(text); // Fallback to escaped plain text
        }
    }
    
    /**
     * Render inline markdown (no block elements)
     * @param {string} text - Raw markdown text
     * @returns {string} - Sanitized HTML
     */
    renderInlineMarkdown(text) {
        try {
            // Use marked's inline lexer if available
            if (typeof marked !== 'undefined' && marked.parseInline) {
                return marked.parseInline(text);
            }
            
            // Fallback to basic inline formatting
            return text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code class="inline-code">$1</code>')
                .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
                
        } catch (error) {
            console.error('[MarkdownUtils] Error rendering inline markdown:', error);
            return this.escapeHtml(text);
        }
    }
    
    /**
     * Basic markdown fallback when marked.js is not available
     * @param {string} text - Raw markdown text
     * @returns {string} - Basic HTML
     */
    basicMarkdownFallback(text) {
        return text
            // Headers
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            // Bold and italic
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Code blocks
            .replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, lang, code) => {
                const langClass = lang ? ` class="language-${lang}"` : '';
                return `<div class="code-block"><pre><code${langClass}>${this.escapeHtml(code.trim())}</code></pre></div>`;
            })
            // Inline code
            .replace(/`(.*?)`/g, '<code class="inline-code">$1</code>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
            // Line breaks
            .replace(/\n/g, '<br>')
            // Lists (basic)
            .replace(/^\* (.+)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    }
    
    /**
     * Escape HTML characters
     * @param {string} text - Text to escape
     * @returns {string} - Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Apply syntax highlighting to existing code blocks
     * @param {HTMLElement} container - Container element to process
     */
    highlightCodeBlocks(container) {
        if (typeof hljs !== 'undefined') {
            const codeBlocks = container.querySelectorAll('pre code, code.hljs');
            codeBlocks.forEach(block => {
                if (!block.classList.contains('hljs')) {
                    hljs.highlightElement(block);
                }
            });
        }
    }
    
    /**
     * Create a copy-to-clipboard button for code blocks
     * @param {HTMLElement} codeBlock - Code block element
     */
    addCopyButton(codeBlock) {
        if (codeBlock.querySelector('.copy-button')) {
            return; // Button already exists
        }
        
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button btn btn-sm btn-outline-secondary';
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        copyButton.title = 'Copy code';
        
        copyButton.addEventListener('click', () => {
            const code = codeBlock.textContent;
            navigator.clipboard.writeText(code).then(() => {
                copyButton.innerHTML = '<i class="fas fa-check text-success"></i>';
                setTimeout(() => {
                    copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            }).catch(() => {
                copyButton.innerHTML = '<i class="fas fa-times text-danger"></i>';
                setTimeout(() => {
                    copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            });
        });
        
        // Wrap code block if not already wrapped
        if (!codeBlock.parentNode.classList.contains('code-block-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-wrapper position-relative';
            codeBlock.parentNode.insertBefore(wrapper, codeBlock);
            wrapper.appendChild(codeBlock);
            wrapper.appendChild(copyButton);
        }
    }
    
    /**
     * Process a message element to add markdown rendering and enhancements
     * @param {HTMLElement} element - Element containing the message
     */
    processMessageElement(element) {
        // Highlight code blocks
        this.highlightCodeBlocks(element);
        
        // Add copy buttons to code blocks
        const codeBlocks = element.querySelectorAll('pre code');
        codeBlocks.forEach(block => {
            this.addCopyButton(block);
        });
        
        // Make external links open in new tab
        const links = element.querySelectorAll('a[href^="http"]');
        links.forEach(link => {
            if (!link.getAttribute('target')) {
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener noreferrer');
            }
        });
    }
}

// Create global instance
window.markdownUtils = new MarkdownUtils();

// Export for use in other modules
window.MarkdownUtils = MarkdownUtils;
