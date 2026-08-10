/* =========================================================
   03_sunburst.js
   Cyclone Activity — Country → Year Sunburst

   Data:
   data/03_cyclones_data.json

   HTML container:
   #cyclone-chart

   Requirements:
   - Plotly.js loaded before this file
   - Inter font handled by CSS
   ========================================================= */


/* =========================================================
   CONFIGURATION
   ========================================================= */

const SUNBURST_CONFIG = {

    dataPath: "data/03_cyclones_data.json",

    chartId: "cyclone-chart",

    colors: [
        "#EEF8FC",
        "#D8EEF7",
        "#BBDDEA",
        "#9BCEDF",
        "#78BCD4",
        "#5BA8C5",
        "#478EAF",
        "#357596"
    ],

    textColor: "#000000",

    mutedText: "#7A858A",

    white: "#FFFFFF"
};


/* =========================================================
   LOAD DATA
   ========================================================= */

async function loadSunburstData() {

    const response = await fetch(
        SUNBURST_CONFIG.dataPath
    );

    if (!response.ok) {
        throw new Error(
            `Could not load ${SUNBURST_CONFIG.dataPath}`
        );
    }

    const rawData = await response.json();


    /* -----------------------------------------------------
       Clean data
       ----------------------------------------------------- */

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


    /* -----------------------------------------------------
       Last 20 years
       ----------------------------------------------------- */

    const latestYear = Math.max(
        ...data.map(row => row.year)
    );

    const firstYear = latestYear - 19;

    data = data.filter(row =>
        row.year >= firstYear &&
        row.year <= latestYear
    );


    return {
        data,
        firstYear,
        latestYear
    };
}


/* =========================================================
   COUNTRY TOTALS
   ========================================================= */

function calculateCountryTotals(data) {

    const totals = {};

    data.forEach(row => {

        if (!totals[row.country]) {
            totals[row.country] = 0;
        }

        totals[row.country] += row.cyclone_count;
    });


    return Object.entries(totals)
        .sort((a, b) => b[1] - a[1]);
}


/* =========================================================
   BUILD SUNBURST HIERARCHY
   ========================================================= */

function buildSunburstHierarchy(data) {

    const labels = [];
    const parents = [];
    const values = [];
    const ids = [];

    /*
     * ------------------------------------------------------
     * Aggregate duplicate country/year records
     * ------------------------------------------------------
     */

    const yearlyTotals = {};

    data.forEach(row => {

        const key = `${row.country}|||${row.year}`;

        if (!yearlyTotals[key]) {
            yearlyTotals[key] = {
                country: row.country,
                year: row.year,
                value: 0
            };
        }

        yearlyTotals[key].value += row.cyclone_count;
    });


    /*
     * ------------------------------------------------------
     * Calculate country totals
     * ------------------------------------------------------
     */

    const countryTotals = {};

    Object.values(yearlyTotals).forEach(row => {

        if (!countryTotals[row.country]) {
            countryTotals[row.country] = 0;
        }

        countryTotals[row.country] += row.value;
    });


    /*
     * ------------------------------------------------------
     * Country nodes
     * ------------------------------------------------------
     */

    Object.entries(countryTotals)
        .sort((a, b) => b[1] - a[1])
        .forEach(([country, total]) => {

            const countryId =
                `country-${country}`;

            ids.push(countryId);

            labels.push(country);

            parents.push("");

            values.push(total);
        });


    /*
     * ------------------------------------------------------
     * Year nodes
     * ------------------------------------------------------
     */

    Object.values(yearlyTotals)
        .sort((a, b) => {

            if (a.country !== b.country) {
                return a.country.localeCompare(
                    b.country
                );
            }

            return a.year - b.year;
        })
        .forEach(row => {

            const countryId =
                `country-${row.country}`;

            const yearId =
                `year-${row.country}-${row.year}`;

            ids.push(yearId);

            labels.push(
                String(row.year)
            );

            parents.push(
                countryId
            );

            values.push(
                row.value
            );
        });


    return {
        ids,
        labels,
        parents,
        values,
        countryTotals
    };
}


/* =========================================================
   CREATE SUNBURST
   ========================================================= */

