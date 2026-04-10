<template>
    <div class="toast" :class="type">
        <span class="icon">{{ icon }}</span>
        <span class="message">{{ message }}</span>
    </div>
</template>

<script>
export default {
    name: 'Toast',
    props: {
        type: {
            type: String,
            default: 'info'
        },
        message: {
            type: String,
            required: true
        }
    },
    computed: {
        icon() {
            const icons = {
                success: '✓',
                error: '✕',
                info: 'ℹ'
            }
            return icons[this.type] || '•'
        }
    }
}
</script>

<style scoped>
.toast {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    padding: 1rem 1.5rem;
    border-radius: 0.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    animation: slideIn 0.3s ease;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    z-index: 9999;
}

.toast.success {
    border-left: 4px solid var(--success);
}

.toast.success .icon {
    color: var(--success);
}

.toast.error {
    border-left: 4px solid var(--error);
}

.toast.error .icon {
    color: var(--error);
}

.icon {
    font-weight: 700;
    font-size: 1.1rem;
}

.message {
    font-size: 0.95rem;
}

@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
</style>
