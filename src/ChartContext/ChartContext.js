/* =========================================================
   chartContext.js
   Standardized context passed from frontend to backend
   ========================================================= */

const CHART_CONTEXT = {

    trend: {
        chart_id: "trend-chart",
        audience: "general",

        selection: {
            region: "Pacific Overall",
            start_year: null,
            end_year: null
        }
    },

    bubble: {
        chart_id: "bubble-chart",
        audience: "general",

        selection: {
            period: "2010s",
            region: null
        }
    },

    cyclone: {
        chart_id: "cyclone-chart",
        audience: "general",

        selection: {
            region: null,
            start_year: null,
            end_year: null
        }
    }

};


/* =========================================================
   GET CHART CONTEXT
   ========================================================= */

function getChartContext(chart, updates = {}) {

    const baseContext =
        CHART_CONTEXT[chart];

    if (!baseContext) {
        throw new Error(
            `Unknown chart context: ${chart}`
        );
    }

    return {
        ...baseContext,

        selection: {
            ...baseContext.selection,
            ...updates
        }
    };
}
