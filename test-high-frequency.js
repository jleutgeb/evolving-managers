js_vars.confidence = 1;
js_vars.partner_confidence = 1.1;
js_vars.joint_payoff_info = true;
js_vars.relative_payoff_info = true;

var p1_fakeaction = 0.3;
var p2_fakeaction = 0.4;

var p1_fakepayoff = payoff(js_vars.confidence, p1_fakeaction, p2_fakeaction, gamma = js_vars.gamma)
var p2_fakepayoff = payoff(js_vars.partner_confidence, p2_fakeaction, p1_fakeaction, gamma = js_vars.gamma)

var fakedata = {
  next_period_length: 4000,
  p1_action: p1_fakeaction,
  p2_action: p2_fakeaction,
  p1_period_payoff: p1_fakepayoff,
  p2_period_payoff: p2_fakepayoff, 
  p1_round_payoff: p1_fakepayoff,
  p2_round_payoff: p2_fakepayoff,
  period: 1,
  type: 'start-period'
};

liveRecv(fakedata);