/* =========================================================
   explain.js
   Climate Chart Explanation Controls

   Handles:
   - Audience selection
   - Explain button
   - ChartContext creation
   - Backend API request
   - Explanation response display

   Charts:
   - trend-chart
   - heatmap
   - bubble-chart
   ========================================================= */


/* =========================================================
   CONFIGURATION
   ========================================================= */

const EXPLAIN_CONFIG = {

    apiUrl:
        "http://localhost:8000/api/explain",

    charts: {

        "trend-chart": {
            outputId: "trend-explanation"
        },

        "heatmap": {
            outputId: "heatmap-explanation"
        },

        "bubble-chart": {
            outputId: "bubble-explanation"
        }

    }

};


/* =========================================================
   CURRENT SELECTION STATE
   ========================================================= */

window.selectedTrendRegion =
    window.selectedTrendRegion ?? null;

window.selectedTrendStartYear =
    window.selectedTrendStartYear ?? null;

window.selectedTrendEndYear =
    window.selectedTrendEndYear ?? null;


window.selectedHeatmapRegion =
    window.selectedHeatmapRegion ?? null;

window.selectedHeatmapYear =
    window.selectedHeatmapYear ?? null;


window.selectedBubbleRegion =
    window.selectedBubbleRegion ?? null;

window.selectedBubblePeriod =
    window.selectedBubblePeriod ?? "2010s";


/* =========================================================
   AUDIENCE OPTIONS
   ========================================================= */

const AUDIENCE_OPTIONS = [

    {
        value: "general",
        label: "General"
    },

    {
        value: "eli5",
        label: "ELI5"
    },

    {
        value: "scientist",
        label: "Scientist"
    }

];


/* =========================================================
   CREATE CONTROLS FOR ALL CHARTS
   ========================================================= */

function initializeExplainControls() {

    Object.entries(
        EXPLAIN_CONFIG.charts
    ).forEach(
        ([chartId, config]) => {

            createControls(
                chartId,
                config.outputId
            );

        }
    );

}


/* =========================================================
   CREATE CONTROLS
   ========================================================= */

function createControls(
    chartId,
    outputId
) {

    const chart =
        document.getElementById(chartId);

    if (!chart) {

        console.warn(
            `Chart not found: ${chartId}`
        );

        return;
    }


    /*
     * Prevent duplicate controls.
     */

    const existing =
        document.querySelector(
            `.explain-controls[data-chart-id="${chartId}"]`
        );

    if (existing) {
        return;
    }


    /*
     * Controls container.
     */

    const controls =
        document.createElement("div");

    controls.className =
        "explain-controls";

    controls.dataset.chartId =
        chartId;


    /*
     * Label.
     */

    const label =
        document.createElement("label");

    label.textContent =
        "Explain for: ";


    /*
     * Audience selector.
     */

    const select =
        document.createElement("select");

    select.className =
        "explain-audience";

    select.setAttribute(
        "aria-label",
        "Choose explanation audience"
    );


    AUDIENCE_OPTIONS.forEach(
        optionData => {

            const option =
                document.createElement("option");

            option.value =
                optionData.value;

            option.textContent =
                optionData.label;

            select.appendChild(option);

        }
    );


    /*
     * Explain button.
     */

    const button =
        document.createElement("button");

    button.type =
        "button";

    button.className =
        "explain-button";

    button.textContent =
        "Explain";


    /*
     * Assemble controls.
     */

    label.appendChild(select);

    controls.appendChild(label);

    controls.appendChild(button);


    /*
     * Insert controls directly below chart.
     */

    const caption =
        chart.parentNode.querySelector(
            ".viz-caption-container"
        );

    if (caption) {

        caption.parentNode.insertBefore(
            controls,
            caption.nextSibling
        );

    } else {

        chart.parentNode.insertBefore(
            controls,
            chart.nextSibling
        );

    }


    /*
     * Output area.
     */

    const output =
        document.createElement("div");

    output.id =
        outputId;

    output.className =
        "explanation-output";

    output.setAttribute(
        "aria-live",
        "polite"
    );


    controls.parentNode.insertBefore(
        output,
        controls.nextSibling
    );


    /*
     * Button event.
     */

    button.addEventListener(
        "click",
        async () => {

            const audience =
                select.value;


            let chartContext;

            try {

                chartContext =
                    createChartContext(
                        chartId,
                        audience
                    );

            } catch (error) {

                console.error(
                    "Could not create chart context:",
                    error
                );

                output.innerHTML =
                    `
                    <div class="explanation-error">
                        <strong>Unable to explain this chart.</strong>
                        <p>
                            Please select a country or chart value first.
                        </p>
                    </div>
                    `;

                return;

            }


            console.log(
                "ChartContext created:",
                chartContext
            );


            await explainChart(
                chartContext,
                button,
                output
            );

        }
    );

}


