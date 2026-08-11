/* =========================================================
   02_environmenttrends.js

   Data:
   data/01_environmental_trends.json

   HTML:
   <div id="trend-chart"></div>

   Requires:
   Plotly.js
   ========================================================= */


/* =========================================================
   CONFIG
   ========================================================= */

const ENV_CONFIG = {

    dataPath: "data/01_environmental_trends.json",

    chartId: "trend-chart",

    colors: {
        seaLevel: "#07575B",
        temperature: "#E4572E",

        baseline: "#B0A8A0",

        grid: "#EAE6DF",

        background: "#FFFFFF",

        text: "#000000",

        muted: "#7A858A"
    }
};


/* =========================================================
   LOAD DATA
   ========================================================= */

async function loadEnvironmentalData() {

    const response = await fetch(
        ENV_CONFIG.dataPath
    );

    if (!response.ok) {
        throw new Error(
            `Could not load ${ENV_CONFIG.dataPath}`
        );
    }

    const rawData = await response.json();


    /* -----------------------------------------------------
       Clean / normalize
       ----------------------------------------------------- */

    return rawData
        .map(row => ({

            country:
                String(row.country ?? "").trim(),

            year:
                Number(row.year),

            sea_level:
                Number(row.sea_lvl_value),

            temperature:
                Number(row.sea_temperature)

        }))
        .filter(row =>

            row.country !== "" &&

            Number.isFinite(row.year) &&

            Number.isFinite(row.sea_level) &&

            Number.isFinite(row.temperature)

        );
}


/* =========================================================
   CALCULATE PACIFIC OVERALL MEAN
   ========================================================= */

function calculateOverall(data) {

    const yearly = {};

    data.forEach(row => {

        if (!yearly[row.year]) {

            yearly[row.year] = {

                seaLevel: [],

                temperature: []

            };
        }


        yearly[row.year].seaLevel.push(
            row.sea_level
        );

        yearly[row.year].temperature.push(
            row.temperature
        );
    });


    return Object.keys(yearly)

        .map(year => {

            const values =
                yearly[year];

            return {

                year: Number(year),

                seaLevel:
                    mean(values.seaLevel),

                temperature:
                    mean(values.temperature)
            };
        })

        .sort(
            (a, b) => a.year - b.year
        );
}


/* =========================================================
   MEAN HELPER
   ========================================================= */

function mean(values) {

    if (!values.length) {
        return null;
    }

    return values.reduce(
        (sum, value) => sum + value,
        0
    ) / values.length;
}


/* =========================================================
   CALCULATE COUNTRY DATA
   ========================================================= */

function calculateCountryData(
    data,
    country
) {

    const filtered =
        data.filter(
            row => row.country === country
        );


    const yearly = {};


    filtered.forEach(row => {

        if (!yearly[row.year]) {

            yearly[row.year] = {

                seaLevel: [],

                temperature: []

            };
        }


        yearly[row.year].seaLevel.push(
            row.sea_level
        );

        yearly[row.year].temperature.push(
            row.temperature
        );
    });


    return Object.keys(yearly)

        .map(year => {

            const values =
                yearly[year];

            return {

                year: Number(year),

                seaLevel:
                    mean(values.seaLevel),

                temperature:
                    mean(values.temperature)
            };
        })

        .sort(
            (a, b) => a.year - b.year
        );
}


/* =========================================================
   CREATE OVERALL TRACES
   ========================================================= */

function createOverallTraces(
    overall
) {

    return [

        /* -------------------------------------------------
           Sea level
           ------------------------------------------------- */

        {

            x:
                overall.map(
                    d => d.year
                ),

            y:
                overall.map(
                    d => d.seaLevel
                ),

            type: "scatter",

            mode: "lines",

            name:
                "Pacific sea-level average",

            line: {

                color:
                    ENV_CONFIG.colors.seaLevel,

                width: 3
            },

            fill: "tozeroy",

            fillcolor:
                "rgba(7, 87, 91, 0.08)",

            hovertemplate:
                "<b>%{x}</b><br>" +
                "Pacific sea-level average: " +
                "%{y:.3f}" +
                "<extra></extra>",

            xaxis: "x",

            yaxis: "y"
        },


        /* -------------------------------------------------
           Temperature
           ------------------------------------------------- */

        {

            x:
                overall.map(
                    d => d.year
                ),

            y:
                overall.map(
                    d => d.temperature
                ),

            type: "scatter",

            mode: "lines",

            name:
                "Pacific temperature average",

            line: {

                color:
                    ENV_CONFIG.colors.temperature,

                width: 3
            },

            fill: "tozeroy",

            fillcolor:
                "rgba(228, 87, 46, 0.08)",

            hovertemplate:
                "<b>%{x}</b><br>" +
                "Pacific temperature average: " +
                "%{y:.3f} °C" +
                "<extra></extra>",

            xaxis: "x2",

            yaxis: "y2"
        }

    ];
}


