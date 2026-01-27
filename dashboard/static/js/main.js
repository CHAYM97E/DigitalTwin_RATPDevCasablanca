// Importations des modules
import { dtInit3D, dtOnWindowResize } from './core/init.js';
import { dtAnimate } from './core/animate.js';
import { dtCreateTerrain } from './world/terrain.js';
import { dtBuildNetwork } from './world/network.js';
import { dtCreateVehicles } from './vehicles/vehicles.js';
import { initUIControls, dtSwitchTab } from './ui/controls.js';
import { dtUpdateStats } from './ui/panels.js';
import { dtInitCharts } from './charts.js';

// Fonction d'initialisation principale
async function initApplication() {
    try {
        // 1. Initialiser la scène 3D
        await dtInit3D();
        
        // 2. Créer le terrain
        dtCreateTerrain();
        
        // 3. Construire le réseau
        dtBuildNetwork();
        
        // 4. Créer les véhicules
        dtCreateVehicles();
        
        // 5. Initialiser les graphiques
        dtInitCharts();
        
        // 6. Initialiser les contrôles UI
        initUIControls();
        
        // 7. Démarrer l'animation
        dtAnimate();
        
        // 8. Configurer les événements
        setupEventListeners();
        
        // 9. Démarrer les mises à jour périodiques
        startPeriodicUpdates();
        
        console.log('Digital Twin initialisé avec succès !');
    } catch (error) {
        console.error('Erreur lors de l\'initialisation du Digital Twin:', error);
    }
}

// Configuration des écouteurs d'événements
function setupEventListeners() {
    // Redimensionnement de la fenêtre
    window.addEventListener('resize', dtOnWindowResize);
    
    // Empêcher le comportement par défaut du contexte
    document.addEventListener('contextmenu', (e) => e.preventDefault());
}

// Mises à jour périodiques
function startPeriodicUpdates() {
    // Auto-switch tabs every 30 seconds for demo
    setInterval(() => {
        const tabs = document.querySelectorAll('.dt-tab');
        const currentIndex = Array.from(tabs).findIndex(t => t.classList.contains('active'));
        const nextIndex = (currentIndex + 1) % tabs.length;
        dtSwitchTab(nextIndex);
    }, 30000);
    
    // Update stats periodically
    setInterval(dtUpdateStats, 3000);
}

// Démarrer l'application lorsque le DOM est chargé
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApplication);
} else {
    initApplication();
}

// Exporter les fonctions globales pour compatibilité avec les anciens event handlers inline
window.dtToggleSimulation = function() {
    import('./ui/controls.js').then(module => {
        module.dtToggleSimulation();
    });
};

window.dtChangeView = function(mode) {
    import('./ui/controls.js').then(module => {
        module.dtChangeView(mode);
    });
};

window.dtTogglePassengers = function() {
    import('./ui/controls.js').then(module => {
        module.dtTogglePassengers();
    });
};

window.dtResetView = function() {
    import('./ui/controls.js').then(module => {
        module.dtResetView();
    });
};

window.dtSelectVehicle = function(index) {
    import('./ui/controls.js').then(module => {
        module.dtSelectVehicle(index);
    });
};

window.dtSwitchTab = function(tabIndex) {
    import('./ui/controls.js').then(module => {
        module.dtSwitchTab(tabIndex);
    });
};