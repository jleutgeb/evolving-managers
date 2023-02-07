/*!
* high frequency interface for evolving managers
 */

function coordinate(x, y) {
    this.x = x;
    this.y = y;
}

function payoff(ai, qi, qj, gamma) {
    price = Math.max(0, ai - qi - gamma * qj);
    return qi * price * 100;
}

var output;

if (js_vars.id === 1) {
    var action = js_vars.p1_action;
    var partner_action = js_vars.p2_action;
    var period_payoff = js_vars.p1_period_payoff;
    var partner_period_payoff = js_vars.p2_period_payoff;
}
else if (js_vars.id === 2) {
    var action = js_vars.p2_action;
    var partner_action = js_vars.p1_action;
    var period_payoff = js_vars.p2_period_payoff;
    var partner_period_payoff = js_vars.p1_period_payoff;
}

var market_payoff = period_payoff + partner_period_payoff;
var payoff_difference = Math.abs(period_payoff - partner_period_payoff);

var millisecondsleft = 0;
const earnings = document.getElementById('earnings');
const earnings_prev_period = document.getElementById('earnings_prev_period');
const period_counter = document.getElementById('period_counter');
const countdown = document.getElementById('countdown');
const gamestate = document.getElementById('gameState');
const ctx = document.getElementById('myChart');
const minaction = 0;
const maxaction = 1;
const stepsize = 0.01; // used to draw the counterfactual payoff
const numchoices = (maxaction - minaction) / stepsize + 1  

const myChart = new Chart(ctx, {
    type: 'scatter',
    data: {
        datasets: [
            {
                data: payoffCurve(js_vars.confidence, numchoices, partner_action, js_vars.gamma), // own payoff curve
                borderColor: [
                    'rgba(0, 0, 0, 1)'
                ],
                borderWidth: 1,
                pointRadius: 0,
                showLine: true,
            },
            {
                data: coordinateArray(action, 0), // own action
                backgroundColor: 'rgb(255, 0, 0)',
                pointRadius: 5,
                pointStyle: 'rect',
            },
            {
                data: coordinateArray(partner_action, 0), // partner's action
                backgroundColor: 'rgb(0, 0, 255)',
                pointRadius: 5,
                pointStyle: 'rect',
            },
            {
                data: coordinateArray(action, period_payoff), // own payoff
                backgroundColor: 'rgb(255, 0, 0)',
                pointRadius: 5,
            },
            {
                data: coordinateArray(partner_action, partner_period_payoff), // partner's payoff
                backgroundColor: 'rgb(0, 0, 255)',
                pointRadius: 5,
                hidden: !js_vars.joint_payoff_info,
            },
            {
                data: coordinateArray(action, period_payoff+partner_period_payoff), // joint payoff
                backgroundColor: 'rgb(0, 0, 255)',
                pointRadius: 5,
                hidden: true,
            },
            {
                data: jointPayoffCurve(js_vars.confidence, js_vars.partner_confidence, numchoices, partner_action, js_vars.gamma), // joint payoff bubble
                borderColor: [
                    'rgba(0, 0, 0, 1)'
                ],
                borderWidth: 1,
                pointRadius: 0,
                showLine: true,
                borderDash: [5, 5],
                hidden: !js_vars.joint_payoff_info,
            },
            {
                data: coordinateArray(action, period_payoff - partner_period_payoff), // payoff difference
                backgroundColor: 'rgb(0, 0, 0)',
                pointRadius: 5,
                hidden: true,
            },
            {
                data: relativePayoffCurve(js_vars.confidence, js_vars.partner_confidence, numchoices, partner_action, js_vars.gamma), // payoff difference bubble
                borderColor: [
                    'rgba(0, 0, 0, 1)'
                ],
                borderWidth: 1,
                pointRadius: 0,
                showLine: true,
                borderDash: [1, 3],
                hidden: !js_vars.relative_payoff_info,
            },
        ]
    },
    options: {
        animation: {
            duration: '200',
        },
        maintainAspectRatio: false,
        onClick: (e) => {
            const canvasPosition = Chart.helpers.getRelativePosition(e, myChart);
            var dataX = Math.round(myChart.scales.x.getValueForPixel(canvasPosition.x)*js_vars.number_of_choices)/js_vars.number_of_choices;
            dataX  = Math.max(dataX, 0);
            dataX  = Math.min(dataX, 1);
            output = dataX;
            myChart.options.plugins.annotation.annotations.line1.xMin = dataX;
            myChart.options.plugins.annotation.annotations.line1.xMax = dataX;
            myChart.update();
        },
        plugins: {
            legend: {
            display: false,
            },
            tooltip: {
                enabled: false,
            },
            autocolors: false,
            annotation: {
                annotations: {
                    line1: {
                        type: 'line',
                        id: 'choiceline',
                        xMin: action,
                        xMax: action,
                        borderColor: 'rgba(255, 0, 0, 0.5)',
                        borderWidth: 2,
                    }
                }
            }
        },            
        scales: {
            x: {
                display: false,
                min: "-0.02",
                max: "1.02"
            },
            y: {
                beginAtZero: true,
                suggestedMin: -0.1 * 100,
                suggestedMax: 0.5 * 100,
            }
        }
    }
});

// after the entire page has loaded, send message "ready"
document.addEventListener("DOMContentLoaded", () => {
    output = action;
    liveSend({
        'type': 'ready'
    });
});

// send data to server: period, action and expected time
function send_update(action, expected) {
    liveSend({
        'type': 'update', 
        'expected': expected, 
        'action': action
    });
}

