const SUPPORTED_LANGUAGES = ["FRENCH", "SPANISH", "JAPANESE"]
const STATS_ENDPOINT = "https://2e103ef1-ab2c-4a75-a746-283686ee43b7.mock.pstmn.io/stats/"

let chartId = undefined

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
    res = await fetch(STATS_ENDPOINT+language)
    json = await res.json()
    return json
}

const updateStats = (language)=>{
    requestStats(language).then((stats)=>{
        console.log(stats)
        $("#learned-count").text(stats.learnedWords)
        $("#conversations-count").text(stats.conversations)
        $("#rosie-score-number").text(stats.rosieScore)

        let donutChart = document.getElementById("donut-chart").getContext("2d");
        if(chartId){
            chartId.destroy()
        }
        chartId = new Chart(donutChart, {
        type: 'pie',
        data: {
            labels: ["Master", "Proficient", "Beginner"],
            datasets: [{
                label: "Mastery",
                data: [stats.mastery.mastered, stats.mastery.proficient, stats.mastery.beginner],
                backgroundColor: ['yellow', 'aqua', 'pink'],
                hoverOffset: 5
            }],
        },
        options: {
            responsive: false,
        },
        });
    })
}

