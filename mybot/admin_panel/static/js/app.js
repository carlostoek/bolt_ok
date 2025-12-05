/**
 * Funciones JavaScript globales para el panel de administración
 */

// Utilidades generales
const utils = {
    /**
     * Realiza una petición fetch con manejo de errores
     */
    async fetchAPI(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Error en la petición');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    /**
     * Muestra un mensaje de notificación toast
     */
    showToast(message, type = 'info') {
        // TODO: Implementar sistema de toast notifications
        console.log(`[${type.toUpperCase()}] ${message}`);
        alert(message); // Temporal
    },
    
    /**
     * Formatea una fecha a string legible
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    /**
     * Debounce function para búsquedas
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Valida formato de fragment key
     */
    isValidFragmentKey(key) {
        const regex = /^[A-Z0-9_-]+$/;
        return regex.test(key);
    },
    
    /**
     * Copia texto al clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copiado al portapapeles', 'success');
        } catch (error) {
            console.error('Error copying to clipboard:', error);
            this.showToast('Error al copiar', 'error');
        }
    },
    
    /**
     * Confirma acción destructiva
     */
    async confirmDelete(itemName) {
        return confirm(`¿Estás seguro de que deseas eliminar "${itemName}"? Esta acción no se puede deshacer.`);
    }
};

// Componentes Alpine.js reutilizables
document.addEventListener('alpine:init', () => {
    
    // Componente para formularios con validación
    Alpine.data('formHandler', (submitUrl) => ({
        loading: false,
        errors: {},
        successMessage: '',
        
        async submit(formData) {
            this.loading = true;
            this.errors = {};
            this.successMessage = '';
            
            try {
                const response = await utils.fetchAPI(submitUrl, {
                    method: 'POST',
                    body: JSON.stringify(formData)
                });
                
                if (response.success) {
                    this.successMessage = response.message || 'Guardado exitosamente';
                    return response.data;
                }
            } catch (error) {
                if (error.field) {
                    this.errors[error.field] = error.message;
                } else {
                    this.errors.general = error.message;
                }
                throw error;
            } finally {
                this.loading = false;
            }
        },
        
        hasError(field) {
            return !!this.errors[field];
        },
        
        getError(field) {
            return this.errors[field] || '';
        }
    }));
    
    // Componente para búsqueda con debounce
    Alpine.data('searchHandler', () => ({
        query: '',
        results: [],
        loading: false,
        
        init() {
            this.debouncedSearch = utils.debounce(this.search.bind(this), 300);
        },
        
        handleInput() {
            this.debouncedSearch();
        },
        
        async search() {
            if (this.query.length < 2) {
                this.results = [];
                return;
            }
            
            this.loading = true;
            
            try {
                // Implementar búsqueda específica por endpoint
                // const data = await utils.fetchAPI(`/api/v1/search?q=${this.query}`);
                // this.results = data.data;
            } catch (error) {
                console.error('Search error:', error);
            } finally {
                this.loading = false;
            }
        }
    }));
    
    // Componente para paginación
    Alpine.data('pagination', (initialPage = 1, perPage = 20) => ({
        currentPage: initialPage,
        perPage: perPage,
        total: 0,
        totalPages: 0,
        
        setTotal(total) {
            this.total = total;
            this.totalPages = Math.ceil(total / this.perPage);
        },
        
        goToPage(page) {
            if (page >= 1 && page <= this.totalPages) {
                this.currentPage = page;
                this.$dispatch('page-changed', { page: this.currentPage });
            }
        },
        
        nextPage() {
            this.goToPage(this.currentPage + 1);
        },
        
        prevPage() {
            this.goToPage(this.currentPage - 1);
        },
        
        hasNext() {
            return this.currentPage < this.totalPages;
        },
        
        hasPrev() {
            return this.currentPage > 1;
        }
    }));
});

// Exportar utils para uso global
window.utils = utils;

// Log de inicialización
console.log('✅ Panel Admin JS loaded');