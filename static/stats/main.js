const SUPPORTED_LANGUAGES = ["FRENCH", "SPANISH", "JAPANESE"]
const STATS_ENDPOINT = "/api/stats"

let chartId = undefined
let graphs = []
$(document).ready(function() {  
    $.each(SUPPORTED_LANGUAGES, function(index, value) {
      $('#language-selector').append($('<option>', {
        value: value,
        text: value
      }));
    });
    updateStats($("#language-selector").val())
    $('#language-selector').on('change', function(e) {
        updateStats($(this).val())
    });
  });

const requestStats = async (language)=>{
    res = await fetch(STATS_ENDPOINT+"/"+language)
    json = await res.json()
    return json
    
}

const updateStats = (language)=>{
    requestStats(language).then((stats)=>{
        // console.log(stats)
        graphs = stats.graphs
        if(chartId){
            chartId.destroy()
        }
        $('#chart-selector').find('option').remove().end()
        $('#stats').find('div').remove().end()
        stats.numbers.map(number =>{
            $("#stats").append(
                `<div class="stat-box">
                    <h2>`+number.title+`</h2>
                    <p>`+number.data+`</p>
                </div>`
            )
        })
        $.each(stats.graphs, function(index, value) {
            $('#chart-selector').append($('<option>', {
              value: value.title,
              text: value.title
            }));
        });
        $('#chart-selector').on('change', function(e) {
            let type = $(this).val()
            let selectedGraph;
            graphs.map((graph)=>{
                if(graph.title == type){
                    selectedGraph = graph
                }
            })
            console.log(selectedGraph)
            let chart = document.getElementById("chart").getContext("2d");
            if(chartId){
                chartId.destroy()
            }
            chartId = new Chart(chart, {
                type: selectedGraph.type,
                data : selectedGraph.data,
                options: {
                    responsive: false,
                },
            });
        });
        if(stats.graphs.length > 0){
            let selectedGraph = stats.graphs[0]
            let chart = document.getElementById("chart").getContext("2d");
            if(chartId){
                chartId.destroy()
            }
            chartId = new Chart(chart, {
                type: selectedGraph.type,
                data : selectedGraph.data,
                options: {
                    responsive: false,
                },
            });
        }
        
    })
}