/* =========================================================
   GET ACTIVE PLOTLY DROPDOWN LABEL
   ========================================================= */

function getActivePlotlyDropdownLabels(
    targetChartId
) {

    const targetChart =
        document.getElementById(
            targetChartId
        );

    const menus =
        targetChart?._fullLayout?.updatemenus;

    if (
        !Array.isArray(menus) ||
        !menus.length
    ) {
        return [];
    }


    const labels = [];


    for (
        const menu of menus
    ) {

        if (
            !menu ||
            !Array.isArray(menu.buttons) ||
            typeof menu.active !== "number"
        ) {
            continue;
        }


        const activeButton =
            menu.buttons[menu.active];


        if (
            activeButton &&
            activeButton.label
        ) {

            labels.push(
                activeButton.label
            );

        }

    }


    return labels;

}


/* =========================================================
   CREATE CHART CONTEXT
   ========================================================= */

function createChartContext(
    chartId,
    audience
) {


    /* =====================================================
       TREND CHART
       ===================================================== */

    if (chartId === "trend-chart") {

        const dropdownLabels =
            getActivePlotlyDropdownLabels(
                chartId
            );


        const selectedRegion =
            window.selectedTrendRegion ||
            dropdownLabels[0] ||
            "Pacific Overall";


        const startYear =
            window.selectedTrendStartYear ??
            null;


        const endYear =
            window.selectedTrendEndYear ??
            null;


        window.selectedTrendRegion =
            selectedRegion;


        console.log(
            "Trend selection:",
            {
                region: selectedRegion,
                start_year: startYear,
                end_year: endYear
            }
        );


        return {

            chart_id:
                "trend-chart",

            audience:
                audience,

            selection: {

                region:
                    selectedRegion,

                start_year:
                    startYear,

                end_year:
                    endYear

            }

        };

    }


    /* =====================================================
       BUBBLE CHART
       ===================================================== */

    if (chartId === "bubble-chart") {

        const selectedRegion =
            window.selectedBubbleRegion ??
            null;


        const selectedPeriod =
            window.selectedBubblePeriod ||
            "2010s";


        console.log(
            "Bubble selection:",
            {
                region: selectedRegion,
                period: selectedPeriod
            }
        );


        return {

            chart_id:
                "bubble-chart",

            audience:
                audience,

            selection: {

                period:
                    selectedPeriod,

                region:
                    selectedRegion

            }

        };

    }


    /* =====================================================
       HEATMAP
       ===================================================== */

    if (chartId === "heatmap") {

        const selectedRegion =
            window.selectedHeatmapRegion ??
            null;


        const selectedYear =
            window.selectedHeatmapYear != null
                ? Number(window.selectedHeatmapYear)
                : null;


        console.log(
            "Heatmap selection:",
            {
                region: selectedRegion,
                year: selectedYear
            }
        );


        /*
         * A heatmap explanation requires
         * a selected country.
         *
         * Do not silently send null.
         */

        if (!selectedRegion) {

            throw new Error(
                "No heatmap country selected"
            );

        }


        return {

            chart_id:
                "heatmap",

            audience:
                audience,

            selection: {

                region:
                    selectedRegion,

                start_year:
                    selectedYear,

                end_year:
                    selectedYear

            }

        };

    }


    throw new Error(
        `Unsupported chart: ${chartId}`
    );

}


/* =========================================================
   LISTEN FOR TREND SELECTION
   ========================================================= */

document.addEventListener(
    "trendRegionSelected",
    (event) => {

        const region =
            event?.detail?.region ??
            event?.detail?.country;


        if (!region) {
            return;
        }


        window.selectedTrendRegion =
            region;


        if (
            event?.detail?.start_year != null
        ) {

            window.selectedTrendStartYear =
                Number(
                    event.detail.start_year
                );

        }


        if (
            event?.detail?.end_year != null
        ) {

            window.selectedTrendEndYear =
                Number(
                    event.detail.end_year
                );

        }


        console.log(
            "Selected trend region:",
            window.selectedTrendRegion
        );

    }
);