async function createSunburst() {

    try {

        /* -------------------------------------------------
           Load data
           ------------------------------------------------- */

        const {
            data,
            firstYear,
            latestYear
        } = await loadSunburstData();


        if (!data.length) {

            console.warn(
                "No cyclone data available."
            );

            return;
        }


        /* -------------------------------------------------
           Country totals
           ------------------------------------------------- */

        const countryTotals =
            calculateCountryTotals(data);


        if (!countryTotals.length) {

            console.warn(
                "No country totals available."
            );

            return;
        }


        const most =
            countryTotals[0];

        const least =
            countryTotals[
                countryTotals.length - 1
            ];


        /* -------------------------------------------------
           Build hierarchy
           ------------------------------------------------- */

        const hierarchy =
            buildSunburstHierarchy(data);


        /* =================================================
           SUNBURST TRACE
           ================================================= */

        const trace = {

            type: "sunburst",

            ids: hierarchy.ids,

            labels: hierarchy.labels,

            parents: hierarchy.parents,

            values: hierarchy.values,

            branchvalues: "total",

            textinfo: "label",

            insidetextorientation: "radial",

            hovertemplate:
                "<b>%{label}</b><br>" +
                "Cyclones: %{value}" +
                "<extra></extra>",

            marker: {

                colors: hierarchy.values,

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

                showscale: true,

                colorbar: {

                    title: {
                        text: "Cyclones",
                        font: {
                            size: 12,
                            color: "#000000"
                        }
                    },

                    thickness: 12,
                    len: 0.55,
                    x: 0.83,
                    outlinewidth: 0,

                    tickfont: {
                        size: 10,
                        color: "#000000"
                    }
                },

                line: {
                    color: "#FFFFFF",
                    width: 2
                }
            }
        };


        /* =================================================
           LAYOUT
           ================================================= */

        const layout = {

            paper_bgcolor:
                SUNBURST_CONFIG.white,

            plot_bgcolor:
                SUNBURST_CONFIG.white,


            /* -------------------------------------------------
               Typography
               ------------------------------------------------- */

            font: {

                family:
                    "Inter, system-ui, -apple-system, " +
                    "BlinkMacSystemFont, 'Segoe UI', sans-serif",

                color:
                    SUNBURST_CONFIG.textColor
            },


            /* -------------------------------------------------
               Title
               ------------------------------------------------- */

            title: {

                text:
                    `<b>Storms Meet the Islands in the Last 20 Years</b>` +
                    `<br><sup style="display:inline-block; margin-top:6px;">` +
                    `<br><sup>Cyclone activity, ${firstYear}–${latestYear}</sup>`,

                x: 0.05,

                xanchor: "left",

                font: {

                    size: 21,

                    color:
                        SUNBURST_CONFIG.textColor
                }
            },


            /* -------------------------------------------------
               Annotations
               ------------------------------------------------- */

            annotations: [

                {
                    x: 0.5,

                    y: -0.06,

                    xref: "paper",

                    yref: "paper",

                    text:
                        "Larger segments indicate more cyclones. " +
                        "Click a country to explore its years.",

                    showarrow: false,

                    align: "center",

                    font: {

                        size: 11,

                        color:
                            SUNBURST_CONFIG.mutedText
                    }
                },


                {
                    x: 0.5,

                    y: -0.12,

                    xref: "paper",

                    yref: "paper",

                    text:
                        `<b>Most:</b> ${most[0]} ` +
                        `(${Math.round(most[1])})` +
                        ` &nbsp;&nbsp;•&nbsp;&nbsp; ` +
                        `<b>Least:</b> ${least[0]} ` +
                        `(${Math.round(least[1])})`,

                    showarrow: false,

                    align: "center",

                    font: {

                        size: 13,

                        color:
                            SUNBURST_CONFIG.textColor
                    }
                }
            ],


            /* -------------------------------------------------
               Margins
               ------------------------------------------------- */

            margin: {

                t: 95,

                l: 30,

                r: 30,

                b: 100
            },


            height: 750,

            showlegend: false
        };


        /* =================================================
           PLOTLY CONFIGURATION
           ================================================= */

        const plotlyConfig = {

            responsive: true,

            displayModeBar: false,

            displaylogo: false,

            scrollZoom: false
        };


        /* =================================================
           RENDER
           ================================================= */

        await Plotly.newPlot(

            SUNBURST_CONFIG.chartId,

            [trace],

            layout,

            plotlyConfig
        );


        /* =================================================
           RESIZE
           ================================================= */

        window.addEventListener(
            "resize",
            () => {

                Plotly.Plots.resize(
                    SUNBURST_CONFIG.chartId
                );

            }
        );


        /* =================================================
           COUNTRY CLICK EVENT
           ================================================= */

        const chart =
            document.getElementById(
                SUNBURST_CONFIG.chartId
            );


        chart.on(
            "plotly_sunburstclick",
            function(event) {

                if (
                    !event ||
                    !event.points ||
                    !event.points.length
                ) {
                    return;
                }


                const point =
                    event.points[0];


                console.log(
                    "Sunburst selection:",
                    point.label
                );


                /*
                 * Plotly provides the hierarchy path.
                 *
                 * Example:
                 *
                 * ["Philippines", "2019"]
                 *
                 * The first item is the country.
                 */

                const path =
                    point.sunburst?.path;


                let selectedCountry =
                    point.label;


                if (
                    Array.isArray(path) &&
                    path.length > 0
                ) {

                    selectedCountry =
                        path[0];

                }


                /* ---------------------------------------------
                   Custom event for other charts
                   --------------------------------------------- */

                document.dispatchEvent(

                    new CustomEvent(
                        "countrySelected",
                        {
                            detail: {

                                country:
                                    selectedCountry,

                                label:
                                    point.label,

                                path:
                                    path || []
                            }
                        }
                    )

                );

            }
        );


    } catch (error) {

        console.error(
            "Sunburst visualization error:",
            error
        );

    }
}


/* =========================================================
   INITIALIZE
   ========================================================= */

createSunburst();
