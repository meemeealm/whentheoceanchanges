/* =========================================================
   heatmap.js
   Cyclone Activity — Country × Year Heatmap

   Data:
   backend/data/03_cyclones_data.json

   HTML container:
   #heatmap

   Responsibilities:
   - Load cyclone data
   - Build Country × Year matrix
   - Render Plotly heatmap
   - Country/year slicing
   - Track selected country/year
   - Provide selection to explain.js
   ========================================================= */


/* =========================================================
   CONFIGURATION
   ========================================================= */

const HEATMAP_CONFIG = {
    dataPath: "backend/data/03_cyclones_data.json",
    chartId: "heatmap",

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
   GLOBAL HEATMAP STATE
   ========================================================= */

let heatmapState = {
    data: [],
    years: [],
    countries: [],
    zValues: [],
    firstYear: null,
    latestYear: null,

    selectedCountry: null,
    selectedYear: null
};


/* =========================================================
   LOAD DATA
   ========================================================= */

async function loadHeatmapData() {

    const response =
        await fetch(
            HEATMAP_CONFIG.dataPath
        );

    if (!response.ok) {
        throw new Error(
            `Could not load ${HEATMAP_CONFIG.dataPath}`
        );
    }

    const rawData =
        await response.json();

    if (!Array.isArray(rawData)) {
        throw new Error(
            "Heatmap data must be a JSON array."
        );
    }

    let data =
        rawData
            .map(row => ({
                country:
                    String(
                        row?.country ?? ""
                    ).trim(),

                year:
                    Number(
                        row?.year
                    ),

                cyclone_count:
                    Number(
                        row?.cyclone_count
                    )
            }))
            .filter(row =>
                row.country !== "" &&
                Number.isFinite(row.year) &&
                Number.isFinite(row.cyclone_count)
            );

    if (!data.length) {
        return {
            data: [],
            firstYear: null,
            latestYear: null
        };
    }

    /*
     * Keep the latest 20 years.
     */

    const latestYear =
        Math.max(
            ...data.map(
                row => row.year
            )
        );

    const firstYear =
        latestYear - 19;

    data =
        data.filter(
            row =>
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
   BUILD HEATMAP MATRIX
   ========================================================= */

function buildHeatmapMatrix(data) {

    const years =
        [
            ...new Set(
                data.map(
                    row => row.year
                )
            )
        ].sort(
            (a, b) => a - b
        );

    const countries =
        [
            ...new Set(
                data.map(
                    row => row.country
                )
            )
        ].sort()
        .reverse();


    /*
     * Aggregate duplicate
     * country/year combinations.
     */

    const lookup = {};

    data.forEach(row => {

        const key =
            `${row.country}|||${row.year}`;

        lookup[key] =
            (lookup[key] || 0) +
            row.cyclone_count;

    });


    /*
     * Build Z matrix.
     */

    const zValues =
        countries.map(
            country =>
                years.map(
                    year => {

                        const key =
                            `${country}|||${year}`;

                        return (
                            lookup[key] ?? 0
                        );

                    }
                )
        );


    return {
        years,
        countries,
        zValues
    };
}


/* =========================================================
   BUILD COUNTRY FILTER BUTTONS
   ========================================================= */

function buildCountryButtons(
    countries,
    zValues
) {

    const buttons = [];


    /*
     * All countries.
     */

    buttons.push({
        label: "All Countries",

        method: "restyle",

        args: [
            {
                z: [zValues]
            }
        ]
    });


    /*
     * Individual countries.
     */

    countries.forEach(
        (country, countryIndex) => {

            const slicedZ =
                zValues.map(
                    (row, rowIndex) => {

                        if (
                            rowIndex ===
                            countryIndex
                        ) {
                            return [...row];
                        }

                        return row.map(
                            () => null
                        );
                    }
                );


            buttons.push({
                label: country,

                method: "restyle",

                args: [
                    {
                        z: [slicedZ]
                    }
                ]
            });

        }
    );


    return buttons;
}


/* =========================================================
   BUILD YEAR FILTER BUTTONS
   ========================================================= */

function buildYearButtons(
    years,
    zValues
) {

    const buttons = [];


    /*
     * All years.
     */

    buttons.push({
        label: "All Years",

        method: "restyle",

        args: [
            {
                z: [zValues]
            }
        ]
    });


    /*
     * Individual years.
     */

    years.forEach(
        (year, yearIndex) => {

            const slicedZ =
                zValues.map(
                    row =>
                        row.map(
                            (value, columnIndex) =>
                                columnIndex ===
                                yearIndex
                                    ? value
                                    : null
                        )
                );


            buttons.push({
                label: String(year),

                method: "restyle",

                args: [
                    {
                        z: [slicedZ]
                    }
                ]
            });

        }
    );


    return buttons;
}


/* =========================================================
   SYNCHRONIZE EXPLANATION STATE
   ========================================================= */

function syncHeatmapExplanationState(
    country,
    year
) {

    heatmapState.selectedCountry =
        country ?? null;

    heatmapState.selectedYear =
        year != null
            ? Number(year)
            : null;


    /*
     * These are the exact state names consumed
     * by explain.js.
     */

    window.selectedHeatmapRegion =
        heatmapState.selectedCountry;

    window.selectedHeatmapYear =
        heatmapState.selectedYear;


    /*
     * Keep the older cyclone names synchronized too,
     * in case another frontend component still reads them.
     */

    window.selectedCycloneRegion =
        heatmapState.selectedCountry;

    window.selectedCycloneStartYear =
        heatmapState.selectedYear;

    window.selectedCycloneEndYear =
        heatmapState.selectedYear;


    console.log(
        "Heatmap explanation state synchronized:",
        {
            region:
                window.selectedHeatmapRegion,

            year:
                window.selectedHeatmapYear
        }
    );
}


/* =========================================================
   HANDLE COUNTRY/YEAR DROPDOWN RESTYLE
   ========================================================= */

function handleHeatmapRestyle(
    eventData
) {

    if (
        !eventData ||
        !eventData[0]
    ) {
        return;
    }

    const update =
        eventData[0];

    if (
        !update.z ||
        !Array.isArray(update.z[0])
    ) {
        return;
    }

    const selectedZ =
        update.z[0];


    /*
     * Detect selected country.
     *
     * A country filter produces exactly one
     * row containing visible values.
     */

    let selectedCountry = null;

    const visibleRows = [];

    for (
        let rowIndex = 0;
        rowIndex < selectedZ.length;
        rowIndex++
    ) {

        const row =
            selectedZ[rowIndex];

        if (
            !Array.isArray(row)
        ) {
            continue;
        }

        const hasValues =
            row.some(
                value =>
                    value !== null
            );

        if (hasValues) {
            visibleRows.push(rowIndex);
        }
    }

    if (visibleRows.length === 1) {

        selectedCountry =
            heatmapState.countries[
                visibleRows[0]
            ];

    }


    /*
     * Detect selected year.
     *
     * A year filter produces exactly one
     * column containing visible values.
     */

    let selectedYear = null;

    const visibleColumns = [];

    for (
        let columnIndex = 0;
        columnIndex < heatmapState.years.length;
        columnIndex++
    ) {

        const hasValues =
            selectedZ.some(
                row =>
                    Array.isArray(row) &&
                    row[columnIndex] !== null
            );

        if (hasValues) {
            visibleColumns.push(columnIndex);
        }
    }

    if (visibleColumns.length === 1) {

        selectedYear =
            heatmapState.years[
                visibleColumns[0]
            ];

    }


    /*
     * Do not accidentally retain a previous selection
     * when the user chooses "All Countries" or "All Years".
     *
     * If one dimension is selected and the other is not,
     * preserve the already-selected dimension where useful.
     */

    if (
        selectedCountry === null &&
        visibleRows.length !== 1
    ) {
        selectedCountry =
            heatmapState.selectedCountry;
    }

    if (
        selectedYear === null &&
        visibleColumns.length !== 1
    ) {
        selectedYear =
            heatmapState.selectedYear;
    }


    /*
     * If the user explicitly selected "All Countries",
     * clear the country selection.
     */

    if (
        visibleRows.length ===
        heatmapState.countries.length
    ) {
        selectedCountry = null;
    }


    /*
     * If the user explicitly selected "All Years",
     * clear the year selection.
     */

    if (
        visibleColumns.length ===
        heatmapState.years.length
    ) {
        selectedYear = null;
    }


    syncHeatmapExplanationState(
        selectedCountry,
        selectedYear
    );


    console.log(
        "Heatmap dropdown selection:",
        {
            region:
                window.selectedHeatmapRegion,

            year:
                window.selectedHeatmapYear
        }
    );
}


/* =========================================================
   HANDLE CELL CLICK
   ========================================================= */

function handleHeatmapClick(
    event
) {

    if (
        !event ||
        !event.points ||
        !event.points.length
    ) {
        return;
    }

    const point =
        event.points[0];

    const country =
        String(
            point.y ?? ""
        ).trim();

    const year =
        Number(point.x);

    const value =
        Number(point.z);


    if (
        !country ||
        !Number.isFinite(year)
    ) {
        return;
    }


    /*
     * Store and synchronize selected cell.
     */

    syncHeatmapExplanationState(
        country,
        year
    );


    console.log(
        "Heatmap cell selected:",
        {
            country,
            year,
            value
        }
    );


    /*
     * Notify other charts/components.
     */

    document.dispatchEvent(
        new CustomEvent(
            "countrySelected",
            {
                detail: {
                    country,
                    year,
                    value
                }
            }
        )
    );
}


/* =========================================================
   CREATE HEATMAP
   ========================================================= */

async function createHeatmap() {

    try {

        const {
            data,
            firstYear,
            latestYear
        } =
            await loadHeatmapData();


        if (!data.length) {

            console.warn(
                "No cyclone data available."
            );

            return;
        }


        const {
            years,
            countries,
            zValues
        } =
            buildHeatmapMatrix(
                data
            );


        /*
         * Save state.
         */

        heatmapState.data =
            data;

        heatmapState.years =
            years;

        heatmapState.countries =
            countries;

        heatmapState.zValues =
            zValues;

        heatmapState.firstYear =
            firstYear;

        heatmapState.latestYear =
            latestYear;

        heatmapState.selectedCountry =
            null;

        heatmapState.selectedYear =
            null;


        /*
         * Clear all explanation selection state.
         */

        syncHeatmapExplanationState(
            null,
            null
        );


        /* =================================================
           TRACE
           ================================================= */

        const trace = {

            type:
                "heatmap",

            x:
                years.map(
                    String
                ),

            y:
                countries,

            z:
                zValues,

            colorscale:
                HEATMAP_CONFIG.colorscale,

            showscale:
                true,

            colorbar: {

                title: {
                    text:
                        "Cyclones",

                    font: {
                        size: 12,
                        color:
                            HEATMAP_CONFIG.textColor
                    }
                },

                thickness:
                    12,

                len:
                    0.85,

                outlinewidth:
                    0,

                tickfont: {
                    size: 10,
                    color:
                        HEATMAP_CONFIG.textColor
                }

            },

            hovertemplate:
                "<b>Country:</b> %{y}<br>" +
                "<b>Year:</b> %{x}<br>" +
                "<b>Cyclones:</b> %{z}<extra></extra>"
        };


        /* =================================================
           DROPDOWNS
           ================================================= */

        const countryButtons =
            buildCountryButtons(
                countries,
                zValues
            );

        const yearButtons =
            buildYearButtons(
                years,
                zValues
            );


        /* =================================================
           LAYOUT
           ================================================= */

        const layout = {

            paper_bgcolor:
                HEATMAP_CONFIG.white,

            plot_bgcolor:
                HEATMAP_CONFIG.white,

            font: {

                family:
                    "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",

                color:
                    HEATMAP_CONFIG.textColor
            },


            title: {

                text:
                    `<b>Storms Meet the Islands in the Last 20 Years</b>` +
                    `<br><sup>` +
                    `Cyclone activity, ${firstYear}–${latestYear}` +
                    `</sup>`,

                x:
                    0,

                xanchor:
                    "left",

                y:
                    0.98,

                yanchor:
                    "top",

                font: {
                    size: 20,
                    color:
                        HEATMAP_CONFIG.textColor
                }

            },


            xaxis: {

                title: {
                    text:
                        "Year",

                    font: {
                        color:
                            HEATMAP_CONFIG.textColor,

                        size: 12
                    },

                    standoff:
                        15
                },

                type:
                    "category",

                showgrid:
                    false,

                zeroline:
                    false,

                side:
                    "bottom"

            },


            yaxis: {

                automargin:
                    true,

                showgrid:
                    false,

                zeroline:
                    false

            },


            updatemenus: [

                {

                    buttons:
                        countryButtons,

                    direction:
                        "down",

                    showactive:
                        true,

                    x:
                        0,

                    xanchor:
                        "left",

                    y:
                        1.18,

                    yanchor:
                        "top",

                    bgcolor:
                        HEATMAP_CONFIG.white,

                    bordercolor:
                        "#EAE6DF",

                    pad: {
                        r: 10,
                        t: 5,
                        b: 5,
                        l: 5
                    }

                },

                {

                    buttons:
                        yearButtons,

                    direction:
                        "down",

                    showactive:
                        true,

                    x:
                        0.25,

                    xanchor:
                        "left",

                    y:
                        1.18,

                    yanchor:
                        "top",

                    bgcolor:
                        HEATMAP_CONFIG.white,

                    bordercolor:
                        "#EAE6DF",

                    pad: {
                        r: 10,
                        t: 5,
                        b: 5,
                        l: 5
                    }

                }

            ],


            annotations: [

                {

                    xref:
                        "paper",

                    yref:
                        "paper",

                    x:
                        0,

                    y:
                        1.25,

                    text:
                        "<b>Country Filter:</b>",

                    showarrow:
                        false,

                    font: {
                        size: 11,
                        color:
                            HEATMAP_CONFIG.textColor
                    }

                },

                {

                    xref:
                        "paper",

                    yref:
                        "paper",

                    x:
                        0.25,

                    y:
                        1.25,

                    text:
                        "<b>Year Filter:</b>",

                    showarrow:
                        false,

                    font: {
                        size: 11,
                        color:
                            HEATMAP_CONFIG.textColor
                    }

                },

                {

                    xref:
                        "paper",

                    yref:
                        "paper",

                    x:
                        0.5,

                    y:
                        -0.22,

                    text:
                        "Hover over cells to view cyclone totals. Use drop-down controls above to highlight single slices.",

                    showarrow:
                        false,

                    align:
                        "center",

                    font: {
                        size: 11,
                        color:
                            HEATMAP_CONFIG.mutedText
                    }

                }

            ],


            margin: {

                t:
                    180,

                l:
                    120,

                r:
                    40,

                b:
                    100

            },

            height:
                720,

            showlegend:
                false

        };


        /* =================================================
           PLOTLY CONFIG
           ================================================= */

        const plotlyConfig = {

            responsive:
                true,

            displayModeBar:
                false,

            displaylogo:
                false,

            scrollZoom:
                false

        };


        /* =================================================
           RENDER
           ================================================= */

        const chartContainer =
            document.getElementById(
                HEATMAP_CONFIG.chartId
            );


        if (!chartContainer) {

            throw new Error(
                `Heatmap container #${HEATMAP_CONFIG.chartId} not found`
            );

        }


        /*
         * Remove any previous Plotly instance
         * safely before rendering.
         */

        if (
            chartContainer.data
        ) {

            await Plotly.purge(
                chartContainer
            );

        }


        await Plotly.newPlot(

            chartContainer,

            [trace],

            layout,

            plotlyConfig

        );


        /* =================================================
           EVENTS
           ================================================= */


        /*
         * Cell click.
         */

        chartContainer.on(
            "plotly_click",
            handleHeatmapClick
        );


        /*
         * Dropdown slicing.
         */

        chartContainer.on(
            "plotly_restyle",
            handleHeatmapRestyle
        );


        /*
         * Resize.
         */

        if (
            !window.__heatmapResizeHandler
        ) {

            window.__heatmapResizeHandler =
                () => {

                    const chart =
                        document.getElementById(
                            HEATMAP_CONFIG.chartId
                        );

                    if (chart) {

                        Plotly.Plots.resize(
                            chart
                        );

                    }

                };

            window.addEventListener(
                "resize",
                window.__heatmapResizeHandler
            );

        }


        console.log(
            "Heatmap created successfully:",
            {
                countries:
                    countries.length,

                years:
                    years.length,

                firstYear,
                latestYear
            }
        );


    } catch (error) {

        console.error(
            "Heatmap visualization error:",
            error
        );

    }

}


/* =========================================================
   INITIALIZE
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        createHeatmap();

    }
);
