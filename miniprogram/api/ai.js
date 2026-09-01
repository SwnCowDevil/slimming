const { request } = require("./client");
function createDraft(data){return request({url:"/api/v1/ai/drafts",method:"POST",data});}function confirmDraft(id,key){return request({url:`/api/v1/ai/drafts/${id}/confirm`,method:"POST",headers:{"Idempotency-Key":key}});}
function createWeeklyReflection(period,endDate){return request({url:"/api/v1/ai/weekly-reflections",method:"POST",data:{period,end_date:endDate,context:{pregnancy:true}}});}
function createRecipeSwap(currentRecipeId){return request({url:"/api/v1/ai/recipe-swaps",method:"POST",data:{current_recipe_id:currentRecipeId,context:{pregnancy:true}}});}
module.exports={createDraft,confirmDraft,createWeeklyReflection,createRecipeSwap};
