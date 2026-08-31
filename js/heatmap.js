/* =========================================================
   heatmap.js
   Cyclone Activity — Country × Year Heatmap with Slicing

   Data:
   backend/data/03_cyclones_data.json

   HTML container:
   #cyclone-chart
   ========================================================= */


/* =========================================================
   CONFIGURATION
   ========================================================= */

const HEATMAP_CONFIG = {
    dataPath: "backend/data/03_cyclones_data.json",
    chartId: "heatmap",
    
    // Sequential palette mapping low to high storm activity
    colorscale: [
        [0.00, "#EEF8FC"],
        [0.15, "#D8EEF7"],
        [0.30, "#BBDDEA"],
        [0.45, "#9BCEDF"],
        [0.60, "#78BCD4"],
        [0.75, "#5BA8C5"],
        [0.90, "#478EAF"],
        [1.00, "#357596"]
    ],

    textColor: "#000000",
    mutedText: "#7A858A",
    white: "#FFFFFF"
};


/* =========================================================
   LOAD & PROCESS DATA
   ========================================================= */

async function loadHeatmapData() {
    const response = await fetch(HEATMAP_CONFIG.dataPath);

    if (!response.ok) {
        throw new Error(`Could not load ${HEATMAP_CONFIG.dataPath}`);
    }

    const rawData = await response.json();

    // Clean data
    let data = rawData
        .map(row => ({
            country: String(row.country ?? "").trim(),
            year: Number(row.year),
            cyclone_count: Number(row.cyclone_count)
        }))
        .filter(row =>
            row.country !== "" &&
            Number.isFinite(row.year) &&
            Number.isFinite(row.cyclone_count)
        );

    // Limit to last 20 years dynamically
    const latestYear = Math.max(...data.map(row => row.year));
    const firstYear = latestYear - 19;

    data = data.filter(row => row.year >= firstYear && row.year <= latestYear);

    return { data, firstYear, latestYear };
}


/* =========================================================
   MATRIX BUILDER FOR HEATMAP
   ========================================================= */

function buildHeatmapMatrix(data) {
    // Extract unique, sorted axes
    const years = [...new Set(data.map(d => d.year))].sort((a, b) => a - b);
    const countries = [...new Set(data.map(d => d.country))].sort().reverse(); // Bottom-to-top layout

    // Pre-aggregate duplicates via lookup map
    const lookup = {};
    data.forEach(row => {
        const key = `${row.country}|||${row.year}`;
        lookup[key] = (lookup[key] || 0) + row.cyclone_count;
    });

    // Populate 2D Z-matrix
    const zValues = countries.map(country => {
        return years.map(year => {
            const key = `${country}|||${year}`;
            return lookup[key] ?? 0;
        });
    });

    return { years, countries, zValues };
}


/* =========================================================
   CREATE HEATMAP
   ========================================================= */

