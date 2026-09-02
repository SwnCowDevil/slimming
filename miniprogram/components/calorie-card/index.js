Component({
  options:{styleIsolation:"apply-shared"},
  properties:{ budget:{type:Number,value:1650}, consumed:{type:Number,value:0}, nutrients:{type:Array,value:[]} },
  data:{remaining:1650,percent:0,statusText:"状态正常"},
  observers:{"budget,consumed":function(budget,consumed){const remaining=Math.max(0,budget-consumed),percent=Math.min(100,Math.round(consumed/Math.max(1,budget)*100));this.setData({remaining,percent,statusText:consumed>budget?"已超出":"状态正常"});}}
});
