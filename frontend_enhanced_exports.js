// ==========================================
// AMÉLIORATIONS FRONTEND POUR LES EXPORTS EXCEL
// HotelManager Pro V2 - Ajouts aux fichiers HTML existants
// ==========================================

// ==========================================
// 1. FONCTIONS UTILITAIRES POUR LES EXPORTS
// ==========================================

// Fonction améliorée pour l'export de simulation
const exportSimulationEnhanced = async () => {
    if (!state.simulation) {
        showToast('Réalisez une simulation avant d\'exporter.', 'warning');
        return;
    }

    try {
        showToast('Génération du rapport Excel amélioré...', 'info');
        
        const response = await fetch(`${getApi()}/export/simulation/enhanced`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: state.simulation,
                filename_prefix: `simulation_${state.hotelId}_${Date.now()}`
            }),
        });

        if (!response.ok) throw new Error('Export impossible');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `simulation_enhanced_${state.hotelId}_${Date.now()}.xlsx`;
        link.click();
        window.URL.revokeObjectURL(url);
        
        showToast('Rapport Excel amélioré téléchargé', 'success');
        
        // Log de l'activité
        with Session(engine) as session => {
            log_activity(
                session,
                activity_type="export.completed",
                description="Export simulation amélioré téléchargé",
                hotel_id=state.hotelId,
                details={
                    type: "enhanced_simulation",
                    rows: state.simulation.results?.length || 0,
                }
            );
            session.commit();
        };
        
    } catch (error) {
        showToast(`Erreur export: ${error.message}`, 'error');
    }
};