/* =========================================================
   CREATE COUNTRY TRACES
   ========================================================= */

function createCountryTraces(
    data,
    countries
) {

    const traces = [];


    countries.forEach(country => {

        const countryData =
            calculateCountryData(
                data,
                country
            );


        /* ---------------------------------------------
           Sea level
           --------------------------------------------- */

        traces.push({

            x:
                countryData.map(
                    d => d.year
                ),

            y:
                countryData.map(
                    d => d.seaLevel
                ),

            type: "scatter",

            mode: "lines",

            name: country,

            line: {

                color:
                    ENV_CONFIG.colors.seaLevel,

                width: 2
            },

            visible: false,

            hovertemplate:
                `<b>${country}</b><br>` +
                "Sea-level anomaly: " +
                "%{y:.3f}" +
                "<extra></extra>",

            xaxis: "x",

            yaxis: "y"
        });


        /* ---------------------------------------------
           Temperature
           --------------------------------------------- */

        traces.push({

            x:
                countryData.map(
                    d => d.year
                ),

            y:
                countryData.map(
                    d => d.temperature
                ),

            type: "scatter",

            mode: "lines",

            name: country,

            line: {

                color:
                    ENV_CONFIG.colors.temperature,

                width: 2
            },

            visible: false,

            hovertemplate:
                `<b>${country}</b><br>` +
                "Temperature anomaly: " +
                "%{y:.3f} °C" +
                "<extra></extra>",

            xaxis: "x2",

            yaxis: "y2"
        });

    });


    return traces;
}


/* =========================================================
   CREATE DROPDOWN
   ========================================================= */

function createDropdown(
    countries,
    totalTraceCount
) {

    const buttons = [];


    /* -----------------------------------------------------
       Pacific Overall
       ----------------------------------------------------- */

    const overallVisibility =
        Array(totalTraceCount).fill(false);

    overallVisibility[0] = true;
    overallVisibility[1] = true;


    buttons.push({

        label: "Pacific Overall",

        method: "update",

        args: [

            {
                visible:
                    overallVisibility
            },

            {
                "title.text":
                    `<b>Changes Across the Pacific</b>` +
                    `<br><sup>` +
                    `Mean sea-level and temperature anomalies` +
                    `</sup>`
            }

        ]

    });


    /* -----------------------------------------------------
       Countries
       ----------------------------------------------------- */

    countries.forEach(
        (country, index) => {

            const visibility =
                Array(totalTraceCount).fill(false);


            const seaTrace =
                2 + index * 2;

            const temperatureTrace =
                seaTrace + 1;


            visibility[seaTrace] = true;

            visibility[temperatureTrace] =
                true;


            buttons.push({

                label: country,

                method: "update",

                args: [

                    {
                        visible:
                            visibility
                    },

                    {

                        "title.text":
                            `<b>${country}</b>` +
                            `<br><sup>` +
                            `Compared with the Pacific overall mean` +
                            `</sup>`
                    }

                ]

            });

        }
    );


    return buttons;
}


/* =========================================================
   MAIN CHART
   ========================================================= */