/* =========================================================
   LISTEN FOR HEATMAP SELECTION
   ========================================================= */

document.addEventListener(
    "countrySelected",
    (event) => {

        const country =
            event?.detail?.country;


        const year =
            event?.detail?.year;


        if (!country) {
            return;
        }


        window.selectedHeatmapRegion =
            country;


        window.selectedHeatmapYear =
            year != null
                ? Number(year)
                : null;


        console.log(
            "Selected heatmap region:",
            window.selectedHeatmapRegion
        );


        console.log(
            "Selected heatmap year:",
            window.selectedHeatmapYear
        );

    }
);


/* =========================================================
   LISTEN FOR BUBBLE SELECTION
   ========================================================= */

document.addEventListener(
    "bubbleRegionSelected",
    (event) => {

        const region =
            event?.detail?.region ??
            event?.detail?.country;


        if (!region) {
            return;
        }


        window.selectedBubbleRegion =
            region;


        if (
            event?.detail?.period
        ) {

            window.selectedBubblePeriod =
                event.detail.period;

        }


        console.log(
            "Selected bubble region:",
            window.selectedBubbleRegion
        );

    }
);


/* =========================================================
   CALL BACKEND
   ========================================================= */

async function explainChart(
    chartContext,
    button,
    output
) {

    /*
     * Loading state.
     */

    button.disabled =
        true;


    const originalText =
        button.textContent;


    button.textContent =
        "Explaining...";


    output.innerHTML =
        `
        <div class="explanation-loading">
            Analyzing the chart...
        </div>
        `;


    try {

        console.log(
            "Country/region sent to backend:",
            chartContext?.selection?.region ??
                null
        );


        console.log(
            "Complete request payload:",
            chartContext
        );


        /*
         * Send ChartContext to FastAPI.
         */

        const response =
            await fetch(
                EXPLAIN_CONFIG.apiUrl,
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            chartContext
                        )

                }
            );


        /*
         * Handle HTTP errors.
         */

        if (!response.ok) {

            let message =
                `Request failed (${response.status})`;


            try {

                const error =
                    await response.json();


                if (error.detail) {

                    message =
                        error.detail;

                }

            } catch {
                /*
                 * Keep default message.
                 */
            }


            throw new Error(
                message
            );

        }


        /*
         * Read backend response.
         */

        const result =
            await response.json();


        console.log(
            "Explanation response:",
            result
        );


        /*
         * Display explanation.
         */

        displayExplanation(
            output,
            result
        );


    } catch (error) {

        console.error(
            "Chart explanation error:",
            error
        );


        output.innerHTML =
            `
            <div class="explanation-error">

                <strong>
                    Unable to generate explanation.
                </strong>

                <p>
                    ${escapeHtml(
                        error?.message ||
                        "Please try again."
                    )}
                </p>

            </div>
            `;

    } finally {

        button.disabled =
            false;


        button.textContent =
            originalText;

    }

}


/* =========================================================
   DISPLAY RESPONSE
   ========================================================= */

function displayExplanation(
    output,
    result
) {

    const explanation =
        result?.explanation ||
        "";


    const takeaway =
        result?.takeaway ||
        "";


    if (
        !explanation &&
        !takeaway
    ) {

        output.innerHTML =
            `
            <div class="explanation-error">
                No explanation was returned.
            </div>
            `;

        return;

    }


    output.innerHTML =
        `
        <div class="explanation-content">

            ${
                explanation
                    ? `
                    <div class="explanation-main">
                        <p>
                            ${escapeHtml(
                                explanation
                            )}
                        </p>
                    </div>
                    `
                    : ""
            }


            ${
                takeaway
                    ? `
                    <div class="explanation-takeaway">

                        <strong>
                            Key takeaway
                        </strong>

                        <p>
                            ${escapeHtml(
                                takeaway
                            )}
                        </p>

                    </div>
                    `
                    : ""
            }

        </div>
        `;

}


/* =========================================================
   ESCAPE HTML
   ========================================================= */

function escapeHtml(
    value
) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );

}


/* =========================================================
   INITIALIZE
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeExplainControls();

    }
);
