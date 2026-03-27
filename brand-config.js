// Brand Configuration — DreaMS Atlas Enterprise
// Maps brand keys to metadata for runtime use

const BRAND_CONFIG = {
    henkel:          { name: 'Henkel',          color: '#e1000f', contrastOnDark: true },
    basf:            { name: 'BASF',            color: '#004A96', contrastOnDark: true },
    '3m':            { name: '3M',              color: '#FF0000', contrastOnDark: true },
    dow:             { name: 'Dow',             color: '#E40046', contrastOnDark: true },
    arkema:          { name: 'Arkema',          color: '#0072CE', contrastOnDark: true },
    'avery-dennison':{ name: 'Avery Dennison',  color: '#CF202F', contrastOnDark: true },
    syensqo:         { name: 'Syensqo',         color: '#6B2D8B', contrastOnDark: true },
    akzonobel:       { name: 'AkzoNobel',       color: '#004B87', contrastOnDark: true },
    clariant:        { name: 'Clariant',        color: '#D7001E', contrastOnDark: true },
    covestro:        { name: 'Covestro',        color: '#00965E', contrastOnDark: true },
    dupont:          { name: 'DuPont',          color: '#ED1C24', contrastOnDark: true },
    evonik:          { name: 'Evonik',          color: '#4A008E', contrastOnDark: true },
    ppg:             { name: 'PPG',             color: '#003DA5', contrastOnDark: true }
};

// Auto-apply brand from data-brand attribute
(function() {
    const brand = document.documentElement.getAttribute('data-brand') ||
                  document.body.getAttribute('data-brand');
    if (brand && BRAND_CONFIG[brand]) {
        document.documentElement.style.setProperty('--accent', BRAND_CONFIG[brand].color);
    }
})();