async function createEnvironmentalChart() {

    try {

        /* -------------------------------------------------
           Load
           ------------------------------------------------- */

        const data =
            await loadEnvironmentalData();


        if (!data.length) {

            console.warn(
                "No environmental data available."
            );

            return;
        }


        /* -------------------------------------------------
           Overall
           ------------------------------------------------- */

        const overall =
            calculateOverall(data);


        /* -------------------------------------------------
           Countries
           ------------------------------------------------- */

        const countries =
            [...new Set(
                data.map(
                    row => row.country
                )
            )].sort();


        /* -------------------------------------------------
           Traces
           ------------------------------------------------- */

        const overallTraces =
            createOverallTraces(
                overall
            );


        const countryTraces =
            createCountryTraces(
                data,
                countries
            );


        const traces = [
            ...overallTraces,
            ...countryTraces
        ];


        /* -------------------------------------------------
           Dropdown
           ------------------------------------------------- */

        const buttons =
            createDropdown(
                countries,
                traces.length
            );


        /* =================================================
           LAYOUT
           ================================================= */

        const layout = {

            paper_bgcolor:
                ENV_CONFIG.colors.background,

            plot_bgcolor:
                ENV_CONFIG.colors.background,


            /* ---------------------------------------------
               Title
               --------------------------------------------- */

            title: {

                text:
                    `<b>Changes Across the Pacific</b>` +
                    `<br><sup>` +
                    `Mean sea-level and temperature anomalies` +
                    `</sup>`,

                x: 0.02,

                xanchor: "left",

                font: {

                    size: 22,

                    color:
                        ENV_CONFIG.colors.text
                }
            },


            /* ---------------------------------------------
               Dropdown
               --------------------------------------------- */

            updatemenus: [

                {

                    buttons: buttons,

                    direction: "down",

                    showactive: true,

                    x: 0.98,

                    xanchor: "right",

                    y: 1.12,

                    yanchor: "top",

                    bgcolor: "#FFFFFF",

                    bordercolor:
                        ENV_CONFIG.colors.grid
                }

            ],


            /* ---------------------------------------------
               Grid
               --------------------------------------------- */

            xaxis: {

                domain: [0, 1],

                anchor: "y",

                showgrid: false,

                showline: false,

                zeroline: false
            },


            xaxis2: {

                domain: [0, 1],

                anchor: "y2",

                matches: "x",

                showgrid: false,

                showline: false,

                zeroline: false,

                title: {

                    text: "Year",

                    font: {

                        color:
                            ENV_CONFIG.colors.text
                    }
                }
            },


            /* ---------------------------------------------
               Sea-level axis
               --------------------------------------------- */

            yaxis: {

                domain: [0.55, 1],

                title: {

                    text:
                        "Sea-level anomaly",

                    font: {

                        color:
                            ENV_CONFIG.colors.text
                    }
                },

                showgrid: true,

                gridcolor:
                    ENV_CONFIG.colors.grid,

                zeroline: false,

                tickfont: {

                    color:
                        ENV_CONFIG.colors.text
                }
            },


            /* ---------------------------------------------
               Temperature axis
               --------------------------------------------- */

            yaxis2: {

                domain: [0, 0.45],

                title: {

                    text:
                        "Temperature anomaly (°C)",

                    font: {

                        color:
                            ENV_CONFIG.colors.text
                    }
                },

                showgrid: true,

                gridcolor:
                    ENV_CONFIG.colors.grid,

                zeroline: false,

                tickfont: {

                    color:
                        ENV_CONFIG.colors.text
                }
            },


            /* ---------------------------------------------
               Baseline
               --------------------------------------------- */

            shapes: [

                {

                    type: "line",

                    xref: "paper",

                    yref: "y",

                    x0: 0,

                    x1: 1,

                    y0: 0,

                    y1: 0,

                    line: {

                        color:
                            ENV_CONFIG.colors.baseline,

                        width: 1.2,

                        dash: "dash"
                    }
                },


                {

                    type: "line",

                    xref: "paper",

                    yref: "y2",

                    x0: 0,

                    x1: 1,

                    y0: 0,

                    y1: 0,

                    line: {

                        color:
                            ENV_CONFIG.colors.baseline,

                        width: 1.2,

                        dash: "dash"
                    }
                }

            ],


            /* ---------------------------------------------
               Typography
               --------------------------------------------- */

            font: {

                family:
                    "Inter, system-ui, -apple-system, " +
                    "BlinkMacSystemFont, 'Segoe UI', sans-serif",

                color:
                    ENV_CONFIG.colors.text
            },


            /* ---------------------------------------------
               Size
               --------------------------------------------- */

            height: 500,


            margin: {

                l: 80,

                r: 40,

                t: 150,

                b: 60
            },


            showlegend: false,

            hovermode: "x unified"
        };


        /* =================================================
           PLOTLY CONFIG
           ================================================= */

        const config = {

            responsive: true,

            displayModeBar: false,

            displaylogo: false
        };


        /* =================================================
           RENDER
           ================================================= */

        await Plotly.newPlot(

            ENV_CONFIG.chartId,

            traces,

            layout,

            config
        );


        /* -------------------------------------------------
           Responsive resize
           ------------------------------------------------- */

        window.addEventListener(
            "resize",
            () => {

                Plotly.Plots.resize(
                    ENV_CONFIG.chartId
                );

            }
        );


    } catch (error) {

        console.error(
            "Environmental chart error:",
            error
        );

    }
}


/* =========================================================
   INITIALIZE
   ========================================================= */

createEnvironmentalChart();