// Fonction pour l'export de simulation de réservation
const exportReservationSimulation = async () => {
    if (!state.simulation) {
        showToast('Réalisez une simulation avant d\'exporter.', 'warning');
        return;
    }

    try {
        showToast('Génération de la prévision de réservation...', 'info');
        
        const response = await fetch(`${getApi()}/export/reservation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: state.simulation
            }),
        });

        if (!response.ok) throw new Error('Export impossible');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `reservation_prediction_${state.hotelId}_${Date.now()}.xlsx`;
        link.click();
        window.URL.revokeObjectURL(url);
        
        showToast('Prévision de réservation téléchargée', 'success');
        
    } catch (error) {
        showToast(`Erreur export réservation: ${error.message}`, 'error');
    }
};

// Fonction pour l'export des disponibilités
const exportAvailabilityData = async () => {
    if (!state.hotelId) {
        showToast('Chargez un hôtel avant d\'exporter.', 'warning');
        return;
    }

    // Récupérer les dernières disponibilités affichées
    const availabilityResults = document.getElementById('availabilityResults');
    if (availabilityResults.classList.contains('hidden')) {
        showToast('Consultez d\'abord les disponibilités avant d\'exporter.', 'warning');
        return;
    }

    try {
        showToast('Génération du rapport de disponibilités...', 'info');
        
        // Récupérer les données de disponibilité depuis l'API
        const response = await fetch(`${getApi()}/availability`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                hotel_id: state.hotelId,
                start_date: document.getElementById('availabilityStart').value,
                end_date: document.getElementById('availabilityEnd').value,
                room_types: Array.from(document.getElementById('availabilityRooms').selectedOptions).map(option => option.value),
                performed_by: 'frontend-ui'
            }),
        });

        if (!response.ok) throw new Error('Récupération des disponibilités impossible');

        const availabilityData = await response.json();

        const exportResponse = await fetch(`${getApi()}/export/availability`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: availabilityData
            }),
        });

        if (!exportResponse.ok) throw new Error('Export impossible');

        const blob = await exportResponse.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `disponibilites_${state.hotelId}_${Date.now()}.xlsx`;
        link.click();
        window.URL.revokeObjectURL(url);
        
        showToast('Rapport de disponibilités téléchargé', 'success');
        
    } catch (error) {
        showToast(`Erreur export disponibilités: ${error.message}`, 'error');
    }
};

// Fonction pour l'export groupé
const exportBatchReports = async () => {
    if (!state.hotelId) {
        showToast('Chargez un hôtel avant d\'exporter.', 'warning');
        return;
    }

    const exportType = prompt(
        'Quel type d\'export souhaitez-vous générer ?\n' +
        '1. Simulation (rapport détaillé)\n' +
        '2. Prévision de réservation\n' +
        '3. Disponibilités\n\n' +
        'Tapez le numéro de votre choix:'
    );

    if (!exportType || !['1', '2', '3'].includes(exportType)) {
        return; // Annulé ou choix invalide
    }

    try {
        let response, data, endpoint;

        switch(exportType) {
            case '1':
                if (!state.simulation) {
                    showToast('Réalisez une simulation avant d\'exporter.', 'warning');
                    return;
                }
                data = state.simulation;
                endpoint = '/export/simulation/enhanced';
                break;
            case '2':
                if (!state.simulation) {
                    showToast('Réalisez une simulation avant d\'exporter.', 'warning');
                    return;
                }
                data = state.simulation;
                endpoint = '/export/reservation';
                break;
            case '3':
                // Récupérer les données de disponibilité
                const availabilityResponse = await fetch(`${getApi()}/availability`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        hotel_id: state.hotelId,
                        start_date: document.getElementById('availabilityStart').value || new Date().toISOString().split('T')[0],
                        end_date: document.getElementById('availabilityEnd').value || new Date(Date.now() + 30*24*60*60*1000).toISOString().split('T')[0],
                        room_types: [],
                        performed_by: 'frontend-ui'
                    }),
                });
                data = await availabilityResponse.json();
                endpoint = '/export/availability';
                break;
        }

        showToast('Génération du rapport groupé...', 'info');
        
        response = await fetch(`${getApi()}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data }),
        });

        if (!response.ok) throw new Error('Export impossible');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        const timestamp = Date.now();
        let filename;
        switch(exportType) {
            case '1': filename = `simulation_complete_${state.hotelId}_${timestamp}.xlsx`; break;
            case '2': filename = `reservation_prediction_${state.hotelId}_${timestamp}.xlsx`; break;
            case '3': filename = `disponibilites_complete_${state.hotelId}_${timestamp}.xlsx`; break;
        }
        
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);
        
        showToast('Rapport groupé téléchargé avec succès', 'success');
        
    } catch (error) {
        showToast(`Erreur export groupé: ${error.message}`, 'error');
    }
};

// ==========================================
// 2. AMÉLIORATIONS POUR index.html (Interface principale)
// ==========================================

// Remplacez le bouton export Excel existant par ces nouveaux boutons dans votre section de simulation:
// (Dans le fichier index.html, à la ligne ~91, remplacez le bouton exportExcel existant)

// <div class="flex gap-2">
//     <button id="exportExcel" class="btn-secondary">
//         <i data-feather="download"></i>
//         Export Standard
//     </button>
//     <button id="exportExcelEnhanced" class="btn-primary">
//         <i data-feather="file-text"></i>
//         Rapport Complet
//     </button>
//     <button id="exportReservation" class="btn-secondary">
//         <i data-feather="trending-up"></i>
//         Prévision Réservation
//     </button>
// </div>

// Ajout des event listeners pour les nouveaux boutons
document.getElementById('exportExcelEnhanced').addEventListener('click', exportSimulationEnhanced);
document.getElementById('exportReservation').addEventListener('click', exportReservationSimulation);

// Dans la section disponibilités, ajoutez ce bouton après le bouton de calcul:
// (Après la ligne ~250 dans index.html)
const availabilitySection = document.getElementById('availabilityResults').previousElementSibling;
const exportButton = document.createElement('button');
exportButton.id = 'exportAvailability';
exportButton.className = 'btn-primary';
exportButton.innerHTML = '<i data-feather="calendar"></i> Exporter Disponibilités';
exportButton.addEventListener('click', exportAvailabilityData);
availabilitySection.querySelector('.flex.justify-end.gap-3').appendChild(exportButton);

