/* =========================================================
   explain.js
   Climate Chart Explanation Controls

   Handles:
   - Audience selection
   - Explain button
   - ChartContext creation
   - Backend API request
   - Gemini response display

   Charts:
   - trend-chart
   - cyclone-chart
   - bubble-chart
   ========================================================= */


/* =========================================================
   CONFIGURATION
   ========================================================= */

const EXPLAIN_CONFIG = {

    /*
     * Local FastAPI backend.
     * Change this URL when deploying to Cloud Run.
     */
    apiUrl:
        "http://localhost:8000/api/explain",

    charts: {

        "trend-chart": {
            outputId: "trend-explanation"
        },

        "cyclone-chart": {
            outputId: "cyclone-explanation"
        },

        "bubble-chart": {
            outputId: "bubble-explanation"
        }
    }

};


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

    chart.parentNode.insertBefore(
        controls,
        chart.nextSibling
    );


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


            const chartContext =
                createChartContext(
                    chartId,
                    audience
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
   CREATE CHART CONTEXT
   ========================================================= */

function createChartContext(
    chartId,
    audience
) {

    /*
     * TREND CHART
     */

    if (chartId === "trend-chart") {

        return {

            chart_id:
                "trend-chart",

            audience:
                audience,

            selection: {

                /*
                 * Your trend chart currently uses
                 * "Pacific Overall" as the default.
                 *
                 * The country dropdown can later
                 * update this value.
                 */

                region:
                    window.selectedTrendRegion ||
                    "Pacific Overall",

                start_year:
                    window.selectedTrendStartYear ??
                    null,

                end_year:
                    window.selectedTrendEndYear ??
                    null
            }

        };

    }


    /*
     * BUBBLE CHART
     */

    if (chartId === "bubble-chart") {

        return {

            chart_id:
                "bubble-chart",

            audience:
                audience,

            selection: {

                /*
                 * Your current bubble chart
                 * represents the 2010s.
                 */

                period:
                    window.selectedBubblePeriod ||
                    "2010s",

                region:
                    window.selectedBubbleRegion ??
                    null
            }

        };

    }


    /*
     * CYCLONE CHART
     */

    if (chartId === "cyclone-chart") {

        return {

            chart_id:
                "cyclone-chart",

            audience:
                audience,

            selection: {

                region:
                    window.selectedCycloneRegion ??
                    null,

                start_year:
                    window.selectedCycloneStartYear ??
                    null,

                end_year:
                    window.selectedCycloneEndYear ??
                    null
            }

        };

    }


    throw new Error(
        `Unsupported chart: ${chartId}`
    );

}


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


        /*
         * Display Gemini explanation.
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
                <strong>Unable to generate explanation.</strong>
                <p>
                    Please try again.
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
        result?.explanation || "";

    const takeaway =
        result?.takeaway || "";


    if (!explanation && !takeaway) {

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
                            ${escapeHtml(explanation)}
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
                            ${escapeHtml(takeaway)}
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