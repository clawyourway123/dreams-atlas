// Plotly Lazy Loader — loads Plotly.js on demand instead of blocking page render
// Usage: loadPlotly().then(() => { Plotly.newPlot(...); })

(function () {
    var PLOTLY_CDN = 'https://cdn.plot.ly/plotly-2.35.0.min.js';
    var _promise = null;

    window.loadPlotly = function () {
        if (_promise) return _promise;

        if (typeof Plotly !== 'undefined') {
            _promise = Promise.resolve();
            return _promise;
        }

        _promise = new Promise(function (resolve, reject) {
            var script = document.createElement('script');
            script.src = PLOTLY_CDN;
            script.async = true;
            script.onload = resolve;
            script.onerror = function () {
                _promise = null;
                reject(new Error('Failed to load Plotly.js'));
            };
            document.head.appendChild(script);
        });

        return _promise;
    };
})();