function update_countdown(expected, interval, msecondsleft, currentperiod) {
    var dt = Date.now() - expected;
    var next_expected = Date.now() + 1000 - dt;
    msecondsleft += -interval;
    millisecondsleft = msecondsleft;
    if (msecondsleft > 0) {
        countdown.innerHTML = 'Nächste Periode in ' + Math.round(msecondsleft/1000) + ' Sekunden';
        setTimeout(function() {update_countdown(next_expected, 1000, msecondsleft)}, Math.max(0,1000-dt));
    } else {
        setTimeout(function() {if (millisecondsleft <= 0) {
            gamestate.innerHTML = "Warte auf den Server";
            countdown.innerHTML = '';
        }}, 1000);
    }
}

// function to draw payoff curve
function payoffCurve(confidence, numchoices, otheraction, gamma) {
    var payoff_curve = new Array();
    for (let i = 0; i < numchoices; i++) {
        payoff_curve.push(new coordinate(i/(numchoices-1), payoff(confidence, i/(numchoices-1), otheraction, gamma)));
    };
    return payoff_curve;
}

// function to create array with single coordinate
function coordinateArray(x, y) {
    var output = new Array();
    output.push(new coordinate(x, y));
    return output;
}

function jointPayoffCurve(confidence, otherconfidence, numchoices, otheraction, gamma) {
    var payoff_curve = new Array();
    for (let i = 0; i < numchoices; i++) {
        var jointpay = payoff(confidence, i/(numchoices-1), otheraction, gamma) + payoff(otherconfidence, otheraction, i/(numchoices-1), gamma);
        payoff_curve.push(new coordinate(i/(numchoices-1), jointpay));
    };
    return payoff_curve;
}

function relativePayoffCurve(confidence, otherconfidence, numchoices, otheraction, gamma) {
    var payoff_curve = new Array();
    for (let i = 0; i < numchoices; i++) {
        var difference = -Math.abs(payoff(confidence, i/(numchoices-1), otheraction, gamma) - payoff(otherconfidence, otheraction, i/(numchoices-1), gamma));
        //var difference = payoff(otherconfidence, otheraction, i/(numchoices-1), gamma);
        //var difference = payoff(confidence, i/(numchoices-1), otheraction, gamma) - payoff(otherconfidence, otheraction, i/(numchoices-1), gamma);
        payoff_curve.push(new coordinate(i/(numchoices-1), difference));
    };
    return payoff_curve;
}

// function what to do when the server sends a message
function liveRecv(data) {
    console.log('received', data) // record it for debugging
    gamestate.innerHTML = '';
    millisecondsleft = data.next_period_length;
    // update variables on page
    if (js_vars.id == 1) {
        action = data.p1_action;
        partner_action = data.p2_action;
        period_payoff = data.p1_period_payoff;
        partner_period_payoff = data.p2_period_payoff;
        round_payoff = data.p1_round_payoff;
    }
    if (js_vars.id == 2) {
        action = data.p2_action;
        partner_action = data.p1_action;
        period_payoff = data.p2_period_payoff;
        partner_period_payoff = data.p1_period_payoff;
        round_payoff = data.p2_round_payoff;
    }

    // update chart
    // own payoff curve
    myChart.data.datasets[0].data = payoffCurve(js_vars.confidence, numchoices, partner_action, js_vars.gamma);
    // own action
    myChart.data.datasets[1].data = coordinateArray(action, 0);
    // partner's action
    myChart.data.datasets[2].data = coordinateArray(partner_action, 0);
    // own payoff
    myChart.data.datasets[3].data = coordinateArray(action, period_payoff);
    // partner's payoff
    myChart.data.datasets[4].data = coordinateArray(partner_action, partner_period_payoff);
    // joint payoff
    myChart.data.datasets[5].data = coordinateArray(action, period_payoff+partner_period_payoff);
    // joint payoff bubble
    myChart.data.datasets[6].data = jointPayoffCurve(js_vars.confidence, js_vars.partner_confidence, numchoices, partner_action, js_vars.gamma);
    // payoff difference
    myChart.data.datasets[7].data = coordinateArray(action, period_payoff - partner_period_payoff);
    // payoff difference bubble
    myChart.data.datasets[8].data = relativePayoffCurve(js_vars.confidence, js_vars.partner_confidence, numchoices, partner_action, js_vars.gamma);

    myChart.update();

    if (data.period == 0) {
        earnings_prev_period.innerHTML = 0;
        earnings.innerHTML = 0;
    } else {
        earnings_prev_period.innerHTML = (Math.round(period_payoff*10)/10).toString().replace(".", ",");
        earnings.innerHTML = (Math.round(round_payoff*10)/10).toString().replace(".", ",");
    }

    var countdown_start = Date.now();
    var interval = data.next_period_length - Math.floor(data.next_period_length/1000)*1000;
    var next_countdown_expected = countdown_start + interval;

    // if the server sends a message to start another period, reply with state of the game after the specified amount of time
    if (data.type === 'start-period') {
        period_counter.innerHTML = 'Periode: ' + (data.period + 1);
        countdown.innerHTML = 'Nächste Periode in ' + Math.round(data.next_period_length/1000) + ' Sekunden';

        setTimeout(function() {update_countdown(next_countdown_expected, interval, data.next_period_length)}, interval);
        setTimeout(function() {send_update(action = parseFloat(output), data.expected)}, data.next_period_length);
    }
    else if (data.type === 'end-supergame') {
        gamestate.innerHTML = 'Ende des Spiels';
        countdown.innerHTML = '';
        setTimeout(function() {document.getElementById("form").submit()}, 2000);
    }
}