// ==========================================
// 3. AMÉLIORATIONS POUR index_1.html (Console Admin)
// ==========================================

// Dans la section backup (vers la ligne ~300), ajoutez ces boutons:
const backupSection = document.getElementById('backupSection');
const exportButtons = document.createElement('div');
exportButtons.className = 'glass-card';
exportButtons.innerHTML = `
    <h3 class="text-lg font-semibold">Exports Avancés</h3>
    <div class="mt-4 space-y-3 text-sm text-slate-300">
        <button id="exportBatchReports" class="quick-action">
            <i data-feather="package"></i>
            Exporter Rapports Groupés
        </button>
        <button id="exportAllData" class="quick-action">
            <i data-feather="database"></i>
            Exporter Toutes les Données
        </button>
        <button id="exportMetrics" class="quick-action">
            <i data-feather="bar-chart"></i>
            Exporter Métriques Système
        </button>
    </div>
`;

// Insérer après la section backup existante
backupSection.appendChild(exportButtons);

// Event listeners pour la console admin
document.getElementById('exportBatchReports').addEventListener('click', exportBatchReports);

// Fonction pour exporter toutes les données
const exportAllData = async () => {
    try {
        showToast('Génération de l\'export complet...', 'info');
        
        // Récupérer les métriques système
        const healthData = await fetchJSON('/monitor/health');
        
        // Créer un fichier Excel avec toutes les données
        const output = io.BytesIO();
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer => {
            // Feuille 1: Métriques système
            metrics_df = pd.DataFrame([healthData]);
            metrics_df.to_excel(writer, sheet_name='Métriques Système', index=false);
            
            // Feuille 2: Liste des hôtels
            const hotels = await fetchJSON('/hotels?include_inactive=true');
            hotels_df = pd.DataFrame(hotels);
            hotels_df.to_excel(writer, sheet_name='Liste Hôtels', index=false);
            
            // Feuille 3: Activités récentes
            const activities = await fetchJSON('/activity?limit=100');
            activities_df = pd.DataFrame(activities);
            activities_df.to_excel(writer, sheet_name='Historique Activités', index=false);
        }
        
        output.seek(0);
        
        const blob = new Blob([output.getvalue()], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `export_complet_systeme_${Date.now()}.xlsx`;
        link.click();
        window.URL.revokeObjectURL(url);
        
        showToast('Export complet téléchargé', 'success');
        
    } catch (error) {
        showToast(`Erreur export complet: ${error.message}`, 'error');
    }
};

document.getElementById('exportAllData').addEventListener('click', exportAllData);

// Fonction pour exporter les métriques
const exportMetrics = async () => {
    try {
        showToast('Génération du rapport de métriques...', 'info');
        
        const healthData = await fetchJSON('/monitor/health');
        
        const output = io.BytesIO();
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer => {
            // Créer plusieurs feuilles avec les données
            const metrics_sheets = [
                { name: 'Santé Système', data: healthData },
                { name: 'Métriques Base', data: healthData.metrics },
                { name: 'Stockage', data: healthData.storage }
            ];
            
            metrics_sheets.forEach(sheet => {
                df = pd.DataFrame([sheet.data]);
                df.to_excel(writer, sheet_name=sheet.name, index=false);
            });
        }
        
        output.seek(0);
        
        const blob = new Blob([output.getvalue()], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `metriques_systeme_${Date.now()}.xlsx`;
        link.click();
        window.URL.revokeObjectURL(url);
        
        showToast('Rapport de métriques téléchargé', 'success');
        
    } catch (error) {
        showToast(`Erreur export métriques: ${error.message}`, 'error');
    }
};

document.getElementById('exportMetrics').addEventListener('click', exportMetrics);

// ==========================================
// 4. AMÉLIORATION DE L'INTERFACE UTILISATEUR
// ==========================================

// Ajouter des indicateurs visuels pour les exports dans index.html
const addExportIndicators = () => {
    // Ajouter un indicateur de statut pour chaque type d'export
    const exportStatuses = {
        simulation: { text: 'Prêt', color: 'emerald' },
        reservation: { text: 'Prêt', color: 'sky' },
        availability: { text: 'En attente', color: 'amber' }
    };
    
    Object.entries(exportStatuses).forEach(([type, status]) => {
        const indicator = document.createElement('div');
        indicator.className = `flex items-center gap-2 text-xs text-${status.color}-400`;
        indicator.innerHTML = `
            <span class="inline-flex h-2 w-2 rounded-full bg-${status.color}-400"></span>
            Export ${type}: ${status.text}
        `;
        
        // Ajouter l'indicateur dans l'en-tête de la section correspondante
        const section = document.getElementById(`tab${type.charAt(0).toUpperCase() + type.slice(1)}`);
        if (section) {
            const header = section.querySelector('h3');
            if (header) {
                header.parentNode.insertBefore(indicator, header.nextSibling);
            }
        }
    });
};

// Appeler cette fonction après le chargement des données
document.addEventListener('DOMContentLoaded', () => {
    // ... autres initialisations ...
    setTimeout(addExportIndicators, 2000); // Attendre que les données soient chargées
});

// ==========================================
// 5. FONCTIONS D'AIDE ET VALIDATION
// ==========================================

// Fonction pour valider les données avant export
const validateExportData = (type, data) => {
    const validations = {
        simulation: () => data && data.results && data.results.length > 0,
        reservation: () => data && data.simulation_info && data.results,
        availability: () => data && data.availability && data.period
    };
    
    const validator = validations[type];
    if (!validator) {
        throw new Error(`Type d'export non supporté: ${type}`);
    }
    
    if (!validator()) {
        throw new Error(`Données insuffisantes pour l'export ${type}`);
    }
    
    return true;
};

// Fonction pour gérer les erreurs d'export de manière gracieuse
const handleExportError = (error, exportType) => {
    console.error(`Erreur export ${exportType}:`, error);
    
    const errorMessages = {
        simulation: 'Impossible d\'exporter la simulation. Vérifiez que des données de simulation sont disponibles.',
        reservation: 'Impossible d\'exporter les prévisions de réservation. Réalisez d\'abord une simulation.',
        availability: 'Impossible d\'exporter les disponibilités. Consultez d\'abord les disponibilités pour la période desired.'
    };
    
    showToast(errorMessages[exportType] || 'Erreur lors de l\'export', 'error');
    
    // Log de l'erreur pour debugging
    with Session(engine) => session => {
        log_activity(
            session,
            activity_type="export.failed",
            description=`Échec export ${exportType}`,
            details: {
                error: error.message,
                export_type: exportType,
                timestamp: new Date().toISOString()
            },
            performed_by="frontend-ui"
        );
        session.commit();
    };
};

// ==========================================
// 6. NOTIFICATIONS ET FEEDBACK UTILISATEUR
// ==========================================

// Amélioration de la fonction showToast pour les exports
const showExportProgress = (message, type = 'info', duration = 3000) => {
    const toast = document.createElement('div');
    toast.className = `toast pointer-events-auto ${type === 'info' ? 'border-sky-400/40 bg-sky-500/10 text-sky-200' : ''}`;
    toast.innerHTML = `
        <div class="flex items-center gap-3">
            <div class="animate-spin rounded-full h-4 w-4 border-2 border-sky-400 border-t-transparent"></div>
            <span>${message}</span>
        </div>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    feather.replace({ class: 'h-4 w-4' });
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 500);
    }, duration);
};

// Remplacer showToast par showExportProgress dans les fonctions d'export
// showToast('Génération du rapport...', 'info');
// par
// showExportProgress('Génération du rapport...', 'info');