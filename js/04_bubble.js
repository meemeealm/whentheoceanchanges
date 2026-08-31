/* =========================================================
   04_bubble.js
   ========================================================= */

const DATA_PATH = "backend/data/bubble_data.json";
const CHART_ID = "bubble-chart";

async function loadBubbleData() {
    const response = await fetch(DATA_PATH);
    if (!response.ok) throw new Error(`Could not load ${DATA_PATH}`);
    return await response.json();
}

async function createBubbleChart() {
    try {
        const data = await loadBubbleData();
        if (!data || !data.length) {
            console.warn("No bubble chart data found.");
            return;
        }

        // Apply DOM width BEFORE rendering Plotly canvas
        const chart = document.getElementById(CHART_ID);
        if (chart) {
            chart.style.width = "85%";
            chart.style.marginLeft = "auto";
            chart.style.marginRight = "auto";
        }

        // Safe Reductions
        const maxLoss = data.reduce((max, row) =>
            Number(row.economic_loss) > Number(max.economic_loss) ? row : max
        , data[0]);

        const maxPeople = data.reduce((max, row) =>
            Number(row.people_affected) > Number(max.people_affected) ? row : max
        , data[0]);

        // Country Colors
        const colors = [
            "#357596", "#5BA8C5", "#78BCD4", "#478EAF",
            "#6FAFC4", "#9BCEDF", "#2F6F8F", "#A7D3E3", "#529DBB"
        ];
        const countries = [...new Set(data.map(row => row.country))].sort();
        const countryColor = {};
        countries.forEach((country, index) => {
            countryColor[country] = colors[index % colors.length];
        });

        // Bubble Sizing Calculation
        const maxEconomicLoss = Math.max(...data.map(row => Number(row.economic_loss))) || 1;
        const maxDesiredDiameter = 45;
        const sizeRef = (2 * maxEconomicLoss) / Math.pow(maxDesiredDiameter, 2);

        const trace = {
            type: "scatter",
            mode: "markers",
            x: data.map(row => Number(row.cyclone_count)),
            y: data.map(row => Number(row.people_affected)),
            marker: {
                size: data.map(row => Number(row.economic_loss)),
                sizemode: "area",
                sizeref: sizeRef,
                sizemin: 4,
                opacity: 0.78,
                color: data.map(row => countryColor[row.country]),
                line: { color: "#FFFFFF", width: 1.5 }
            },
            customdata: data.map(row => [
                row.country,
                Number(row.cyclone_count),
                Number(row.people_affected),
                Number(row.economic_loss)
            ]),
            hovertemplate:
                "<b>%{customdata[0]}</b><br>" +
                "Cyclones: %{customdata[1]:,.0f}<br>" +
                "People affected: %{customdata[2]:,.0f}<br>" +
                "Economic loss: $%{customdata[3]:,.0f}<extra></extra>",
            showlegend: false
        };

        const layout = {
            autosize: true,
            template: "plotly_white",
            height: 500,
            paper_bgcolor: "#FFFFFF",
            plot_bgcolor: "#FFFFFF",
            title: {
                text: "<b>When Hazards Become Impacts</b><br><sup>During the 2010s</sup>",
                x: 0.02,
                xanchor: "left",
                font: { size: 22, color: "#000000" }
            },
            xaxis: {
                title: { text: "Number of Cyclones", font: { color: "#000000" } },
                showgrid: false,
                zeroline: false,
                tickfont: { color: "#000000" }
            },
            yaxis: {
                title: { text: "People affected", standoff: 15, font: { color: "#000000" } },
                showgrid: true,
                gridcolor: "#EAE6DF",
                zeroline: false,
                tickfont: { color: "#000000" }
            },
            annotations: [
                {
                    x: Number(maxPeople.cyclone_count),
                    y: Number(maxPeople.people_affected),
                    text: `${maxPeople.country} — highest people affected`,
                    showarrow: true,
                    arrowhead: 2,
                    ax: 40,
                    ay: -50,
                    arrowcolor: "#000000",
                    font: { size: 11, color: "#000000" }
                },
                {
                    x: Number(maxLoss.cyclone_count),
                    y: Number(maxLoss.people_affected),
                    text: `${maxLoss.country} — highest economic loss`,
                    showarrow: true,
                    arrowhead: 2,
                    ax: 50,
                    ay: 50,
                    arrowcolor: "#000000",
                    font: { size: 11, color: "#000000" }
                },
                {
                    xref: "paper",
                    yref: "paper",
                    x: 0,
                    y: 1.08,
                    text: "Larger bubbles indicate greater economic loss",
                    showarrow: false,
                    font: { size: 9, color: "#7A858A" },
                    align: "left"
                }
            ],
            margin: { l: 100, r: 40, t: 125, b: 70 },
            font: {
                family: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                color: "#000000"
            }
        };

        const config = {
            responsive: true,
            displayModeBar: false,
            displaylogo: false
        };

        await Plotly.newPlot(CHART_ID, [trace], layout, config);
    } catch (error) {
        console.error("Bubble chart error:", error);
    }
}

createBubbleChart();