async function createHeatmap() {
    try {
        const { data, firstYear, latestYear } = await loadHeatmapData();

        if (!data.length) {
            console.warn("No cyclone data available.");
            return;
        }

        const { years, countries, zValues } = buildHeatmapMatrix(data);

        /* =================================================
           TRACE SETUP
           ================================================= */

        const trace = {
            type: "heatmap",
            x: years.map(String),
            y: countries,
            z: zValues,
            colorscale: HEATMAP_CONFIG.colorscale,
            showscale: true,
            colorbar: {
                title: {
                    text: "Cyclones",
                    font: { size: 12, color: HEATMAP_CONFIG.textColor }
                },
                thickness: 12,
                len: 0.85,
                outlinewidth: 0,
                tickfont: { size: 10, color: HEATMAP_CONFIG.textColor }
            },
            hovertemplate:
                "<b>Country:</b> %{y}<br>" +
                "<b>Year:</b> %{x}<br>" +
                "<b>Cyclones:</b> %{z}<extra></extra>"
        };


        /* =================================================
           DROPDOWN CONTROLS (NON-DESTRUCTIVE SLICING)
           ================================================= */

        // 1. Country Slicing Dropdowns
        const countryButtons = [
            {
                label: "All Countries",
                method: "restyle",
                args: [{ z: [zValues] }]
            },
            ...countries.map((country, countryIdx) => {
                const slicedZ = zValues.map((row, rIdx) =>
                    rIdx === countryIdx ? row : row.map(() => null)
                );
                return {
                    label: country,
                    method: "restyle",
                    args: [{ z: [slicedZ] }]
                };
            })
        ];

        // 2. Year Slicing Dropdowns
        const yearButtons = [
            {
                label: "All Years",
                method: "restyle",
                args: [{ z: [zValues] }]
            },
            ...years.map((year, yearIdx) => {
                const slicedZ = zValues.map(row =>
                    row.map((val, cIdx) => (cIdx === yearIdx ? val : null))
                );
                return {
                    label: String(year),
                    method: "restyle",
                    args: [{ z: [slicedZ] }]
                };
            })
        ];


        /* =================================================
           LAYOUT
           ================================================= */

        const layout = {
            paper_bgcolor: HEATMAP_CONFIG.white,
            plot_bgcolor: HEATMAP_CONFIG.white,

            font: {
                family: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                color: HEATMAP_CONFIG.textColor
            },

            title: {
                text:
                    `<b>Storms Meet the Islands in the Last 20 Years</b>` +
                    `<br><sup style="display:inline-block; margin-top:4px;">` +
                    `Cyclone activity, ${firstYear}–${latestYear}</sup>`,
                x: 0.0,
                xanchor: "left",
                y: 0.98,
                yanchor: "top",
                font: { size: 20, color: HEATMAP_CONFIG.textColor }
            },

            xaxis: {
                title: { text: "Year", font: { color: HEATMAP_CONFIG.textColor, size: 12 }, standoff: 15 },
                type: "category",
                showgrid: false,
                zeroline: false,
                side: "bottom"
            },

            yaxis: {
                automargin: true,
                showgrid: false,
                zeroline: false
            },

        updatemenus: [
            {
                buttons: countryButtons,
                direction: "down",
                showactive: true,
                x: 0.0,
                xanchor: "left",
                y: 1.18, // Pushed higher above the heatmap grid
                yanchor: "top",
                bgcolor: HEATMAP_CONFIG.white,
                bordercolor: "#EAE6DF",
                pad: { r: 10, t: 5, b: 5, l: 5 }
            },
            {
                buttons: yearButtons,
                direction: "down",
                showactive: true,
                x: 0.25,
                xanchor: "left",
                y: 1.18, // Pushed higher above the heatmap grid
                yanchor: "top",
                bgcolor: HEATMAP_CONFIG.white,
                bordercolor: "#EAE6DF",
                pad: { r: 10, t: 5, b: 5, l: 5 }
            }
        ],

        annotations: [
            // Dropdown Label 1
            {
                xref: "paper",
                yref: "paper",
                x: 0.0,
                y: 1.25, // Placed directly above the first dropdown
                text: "<b>Country Filter:</b>",
                showarrow: false,
                font: { size: 11, color: HEATMAP_CONFIG.textColor }
            },
            // Dropdown Label 2
            {
                xref: "paper",
                yref: "paper",
                x: 0.25,
                y: 1.25, // Placed directly above the second dropdown
                text: "<b>Year Filter:</b>",
                showarrow: false,
                font: { size: 11, color: HEATMAP_CONFIG.textColor }
            },
        // Bottom Helper Guidance (Moved below the X-axis)
        {
            xref: "paper",
            yref: "paper",
            x: 0.5,
            y: -0.22, // Placed cleanly below the X-axis "Year" title
            text: "Hover over cells to view cyclone totals. Use drop-down controls above to highlight single slices.",
            showarrow: false,
            align: "center",
            font: { size: 11, color: HEATMAP_CONFIG.mutedText }
                }
            ],

            // Expanded top margin (t: 180) and bottom margin (b: 100) to grant spacing
            margin: { t: 180, l: 120, r: 40, b: 100 },
            height: 720,
            showlegend: false
        };

        const plotlyConfig = {
            responsive: true,
            displayModeBar: false,
            displaylogo: false,
            scrollZoom: false
        };


        /* =================================================
           RENDER & ATTACH EVENTS
           ================================================= */

        await Plotly.newPlot(
            HEATMAP_CONFIG.chartId,
            [trace],
            layout,
            plotlyConfig
        );

        const chartContainer = document.getElementById(HEATMAP_CONFIG.chartId);

        // Click Event Dispatcher for Inter-chart communication
        chartContainer.on("plotly_click", function(event) {
            if (!event || !event.points || !event.points.length) return;

            const point = event.points[0];
            const clickedCountry = point.y;
            const clickedYear = point.x;

            document.dispatchEvent(
                new CustomEvent("countrySelected", {
                    detail: {
                        country: clickedCountry,
                        year: clickedYear,
                        value: point.z
                    }
                })
            );
        });

        // Window resize binding
        window.addEventListener("resize", () => {
            Plotly.Plots.resize(HEATMAP_CONFIG.chartId);
        });

    } catch (error) {
        console.error("Heatmap visualization error:", error);
    }
}


/* =========================================================
   INITIALIZE
   ========================================================= */

createHeatmap();