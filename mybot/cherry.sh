#!/bin/bash

# Visual Cherry-Pick Tool
# Selector gráfico e interactivo para cherry-pick de commits
# Uso: ./cherry-pick-tool.sh

set -e

# Colores y estilos
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
UNDERLINE='\033[4m'
NC='\033[0m'

# Variables globales
SOURCE_BRANCH=""
TARGET_BRANCH=""
COMMITS=()
SELECTED_COMMITS=()
COMMIT_DETAILS=()

# Funciones de UI
print_header() {
    clear
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║                ${WHITE}🍒 CHERRY-PICK TOOL 🍒${CYAN}                ║${NC}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Verificar que estamos in un repo Git
check_git_repo() {
    if [[ ! -d .git ]]; then
        log_error "No estás en un repositorio Git"
        exit 1
    fi
}

# Obtener lista de ramas
get_branches() {
    git branch -a | grep -v "^*" | sed 's/^[[:space:]]*//' | sed 's/^remotes\///' | sort | uniq
}

# Seleccionar rama fuente
select_source_branch() {
    print_header
    echo -e "${BOLD}${WHITE}PASO 1: Seleccionar rama FUENTE${NC}"
    echo -e "${DIM}(De donde quieres tomar los commits)${NC}"
    echo ""
    
    local branches=($(get_branches))
    local current_branch=$(git branch --show-current)
    
    echo -e "${CYAN}Ramas disponibles:${NC}"
    echo ""
    
    for i in "${!branches[@]}"; do
        local branch="${branches[$i]}"
        local prefix="  "
        local suffix=""
        
        if [[ "$branch" == "$current_branch" ]]; then
            prefix="${GREEN}► "
            suffix=" ${DIM}(actual)${NC}"
        fi
        
        printf "${prefix}${YELLOW}%2d.${NC} %s%s\n" $((i+1)) "$branch" "$suffix"
    done
    
    echo ""
    read -p "Selecciona la rama fuente (número): " source_choice
    
    if [[ $source_choice =~ ^[0-9]+$ ]] && [[ $source_choice -ge 1 ]] && [[ $source_choice -le ${#branches[@]} ]]; then
        SOURCE_BRANCH="${branches[$((source_choice-1))]}"
        log_success "Rama fuente seleccionada: $SOURCE_BRANCH"
    else
        log_error "Selección inválida"
        exit 1
    fi
    
    sleep 1
}

# Seleccionar rama destino
select_target_branch() {
    print_header
    echo -e "${BOLD}${WHITE}PASO 2: Seleccionar rama DESTINO${NC}"
    echo -e "${DIM}(Donde quieres aplicar los commits)${NC}"
    echo ""
    echo -e "${GREEN}Rama fuente: ${WHITE}$SOURCE_BRANCH${NC}"
    echo ""
    
    local branches=($(get_branches))
    local current_branch=$(git branch --show-current)
    
    echo -e "${CYAN}Ramas disponibles:${NC}"
    echo ""
    
    for i in "${!branches[@]}"; do
        local branch="${branches[$i]}"
        local prefix="  "
        local suffix=""
        
        if [[ "$branch" == "$current_branch" ]]; then
            prefix="${GREEN}► "
            suffix=" ${DIM}(actual)${NC}"
        fi
        
        if [[ "$branch" == "$SOURCE_BRANCH" ]]; then
            prefix="${DIM}  "
            suffix=" ${DIM}(fuente - no seleccionable)${NC}"
            continue
        fi
        
        printf "${prefix}${YELLOW}%2d.${NC} %s%s\n" $((i+1)) "$branch" "$suffix"
    done
    
    echo ""
    read -p "Selecciona la rama destino (número): " target_choice
    
    if [[ $target_choice =~ ^[0-9]+$ ]] && [[ $target_choice -ge 1 ]] && [[ $target_choice -le ${#branches[@]} ]]; then
        local selected_branch="${branches[$((target_choice-1))]}"
        if [[ "$selected_branch" != "$SOURCE_BRANCH" ]]; then
            TARGET_BRANCH="$selected_branch"
            log_success "Rama destino seleccionada: $TARGET_BRANCH"
        else
            log_error "No puedes usar la misma rama como fuente y destino"
            exit 1
        fi
    else
        log_error "Selección inválida"
        exit 1
    fi
    
    sleep 1
}

# Obtener commits de la rama fuente
get_commits() {
    log_info "Obteniendo commits de $SOURCE_BRANCH..."
    
    # Obtener commits que están en SOURCE pero no en TARGET
    local commit_range="$TARGET_BRANCH..$SOURCE_BRANCH"
    
    # Leer commits en arrays
    readarray -t COMMITS < <(git rev-list --reverse "$commit_range")
    
    if [[ ${#COMMITS[@]} -eq 0 ]]; then
        log_warning "No hay commits únicos en $SOURCE_BRANCH que no estén en $TARGET_BRANCH"
        exit 0
    fi
    
    # Obtener detalles de cada commit
    COMMIT_DETAILS=()
    for commit in "${COMMITS[@]}"; do
        local short_hash=$(git rev-parse --short "$commit")
        local message=$(git log --format="%s" -n 1 "$commit")
        local author=$(git log --format="%an" -n 1 "$commit")
        local date=$(git log --format="%ar" -n 1 "$commit")
        local files_changed=$(git diff-tree --no-commit-id --name-only -r "$commit" | wc -l)
        
        COMMIT_DETAILS+=("$short_hash|$message|$author|$date|$files_changed")
    done
}

# Mostrar commit con detalles
show_commit_details() {
    local commit=$1
    local short_hash=$(git rev-parse --short "$commit")
    
    echo -e "${BOLD}${WHITE}Detalles del commit $short_hash:${NC}"
    echo ""
    
    # Información básica
    echo -e "${CYAN}📝 Mensaje:${NC} $(git log --format='%s' -n 1 "$commit")"
    echo -e "${CYAN}👤 Autor:${NC} $(git log --format='%an <%ae>' -n 1 "$commit")"
    echo -e "${CYAN}📅 Fecha:${NC} $(git log --format='%cd' --date=format:'%Y-%m-%d %H:%M' -n 1 "$commit")"
    echo -e "${CYAN}🕐 Hace:${NC} $(git log --format='%ar' -n 1 "$commit")"
    echo ""
    
    # Estadísticas
    local stats=$(git show --stat "$commit" | tail -n 1)
    echo -e "${CYAN}📊 Cambios:${NC} $stats"
    echo ""
    
    # Archivos modificados
    echo -e "${CYAN}📁 Archivos modificados:${NC}"
    git diff-tree --no-commit-id --name-status -r "$commit" | while read status file; do
        case $status in
            A) echo -e "  ${GREEN}+ $file${NC}" ;;
            M) echo -e "  ${YELLOW}~ $file${NC}" ;;
            D) echo -e "  ${RED}- $file${NC}" ;;
            *) echo -e "  ${BLUE}? $file${NC}" ;;
        esac
    done
    echo ""
    
    # Diff resumido
    echo -e "${CYAN}📋 Cambios (primeras 10 líneas):${NC}"
    git show --no-merges --format="" "$commit" | head -10 | sed 's/^/  /'
    echo ""
}

# Selector visual de commits
select_commits() {
    while true; do
        print_header
        echo -e "${BOLD}${WHITE}PASO 3: Seleccionar commits para cherry-pick${NC}"
        echo -e "${DIM}Commits únicos en ${GREEN}$SOURCE_BRANCH${DIM} que no están en ${BLUE}$TARGET_BRANCH${DIM}${NC}"
        echo ""
        echo -e "${GREEN}Fuente: ${WHITE}$SOURCE_BRANCH${NC}"
        echo -e "${BLUE}Destino: ${WHITE}$TARGET_BRANCH${NC}"
        echo -e "${PURPLE}Seleccionados: ${WHITE}${#SELECTED_COMMITS[@]} commits${NC}"
        echo ""
        
        # Mostrar commits con formato visual
        echo -e "${CYAN}╭─────┬──────────┬──────────────────────────────────────────┬─────────────────┬───────╮${NC}"
        echo -e "${CYAN}│ Sel │   Hash   │                 Mensaje                  │     Autor       │ Arch. │${NC}"
        echo -e "${CYAN}├─────┼──────────┼──────────────────────────────────────────┼─────────────────┼───────┤${NC}"
        
        for i in "${!COMMITS[@]}"; do
            local commit="${COMMITS[$i]}"
            local details="${COMMIT_DETAILS[$i]}"
            IFS='|' read -r short_hash message author date files_changed <<< "$details"
            
            # Truncar mensaje si es muy largo
            if [[ ${#message} -gt 38 ]]; then
                message="${message:0:35}..."
            fi
            
            # Truncar autor si es muy largo
            if [[ ${#author} -gt 13 ]]; then
                author="${author:0:10}..."
            fi
            
            # Verificar si está seleccionado
            local selected=" "
            local color=$WHITE
            if [[ " ${SELECTED_COMMITS[*]} " =~ " $commit " ]]; then
                selected="✓"
                color=$GREEN
            fi
            
            printf "${CYAN}│${color} %2s  ${CYAN}│${color} %8s ${CYAN}│${color} %-38s ${CYAN}│${color} %-13s ${CYAN}│${color} %3s   ${CYAN}│${NC}\n" \
                   "$((i+1))" "$short_hash" "$message" "$author" "$files_changed"
        done
        
        echo -e "${CYAN}╰─────┴──────────┴──────────────────────────────────────────┴─────────────────┴───────╯${NC}"
        echo ""
        
        # Mostrar commits seleccionados si hay
        if [[ ${#SELECTED_COMMITS[@]} -gt 0 ]]; then
            echo -e "${GREEN}✅ Commits seleccionados:${NC}"
            for selected in "${SELECTED_COMMITS[@]}"; do
                local short_hash=$(git rev-parse --short "$selected")
                local message=$(git log --format="%s" -n 1 "$selected")
                echo -e "   ${GREEN}$short_hash${NC} $message"
            done
            echo ""
        fi
        
        # Opciones
        echo -e "${WHITE}Opciones:${NC}"
        echo -e "  ${YELLOW}1-${#COMMITS[@]}${NC}  Seleccionar/deseleccionar commit"
        echo -e "  ${YELLOW}v${NC} + número  Ver detalles del commit"
        echo -e "  ${YELLOW}a${NC}          Seleccionar todos"
        echo -e "  ${YELLOW}n${NC}          No seleccionar ninguno"
        echo -e "  ${YELLOW}c${NC}          Continuar con cherry-pick"
        echo -e "  ${YELLOW}q${NC}          Salir"
        echo ""
        
        read -p "Opción: " choice
        
        case $choice in
            [1-9]|[1-9][0-9])
                if [[ $choice -ge 1 ]] && [[ $choice -le ${#COMMITS[@]} ]]; then
                    local commit="${COMMITS[$((choice-1))]}"
                    if [[ " ${SELECTED_COMMITS[*]} " =~ " $commit " ]]; then
                        # Deseleccionar
                        SELECTED_COMMITS=($(printf '%s\n' "${SELECTED_COMMITS[@]}" | grep -v "^$commit$"))
                        log_info "Commit deseleccionado"
                    else
                        # Seleccionar
                        SELECTED_COMMITS+=("$commit")
                        log_success "Commit seleccionado"
                    fi
                    sleep 0.5
                else
                    log_error "Número inválido"
                    sleep 1
                fi
                ;;
            v[1-9]|v[1-9][0-9])
                local num=$(echo "$choice" | sed 's/v//')
                if [[ $num -ge 1 ]] && [[ $num -le ${#COMMITS[@]} ]]; then
                    local commit="${COMMITS[$((num-1))]}"
                    clear
                    show_commit_details "$commit"
                    read -p "Presiona Enter para continuar..."
                else
                    log_error "Número inválido"
                    sleep 1
                fi
                ;;
            a|A)
                SELECTED_COMMITS=("${COMMITS[@]}")
                log_success "Todos los commits seleccionados"
                sleep 1
                ;;
            n|N)
                SELECTED_COMMITS=()
                log_info "Todos los commits deseleccionados"
                sleep 1
                ;;
            c|C)
                if [[ ${#SELECTED_COMMITS[@]} -eq 0 ]]; then
                    log_warning "No has seleccionado ningún commit"
                    sleep 1
                else
                    break
                fi
                ;;
            q|Q)
                log_info "Saliendo..."
                exit 0
                ;;
            *)
                log_error "Opción inválida"
                sleep 1
                ;;
        esac
    done
}

# Confirmar cherry-pick
confirm_cherry_pick() {
    print_header
    echo -e "${BOLD}${WHITE}PASO 4: Confirmar operación${NC}"
    echo ""
    echo -e "${GREEN}Fuente: ${WHITE}$SOURCE_BRANCH${NC}"
    echo -e "${BLUE}Destino: ${WHITE}$TARGET_BRANCH${NC}"
    echo -e "${PURPLE}Commits a aplicar: ${WHITE}${#SELECTED_COMMITS[@]}${NC}"
    echo ""
    
    echo -e "${YELLOW}📋 Commits que se aplicarán:${NC}"
    for commit in "${SELECTED_COMMITS[@]}"; do
        local short_hash=$(git rev-parse --short "$commit")
        local message=$(git log --format="%s" -n 1 "$commit")
        echo -e "  ${GREEN}$short_hash${NC} $message"
    done
    
    echo ""
    log_warning "Esta operación aplicará ${#SELECTED_COMMITS[@]} commits a la rama $TARGET_BRANCH"
    echo ""
    
    read -p "¿Proceder con cherry-pick? (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Operación cancelada"
        exit 0
    fi
}

# Ejecutar cherry-pick
execute_cherry_pick() {
    print_header
    echo -e "${BOLD}${WHITE}PASO 5: Ejecutando cherry-pick${NC}"
    echo ""
    
    # Cambiar a rama destino
    log_info "Cambiando a rama $TARGET_BRANCH..."
    git checkout "$TARGET_BRANCH"
    
    local success_count=0
    local conflict_count=0
    local failed_commits=()
    
    echo ""
    echo -e "${CYAN}Aplicando commits:${NC}"
    
    for i in "${!SELECTED_COMMITS[@]}"; do
        local commit="${SELECTED_COMMITS[$i]}"
        local short_hash=$(git rev-parse --short "$commit")
        local message=$(git log --format="%s" -n 1 "$commit")
        
        printf "${YELLOW}[%d/%d]${NC} Aplicando ${GREEN}%s${NC} %s... " $((i+1)) ${#SELECTED_COMMITS[@]} "$short_hash" "$message"
        
        if git cherry-pick "$commit" >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
            ((success_count++))
        else
            echo -e "${RED}✗${NC}"
            
            # Verificar si es conflicto
            if git status --porcelain | grep -q "^UU\|^AA\|^DD"; then
                echo -e "    ${RED}→ Conflicto detectado${NC}"
                ((conflict_count++))
                
                # Mostrar archivos en conflicto
                echo -e "    ${YELLOW}Archivos en conflicto:${NC}"
                git status --porcelain | grep "^UU\|^AA\|^DD" | sed 's/^/      /'
                
                echo ""
                echo -e "${WHITE}Opciones para resolver conflicto:${NC}"
                echo -e "  ${CYAN}1.${NC} Resolver manualmente y continuar"
                echo -e "  ${CYAN}2.${NC} Saltar este commit"
                echo -e "  ${CYAN}3.${NC} Abortar cherry-pick completo"
                echo ""
                
                while true; do
                    read -p "Opción (1/2/3): " conflict_choice
                    case $conflict_choice in
                        1)
                            echo -e "${YELLOW}Resuelve los conflictos y presiona Enter para continuar...${NC}"
                            read -p ""
                            
                            # Verificar si se resolvieron los conflictos
                            if ! git status --porcelain | grep -q "^UU\|^AA\|^DD"; then
                                git commit --no-edit
                                echo -e "    ${GREEN}→ Conflictos resueltos y commit aplicado${NC}"
                                ((success_count++))
                                break
                            else
                                echo -e "    ${RED}→ Aún hay conflictos sin resolver${NC}"
                            fi
                            ;;
                        2)
                            git cherry-pick --abort
                            echo -e "    ${YELLOW}→ Commit saltado${NC}"
                            failed_commits+=("$commit")
                            break
                            ;;
                        3)
                            git cherry-pick --abort
                            log_error "Cherry-pick abortado por el usuario"
                            exit 1
                            ;;
                        *)
                            echo -e "${RED}Opción inválida${NC}"
                            ;;
                    esac
                done
            else
                failed_commits+=("$commit")
            fi
        fi
    done
    
    # Resumen final
    echo ""
    echo -e "${BOLD}${CYAN}📊 RESUMEN DE CHERRY-PICK${NC}"
    echo -e "${GREEN}✅ Commits aplicados exitosamente: $success_count${NC}"
    if [[ $conflict_count -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Commits con conflictos resueltos: $conflict_count${NC}"
    fi
    if [[ ${#failed_commits[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Commits fallidos: ${#failed_commits[@]}${NC}"
        for failed in "${failed_commits[@]}"; do
            local short_hash=$(git rev-parse --short "$failed")
            local message=$(git log --format="%s" -n 1 "$failed")
            echo -e "   ${RED}$short_hash${NC} $message"
        done
    fi
    
    echo ""
    echo -e "${WHITE}Estado actual de la rama ${BLUE}$TARGET_BRANCH${WHITE}:${NC}"
    git log --oneline -5
    
    echo ""
    log_success "Cherry-pick completado!"
}

# Función principal
main() {
    check_git_repo
    select_source_branch
    select_target_branch
    get_commits
    select_commits
    confirm_cherry_pick
    execute_cherry_pick
    
    echo ""
    echo -e "${BOLD}${GREEN}🎉 ¡Proceso completado exitosamente!${NC}"
    echo ""
    echo -e "${WHITE}Próximos pasos:${NC}"
    echo "• Revisar los commits aplicados"
    echo "• Hacer push si estás satisfecho: git push origin $TARGET_BRANCH"
    echo "• O hacer más cherry-picks si es necesario"
}

# Ejecutar
main "$@"
