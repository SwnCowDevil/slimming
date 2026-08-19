const { request } = require("./client");
function listRecipes(){return request({url:"/api/v1/recipes"});}
function recordRecipe(id,payload,key){return request({url:`/api/v1/recipes/${id}/record`,method:"POST",data:payload,headers:{"Idempotency-Key":key}});}
module.exports={listRecipes,recordRecipe};
